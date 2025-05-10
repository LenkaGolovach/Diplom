from celery import shared_task
import ollama
from .models import Message, MessageAttachment
from django.contrib.auth import get_user_model
from .serializers import MessageSerializer
import socketio, io, tempfile, subprocess
import re
import fitz  # PyMuPDF for PDF → text
from docx import Document as DocxDocument
from pdf2image import convert_from_bytes
from transformers import pipeline, Pipeline

User = get_user_model()
sio = socketio.Client(reconnection=True, reconnection_attempts=5, reconnection_delay=1)

# Глобальная инициализация переводчиков
translator_ru_en: Pipeline | None = None
translator_en_ru: Pipeline | None = None

# Простая функция определения, на английском ли текст (нет кириллицы)
def is_english(text: str) -> bool:
    return not bool(re.search(r'[\u0400-\u04FF]', text))

@shared_task
def generate_ai_response(user_message_id):
    # Fetch the user message
    user_msg = Message.objects.get(id=user_message_id)
    user_text = user_msg.text or ""

    # System instruction: английский Markdown
    system_instruction = (
        "You are an intelligent AI assistant.\n"
        "When you answer, format the entire response in Markdown with line breaks preserved."
    )

    # Инициализируем переводчики при первом вызове
    global translator_ru_en, translator_en_ru
    if translator_ru_en is None:
        translator_ru_en = pipeline("translation", model="Helsinki-NLP/opus-mt-ru-en", tokenizer="Helsinki-NLP/opus-mt-ru-en")
    if translator_en_ru is None:
        translator_en_ru = pipeline("translation", model="Helsinki-NLP/opus-mt-en-ru", tokenizer="Helsinki-NLP/opus-mt-en-ru")

    # Определяем язык запроса
    english_input = is_english(user_text)

    # Если вход на русском (или другом не-английском), переводим на английский
    if not english_input:
        user_text_en = translator_ru_en(user_text)[0]["translation_text"]
    else:
        user_text_en = user_text

    prompt = f"{system_instruction}\n\n{user_text_en}"

    # Process attachments (не изменялось)
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

    # Получаем ответ AI на английском Markdown
    resp = ollama.chat(
        model="llava:7b",
        messages=[
            {'role': 'system', 'content': system_instruction},
            {'role': 'user', 'content': prompt, 'images': images_b64 or None}
        ],
        stream=False
    )
    ai_text_en = resp['message']['content']

    # Если вход был не на английском, переводим ответ обратно на русский построчно
    if not english_input:
        lines = ai_text_en.split("\n")
        translated_lines = []
        for line in lines:
            translated = translator_en_ru(line)[0]["translation_text"]
            translated_lines.append(translated)
        ai_text = "\n".join(translated_lines)
    else:
        ai_text = ai_text_en

    # Save AI message
    ai_user, _ = User.objects.get_or_create(
        email='ai@localhost',
        defaults={'name': 'NeuroBot', 'avatar': 'icons/ai-avatar.png'}
    )
    session = user_msg.session
    ai_msg = Message.objects.create(
        text=ai_text,
        sender=ai_user,
        neuro_chat=True,
        session=session
    )

    # Emit via Socket.IO
    payload = MessageSerializer(ai_msg, context={'request': None}).data
    try:
        if not sio.connected:
            sio.connect('http://127.0.0.1:8000', transports=['websocket'])
        sio.emit('neuro-chat:message-created', payload)
    finally:
        if sio.connected:
            sio.disconnect()

    return ai_msg.id