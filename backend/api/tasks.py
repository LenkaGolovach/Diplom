from celery import shared_task
import ollama
from .models import Message, MessageAttachment
from django.contrib.auth import get_user_model
from .serializers import MessageSerializer
import socketio, base64, io, tempfile, subprocess
import fitz  # PyMuPDF for PDF → text
from docx import Document as DocxDocument
from pptx import Presentation
from pdf2image import convert_from_bytes

User = get_user_model()
sio = socketio.Client(reconnection=True, reconnection_attempts=5, reconnection_delay=1)

@shared_task
def generate_ai_response(user_message_id):
    # Fetch the user message
    user_msg = Message.objects.get(id=user_message_id)
    user_text = user_msg.text or ""

    # System instruction to lock Russian language and formatting
    system_instruction = (
        "Ты — интеллигентный AI-помощник. "
        "Отвечай **исключительно** на русском языке. "
        "Не используй другие языки, кроме случаев, когда необходимо привести формулу или точную цитату."
    )

    prompt = f"{system_instruction}\n\n{user_text}"

    images_b64 = []

    # Process attachments
    for att in user_msg.attachments.all():
        att.file.open('rb')
        content = att.file.read()
        att.file.close()
        mime = att.content_type.lower()

        # Image or video → raw bytes
        if mime.startswith('image/') or mime.startswith('video/'):
            images_b64.append(content)

        # PDF → extract text
        elif mime == 'application/pdf':
            doc = fitz.open(stream=content, filetype='pdf')
            text = "\n".join(page.get_text() for page in doc)
            prompt += f"\n\n[PDF text:]\n{text}"

        # DOCX → extract text
        elif mime in (
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword'
        ):
            doc = DocxDocument(io.BytesIO(content))
            text = "\n".join(p.text for p in doc.paragraphs)
            prompt += f"\n\n[Word text:]\n{text}"

        # PPTX → convert slides to images for true vision
        elif mime in (
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/vnd.ms-powerpoint'
        ):
            # save pptx to temp file
            with tempfile.NamedTemporaryFile(suffix='.pptx', delete=False) as f_pptx:
                f_pptx.write(content)
                pptx_path = f_pptx.name

            # convert PPTX→PDF via LibreOffice headless
            subprocess.run([
                'soffice', '--headless', '--convert-to', 'pdf', '--outdir', tempfile.gettempdir(), pptx_path
            ], check=True)
            pdf_path = pptx_path.rsplit('.pptx', 1)[0] + '.pdf'

            # convert PDF pages → images
            pages = convert_from_bytes(open(pdf_path, 'rb').read())
            for page in pages:
                buf = io.BytesIO()
                page.save(buf, format='PNG')
                images_b64.append(buf.getvalue())

        # other docs → try PyMuPDF text
        else:
            try:
                doc = fitz.open(stream=content, filetype=None)
                text = "\n".join(p.get_text() for p in doc)
                prompt += f"\n\n[Document text:]\n{text}"
            except Exception:
                continue

    # Use chat API with roles and images
    resp = ollama.chat(
        model="llava:7b", 
        messages=[
            {'role': 'system', 'content': system_instruction},
            {'role': 'user', 'content': prompt, 'images': images_b64 or None}
        ],
        stream=False
    )
    ai_text = resp['message']['content']

    # Save AI message
    ai_user, _ = User.objects.get_or_create(
        email='ai@localhost',
        defaults={'name': 'NeuroBot', 'avatar': 'icons/ai-avatar.png'}
    )
    ai_msg = Message.objects.create(text=ai_text, sender=ai_user, neuro_chat=True)

    # Emit via Socket.IO (server as sole emitter)
    payload = MessageSerializer(ai_msg, context={'request': None}).data
    try:
        if not sio.connected:
            sio.connect('http://127.0.0.1:8000', transports=['websocket'])
        sio.emit('neuro-chat:message-created', payload, namespace='/')
        import time; time.sleep(0.1)
    finally:
        if sio.connected:
            sio.disconnect()

    return ai_msg.id