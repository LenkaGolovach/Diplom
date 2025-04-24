<template>
  <div class="chat-container">
    <div class="messages-list">
      <div
        v-for="message in messages"
        :key="message.id"
        :class="['message-item', { 'own': message.sender.id === currentUser.id } ]"
      >
        <div class="avatar" v-if="message.sender.id !== currentUser.id">
          <img :src="message.sender.avatar || '/default-avatar.png'" alt="avatar">
        </div>

        <div class="message-content">
          <div class="message-header">
            <span class="sender-name" v-if="message.sender.id !== currentUser.id">
              {{ message.sender.name }}
            </span>
            <span class="message-time">
              {{ formatTime(message.created_at) }}
            </span>
          </div>

          <div class="message-body">
            <div class="reply-preview" v-if="message.reply_to">
              <span class="reply-sender">
                @{{ (message.reply_to.sender && message.reply_to.sender.name) || message.reply_to.sender.email || 'Неизвестный' }}:
              </span>
              <span class="reply-text">
                {{ message.reply_to.text || 'вложение' }}
              </span>
            </div>

            <p class="text" v-if="message.text">
              {{ message.text }}
            </p>

            <div class="attachments" v-if="message.attachments.length">
              <div
                v-for="(file, idx) in message.attachments"
                :key="idx"
                class="attachment-item"
              >
                <img 
                  v-if="isImage(file.content_type)" 
                  :src="file.url" 
                  class="attachment-img" 
                />
                <video 
                  v-else-if="isVideo(file.content_type)" 
                  controls 
                  class="attachment-video"
                >
                  <source :src="file.url" :type="file.content_type" />
                </video>
                <a 
                  v-else 
                  :href="file.url" 
                  target="_blank" 
                  class="attachment-file"
                >
                  {{ file.name }}
                </a>
              </div>
            </div>
          </div>

          <div class="message-actions">
            <button @click="startReply(message)">Ответить</button>
          </div>
        </div>
      </div>
    </div>

    <div class="chat-input-area">
      <div v-if="replyTo" class="replying-to">
        Ответ на: <strong>{{ replyTo.text }}</strong>
        <button @click="cancelReply">×</button>
      </div>

      <div v-if="attachments.length" class="selected-files">
        <div v-for="(file, index) in attachments" :key="index" class="file-item">
          <span class="file-name">{{ file.name }}</span>
          <button @click="removeAttachment(index)" class="remove-file-btn">×</button>
        </div>
      </div>

      <textarea
        ref="input"
        v-model="newMessage"
        placeholder="Напишите сообщение..."
        @keyup.enter.exact.prevent="sendMessage"
      ></textarea>

      <div class="input-actions">
        <label class="attach-btn">
          📎
          <input type="file" multiple @change="handleAttachment" hidden>
        </label>
        <button 
          @click="sendMessage" 
          :disabled="!isMessageValid"
        >
          Отправить
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
export default {
  props: {
    taskId: { type: Number, required: true }
  },
  data() {
    return {
      messages: [],
      newMessage: '',
      attachments: [],
      replyTo: null,
      currentUser: this.$store.state.user
    };
  },
  computed: {
    isMessageValid() {
      return this.newMessage.trim().length > 0 || this.attachments.length > 0;
    }
  },
  methods: {
    async fetchMessages() {
      try {
        const { data } = await axios.get(`/api/tasks/${this.taskId}/messages/`, {
          params: {
            expand: 'reply_to.sender,attachments'
          },
          headers: { 
            Authorization: `Bearer ${localStorage.getItem('token')}` 
          }
        });
        this.messages = data; 
      } catch (error) {
        console.error('Ошибка загрузки сообщений:', error);
      }
    },
    formatTime(ts) {
      return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    },
    isImage(type) { 
      return type && type.startsWith('image/');// Добавить опциональную цепочку
    },
    isVideo(type) {
      return type && type.startsWith('video/');
    },
    startReply(message) {
      this.replyTo = {
        id: message.id,
        text: message.text || 'вложение',
        sender: message.sender
      };
      this.$nextTick(() => {
        this.$refs.input.focus();
        this.$refs.input.scrollIntoView({ behavior: 'smooth' });
      });
    },
    cancelReply() {
      this.replyTo = null;
    },
    async handleAttachment(event) {
      const files = Array.from(event.target.files);
      this.attachments.push(...files);
    },
    removeAttachment(index) {
      this.attachments.splice(index, 1);
    },
    async sendMessage() {
      try {
        const form = new FormData();
        
        // Добавляем текст сообщения
        if (this.newMessage.trim()) {
          form.append('text', this.newMessage);
        }

        // Добавляем ID сообщения для ответа
        if (this.replyTo) {
          form.append('reply_to_id', this.replyTo.id); 
        }

        // Добавляем вложения
        this.attachments.forEach(file => {form.append('attachments', file); });

        // Отправка запроса
        const response = await axios.post(
          `/api/tasks/${this.taskId}/messages/`,
          form,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
              Authorization: `Bearer ${localStorage.getItem('token')}`
            }
          }
        );

        // Обновляем список сообщений
        await this.fetchMessages();
        
        // Сбрасываем состояние
        this.newMessage = '';
        this.attachments = [];
        this.replyTo = null;

      } catch (error) {
        console.error('Ошибка отправки сообщения:', error.response && error.response.data);
        alert(`Ошибка: ${(error.response && error.response.data && error.response.data.error) || 'Неизвестная ошибка'}`);
      }
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const el = this.$el.querySelector('.messages-list');
        el.scrollTop = el.scrollHeight;
      });
    }
  },
  mounted() {
    this.fetchMessages();
  }
};
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 300px;
  border: 1px solid rgba(0,0,0,0.05);
  border-radius: 8px;
  overflow: hidden;
  background: rgba(255,255,255,0.8);
}
.messages-list {
  flex: 1;
  padding: 10px;
  overflow-y: auto;
}
.message-item {
  display: flex;
  margin-bottom: 10px;
}
.message-item.own {
  flex-direction: row-reverse;
}
.avatar img {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  margin-right: 8px;
}
.message-item.own .avatar img {
  margin-left: 8px;
  margin-right: 0;
}
.message-content {
  max-width: 75%;
  display: flex;
  flex-direction: column;
}
.message-item.own .message-content {
  align-items: flex-end;
}
.message-header {
  display: flex;
  align-items: center;
  gap: 6px;
}
.sender-name {
  font-weight: 600;
  font-size: 14px;
}
.message-time {
  font-size: 12px;
  color: #64748b;
}
.message-body {
  background: #f0f0f0;
  border-radius: 8px;
  padding: 8px;
  margin-top: 4px;
}
.message-item.own .message-body {
  background: #5b9cff33;
}
.text {
  margin: 0;
  font-size: 14px;
}
.attachments {
  margin-top: 6px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.attachment-item {
  max-width: 120px;
}
.attachment-img {
  width: 100%;
  border-radius: 6px;
}
.attachment-video {
  width: 100%;
  border-radius: 6px;
}
.attachment-file {
  display: block;
  background: #fff;
  padding: 6px;
  border-radius: 6px;
  font-size: 14px;
  text-decoration: underline;
}
.message-actions button {
  background: none;
  border: none;
  font-size: 12px;
  color: #5b9cff;
  cursor: pointer;
  margin-top: 4px;
}
.chat-input-area {
  padding: 8px;
  border-top: 1px solid rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
}
.replying-to {
  font-size: 13px;
  margin-bottom: 4px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.chat-input-area textarea {
  resize: none;
  height: 60px;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-family: 'Segoe UI', sans-serif;
}
.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 6px;
}
.attach-btn {
  cursor: pointer;
  font-size: 18px;
}
.input-actions button {
  background: #5b9cff;
  color: #fff;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
}
.input-actions button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.reply-preview {
  border-left: 3px solid #4CAF50;
  margin: 8px 0;
  padding: 8px 12px;
  background: #f5f5f5;
  border-radius: 4px;
}

.reply-sender {
  color: #2c3e50;
  font-weight: 600;
  font-size: 0.9em;
}

.reply-text {
  color: #7f8c8d;
  font-size: 0.85em;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.selected-files {
  margin-bottom: 8px;
  max-width: 100%;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  background: #f0f0f0;
  border-radius: 4px;
  margin: 4px 0;
  font-size: 0.9em;
}

.file-name {
  flex-grow: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-file-btn {
  background: none;
  border: none;
  color: #ff4444;
  cursor: pointer;
  margin-left: 8px;
  padding: 0 4px;
}

.remove-file-btn:hover {
  background: rgba(255, 68, 68, 0.1);
}
</style>
