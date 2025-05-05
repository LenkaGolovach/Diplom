from celery import shared_task
import ollama
from .models import Message, FileAttachment, MessageAttachment
from django.contrib.auth import get_user_model
from .serializers import MessageSerializer
import socketio, base64, requests, io, time, logging
# For document conversion
from pdf2image import convert_from_bytes
import fitz  # PyMuPDF
from docx import Document as DocxDocument
from pptx import Presentation

# Setup
User = get_user_model()
sio = socketio.Client(reconnection=True, reconnection_attempts=5, reconnection_delay=1)
logger = logging.getLogger(__name__)

@shared_task
def generate_ai_response(user_message_id):
    start_time = time.time()
    logger.info(f"Starting AI response generation for message {user_message_id}")
    
    try:
        # Fetch the user message and initial text
        user_msg = Message.objects.get(id=user_message_id)
        prompt = user_msg.text or ""
        logger.info(f"Processing message: {prompt[:100]}...")  # Логируем первые 100 символов

        # Collect multimodal inputs
        images_b64 = []

        for att in user_msg.attachments.all():
            # Download raw bytes
            resp = requests.get(att.url)
            content = resp.content
            mime = att.type.lower()

            # Image or video: encode directly
            if mime.startswith('image/') or mime.startswith('video/'):
                b64 = base64.b64encode(content).decode()
                images_b64.append(f"data:{mime};base64,{b64}")

            # PDF -> convert each page to image
            elif mime == 'application/pdf':
                pages = convert_from_bytes(content)
                for page in pages:
                    buf = io.BytesIO()
                    page.save(buf, format='PNG')
                    b64 = base64.b64encode(buf.getvalue()).decode()
                    images_b64.append(f"data:image/png;base64,{b64}")

            # Word docx -> extract text and append to prompt
            elif mime in ('application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                          'application/msword'):
                doc = DocxDocument(io.BytesIO(content))
                text = '\n'.join(p.text for p in doc.paragraphs)
                prompt += f"\n\n[Word doc content:]\n{text}"

            # PPTX -> render slides as images
            elif mime in ('application/vnd.openxmlformats-officedocument.presentationml.presentation',
                          'application/vnd.ms-powerpoint'):
                prs = Presentation(io.BytesIO(content))
                for slide in prs.slides:
                    # simplistic: save slide background as image (if any)
                    img_buf = io.BytesIO()
                    slide.shapes._spTree.write(img_buf)
                    b64 = base64.b64encode(img_buf.getvalue()).decode()
                    images_b64.append(f"data:application/vnd.openxmlformats-officedocument.presentationml.presentation;base64,{b64}")

            # Other: try PDF-style text extract via MuPDF
            else:
                try:
                    doc = fitz.open(stream=content, filetype=None)
                    text = "\n".join(p.get_text() for p in doc)
                    prompt += f"\n\n[Document content:]\n{text}"
                except Exception:
                    # skip unknown
                    continue

        # Build chat args
        chat_kwargs = {
            'model': 'ZimaBlueAI/Qwen2.5-VL-7B-Instruct:latest',
            'messages': [{'role': 'user', 'content': prompt}],
            'stream': False
        }
        if images_b64:
            chat_kwargs['images'] = images_b64

        # Call multimodal model
        logger.info("Calling Ollama API...")
        response = ollama.chat(**chat_kwargs)
        ai_text = response['message']['content']
        logger.info(f"Got response from Ollama, length: {len(ai_text)}")

        # Create AI user if needed
        ai_user, _ = User.objects.get_or_create(
            email='ai@localhost',
            defaults={'name': 'NeuroBot', 'avatar': 'icons/ai-avatar.png'}
        )

        # Save message
        ai_msg = Message.objects.create(
            text=ai_text,
            sender=ai_user,
            neuro_chat=True
        )

        # Serialize & emit via Socket.IO
        payload = MessageSerializer(ai_msg, context={'request': None}).data
        try:
            if not sio.connected:
                sio.connect('http://127.0.0.1:8000')
            sio.emit('neuro-chat:message-created', payload, namespace='/')
            time.sleep(0.1)
        finally:
            if sio.connected:
                sio.disconnect()

        end_time = time.time()
        logger.info(f"Task completed in {end_time - start_time:.2f} seconds")
        return ai_msg.id

    except Exception as e:
        logger.error(f"Error in generate_ai_response: {str(e)}")
        raise
