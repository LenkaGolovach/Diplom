from celery import shared_task
import ollama
from .models import Message
from django.contrib.auth import get_user_model
from .serializers import MessageSerializer
import socketio
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

# создаём клиент, НЕ коннектимся при импорте
sio = socketio.Client(
    reconnection=True,
    reconnection_attempts=5,
    reconnection_delay=1
)

@shared_task
def generate_ai_response(user_message_id):
    user_msg = Message.objects.get(id=user_message_id)
    prompt  = user_msg.text

    response = ollama.chat(
        model='mistral',
        messages=[{'role':'user','content':prompt}],
        stream=False
    )
    ai_text = response['message']['content']

    ai_user, _ = User.objects.get_or_create(
        email='ai@localhost',
        defaults={'name':'NeuroBot','avatar':'icons/ai-avatar.png'}
    )

    ai_msg = Message.objects.create(
       text=ai_text,
       sender=ai_user,
       neuro_chat=True
    )
    payload = MessageSerializer(ai_msg, context={'request':None}).data

    # эмитим ответ ИИ в Socket.IO
    try:
        if not sio.connected:
            sio.connect('http://127.0.0.1:8000')  # подключаемся к серверу 
        sio.emit('neuro-chat:message-created', payload, namespace='/')  # отправляем событие 
        # даём time-slice eventlet, чтобы пакет точно ушёл, иначе emit может быть отброшен 
        import eventlet
        eventlet.sleep(0)
    finally:
        if sio.connected:
            sio.disconnect()  

    return ai_msg.id
