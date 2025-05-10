#!/usr/bin/env python

# 1) Монки-патчим перед любого рода асинхронщиной
import eventlet
# Изменяем monkey_patch, чтобы не затрагивать модуль os
eventlet.monkey_patch(os=False, subprocess=False)  # нужно для eventlet + KombuManager, os=False для Windows file I/O

import os, sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

import socketio
from django.core.wsgi import get_wsgi_application

# KombuManager для RabbitMQ, URL из ваших настроек
mgr = socketio.KombuManager('amqp://guest:guest@localhost:5672//')

# Socket.IO-сервер с внешней очередью
sio = socketio.Server(
    client_manager=mgr,
    async_mode='eventlet',
    cors_allowed_origins='*'
)

# Оборачиваем Django WSGI в Socket.IO WSGIApp
django_app = get_wsgi_application()
application = socketio.WSGIApp(sio, django_app)

# --- Обработчики подключений ---
@sio.event
def connect(sid, environ):
    # достаём query‑строку, ищем session=<id>
    qs = environ.get('QUERY_STRING','')
    params = dict(pair.split('=') for pair in qs.split('&') if '=' in pair)
    session = params.get('session')
    if session:
        room = f'neuro-{session}'
        sio.enter_room(sid, room)
        print(f"SID {sid} joined room {room}")
    print(f"Client connected: {sid}")


@sio.event
def disconnect(sid):
    print(f"Client disconnected: {sid}")

# --- Relay для нейрочата (оставляем ваш) ---
@sio.on('neuro-chat:message-created')
def handle_neuro_message_created(sid, data):
    print("RELAY got data:", data)
    session = data.get('session')
    print(" -> session in payload:", session)
    room = f'neuro-{session}'
    print(f" -> emitting to room {room}")
    sio.emit('neuro-chat:message-created', data, room=room)

# --- NEW: Relay для задач ---
@sio.on('task:message-created')
def handle_task_message_created(sid, data):
    print("Received from Celery/task:", data)
    sio.emit('task:message-created', data)      

@sio.on('task:message-updated')
def handle_task_message_updated(sid, data):
    print("Task updated:", data)
    sio.emit('task:message-updated', data)

@sio.on('task:message-deleted')
def handle_task_message_deleted(sid, data):
    print("Task deleted:", data)
    sio.emit('task:message-deleted', data)

if __name__ == '__main__':
    # Запускаем eventlet-сервер на 8000
    eventlet.wsgi.server(eventlet.listen(('', 8000)), application)
