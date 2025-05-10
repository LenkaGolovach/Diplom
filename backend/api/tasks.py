from celery import shared_task
import ollama
from .models import Message, MessageAttachment, NeuroSession
from django.contrib.auth import get_user_model
from .serializers import MessageSerializer
import socketio, io, tempfile, subprocess
import re
import fitz  # PyMuPDF for PDF → text
from docx import Document as DocxDocument
from pdf2image import convert_from_bytes
from transformers import pipeline, Pipeline
import logging

User = get_user_model()
# Убираем или комментируем глобальный клиент sio
# sio = socketio.Client(reconnection=True, reconnection_attempts=5, reconnection_delay=1)

logger = logging.getLogger(__name__)

# --- Инициализация Socket.IO для отправки из Celery ---
# Используем тот же KombuManager, что и в run_socketio.py
# Убедитесь, что URL очереди (amqp://...) совпадает
# и что RabbitMQ доступен для Celery worker'а.
try:
    celery_sio_manager = socketio.KombuManager('amqp://guest:guest@localhost:5672//', write_only=True)
    # Создаем "фиктивный" сервер, чтобы использовать его метод emit с менеджером
    # Этот сервер не будет слушать входящие соединения, только отправлять через KombuManager
    celery_sio_server = socketio.Server(
        client_manager=celery_sio_manager,
        async_mode='eventlet' # или 'threading', если eventlet не используется/не нужен в Celery
                              # Важно, чтобы async_mode был совместим с окружением Celery
                              # Если Celery работает с eventlet (-P eventlet), то 'eventlet' здесь ок.
    )
    logger.info("Celery Socket.IO bridge initialized successfully with KombuManager.")
except Exception as e:
    logger.error(f"Failed to initialize Celery Socket.IO bridge with KombuManager: {e}", exc_info=True)
    celery_sio_server = None # Обработка ошибки, если не удалось инициализировать

# Глобальная инициализация переводчиков
translator_ru_en: Pipeline | None = None
translator_en_ru: Pipeline | None = None

# Простая функция определения, на английском ли текст (нет кириллицы)
def is_english(text: str) -> bool:
    return not bool(re.search(r'[\u0400-\u04FF]', text))

@shared_task
def generate_ai_response(user_message_id):
    try:
        # Fetch the user message
        user_msg = Message.objects.get(id=user_message_id)
        user_text = user_msg.text or ""

        system_instruction = (
            "You are an intelligent AI assistant.\n"
            "When you answer, format the entire response in Markdown with line breaks preserved."
        )

        global translator_ru_en, translator_en_ru
        if translator_ru_en is None:
            translator_ru_en = pipeline("translation", model="Helsinki-NLP/opus-mt-ru-en", tokenizer="Helsinki-NLP/opus-mt-ru-en")
        if translator_en_ru is None:
            translator_en_ru = pipeline("translation", model="Helsinki-NLP/opus-mt-en-ru", tokenizer="Helsinki-NLP/opus-mt-en-ru")

        english_input = is_english(user_text)
        user_text_en = translator_ru_en(user_text)[0]["translation_text"] if not english_input else user_text
        
        prompt = f"{system_instruction}\n\n{user_text_en}"
        images_b64 = []
        for att in user_msg.attachments.all():
            att.file.open('rb')
            content = att.file.read()
            att.file.close()
            mime = att.content_type.lower()
            if mime.startswith('image/') or mime.startswith('video/'):
                images_b64.append(content)
            else:
                try:
                    if mime == 'application/pdf':
                        doc = fitz.open(stream=content, filetype='pdf')
                        text = "\n".join(page.get_text() for page in doc)
                    else:
                        doc = DocxDocument(io.BytesIO(content))
                        text = "\n".join(p.text for p in doc.paragraphs)
                    prompt += f"\n[Attachment text:]\n{text}"
                except Exception:
                    pass

        resp = ollama.chat(
            model="llava:7b",
            messages=[
                {'role': 'system', 'content': system_instruction},
                {'role': 'user', 'content': prompt, 'images': images_b64 or None}
            ],
            stream=False
        )
        ai_text_en = resp['message']['content']

        if not english_input:
            lines = ai_text_en.split("\n")
            translated_lines = [translator_en_ru(line)[0]["translation_text"] for line in lines if line.strip()]
            ai_text = "\n".join(translated_lines)
        else:
            ai_text = ai_text_en

        ai_user, _ = User.objects.get_or_create(
            email='ai@localhost',
            defaults={'name': 'NeuroBot', 'avatar': 'icons/ai-avatar.png'}
        )
        
        session_for_ai = user_msg.session
        if not session_for_ai:
            logger.error(f"User message {user_msg.id} does not have a session. AI response for it will also lack a session.")

        ai_msg = Message.objects.create(
            text=ai_text,
            sender=ai_user,
            neuro_chat=True,
            session=session_for_ai
        )

        payload = MessageSerializer(ai_msg, context={'request': None}).data
        
        if not session_for_ai or not session_for_ai.id:
            logger.warning(f"AI message {ai_msg.id} created, but its session_id is None or invalid. "
                        f"Payload session ID: {payload.get('session')}. Socket.IO emit might go to the wrong room.")
        else:
            logger.info(f"AI message {ai_msg.id} created for session {session_for_ai.id}. Payload session ID: {payload.get('session')}")

        # --- Отправка сообщения через KombuManager ---
        if celery_sio_server:
            try:
                # Формируем имя комнаты так же, как это делается на стороне клиента и сервера при подключении
                room_name = f"neuro-{session_for_ai.id}" if session_for_ai and session_for_ai.id else None
                
                if room_name:
                    logger.info(f"Celery task: Attempting to emit 'neuro-chat:message-created' to room '{room_name}' via KombuManager for AI msg {ai_msg.id}.")
                    # Используем celery_sio_server.emit(), который отправит сообщение через RabbitMQ
                    celery_sio_server.emit('neuro-chat:message-created', payload, room=room_name)
                    logger.info(f"Celery task: Successfully emitted 'neuro-chat:message-created' to room '{room_name}' via KombuManager for AI msg {ai_msg.id}.")
                else:
                    logger.error(f"Celery task: Cannot emit 'neuro-chat:message-created' for AI msg {ai_msg.id} because room_name is None (session missing or invalid).")

            except Exception as e:
                logger.error(f"Celery task: Error emitting AI response for AI msg {ai_msg.id} via KombuManager: {e}", exc_info=True)
        else:
            logger.error("Celery Socket.IO bridge (celery_sio_server) is not initialized. Cannot send message.")

        return ai_msg.id

    except Message.DoesNotExist:
        logger.error(f"generate_ai_response: User message with id {user_message_id} not found.")
        return None
    except Exception as e:
        logger.error(f"generate_ai_response: Unexpected error for user_message_id {user_message_id}: {e}", exc_info=True)
        raise