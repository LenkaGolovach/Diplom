<template>
  <div class="chat-container">
    <div class="messages-list">
      <template v-for="(group, date) in groupedMessages" :key="date">
        <div class="date-divider">
          {{ formatDateDivider(date) }}
        </div>
        <div 
          v-for="message in group" 
          :key="message.id"
          :class="['message-item', { 'own': message.sender.id === currentUser.id }]"
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
                <span v-if="message.is_edited" class="edited-mark">ред.</span>
              </span>
            </div>

            <div class="message-body" v-if="!message.is_deleted">
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
                  <div class="attachment-preview">
                    <img
                      v-if="isImage(file.content_type)"
                      :src="file.url"
                      class="attachment-thumb"
                    />
                    <video
                      v-else-if="isVideo(file.content_type)"
                      :src="file.url"
                      class="attachment-thumb"
                    ></video>
                    <img
                      v-else
                      src="/icons/file-icon.png"
                      class="file-icon"
                    />
                  </div>
                  <a 
                    :href="file.url" 
                    target="_blank"
                    class="attachment-name"
                  >
                    {{ file.name }}
                  </a>
                </div>
              </div>
            </div>

            <div v-else class="deleted-message">
              Сообщение удалено
            </div>

            <div class="message-actions">
              <button @click="startReply(message)">
                <img src="/icons/reply-icon.png" class="action-icon">
              </button>
              <button @click="editMessage(message)" v-if="message.sender.id === currentUser.id">
                <img src="/icons/edit-icon.png" class="action-icon">
              </button>
              <button @click="deleteMessage(message)" v-if="message.sender.id === currentUser.id">
                <img src="/icons/delete-icon.png" class="action-icon">
              </button>
              <button @click="copyMessage(message)">
                <img src="/icons/copy-icon.png" class="action-icon">
              </button>
            </div>
          </div>
        </div>
      </template>
    </div>

    <div class="chat-input-area">
      <div v-if="replyTo" class="replying-to">
        Ответ на: <strong>{{ replyTo.text }}</strong>
        <button @click="cancelReply">×</button>
      </div>

      <!-- Блок режима редактирования -->
      <div v-if="editingMessage" class="editing-notice">
        Редактирование сообщения
        <button @click="cancelEdit">×</button>
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
          <img src="/icons/attach-icon.png" class="action-icon">
          <input type="file" multiple @change="handleAttachment" hidden>
        </label>
        <button 
          @click="sendMessage" 
          :disabled="!isMessageValid"
        >
          {{ editingMessage ? 'Сохранить' : 'Отправить' }}
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
      currentUser: this.$store.state.user,
      editingMessage: null,
      pollInterval: null,
    };
  },
  computed: {
    isMessageValid() {
      return (this.newMessage && this.newMessage.trim().length > 0) || this.attachments.length > 0;
    },
    groupedMessages() {
      const groups = {}
      this.messages.forEach(msg => {
        const date = new Date(msg.created_at).toISOString().split('T')[0]
        if (!groups[date]) groups[date] = []
        groups[date].push(msg)
      })
      return groups
    }
  },
  methods: {
    startPolling() {
      this.pollInterval = setInterval(() => {
        this.fetchMessages();
      }, 3000); // Опрашиваем сервер каждые 3 секунды
    },
    async fetchMessages() {
      try {
        const { data } = await axios.get(`/api/tasks/${this.taskId}/messages/`, {
          params: { expand: 'reply_to.sender,attachments' },
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        
        // Обновляем только если есть изменения
        if (JSON.stringify(this.messages) !== JSON.stringify(data)) {
          this.messages = data;
        }
      } catch (error) {
        console.error('Ошибка загрузки сообщений:', error);
      }
    },
    formatTime(ts) {
      return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    },
    formatDateDivider(dateStr) {
      const date = new Date(dateStr)
      return new Intl.DateTimeFormat('ru-RU', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
        weekday: 'short'
      }).format(date).replace(/,/g, '')
    },
    isImage(type) { 
      return type && type.startsWith('image/')
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
        if (this.editingMessage) {
          // Режим редактирования
          const form = new FormData();
      
          // Сохраняем текст даже если он пустой
          form.append('text', this.newMessage ? this.newMessage.trim() : '');
          
          // Добавляем существующие вложения
          this.attachments.forEach(file => {
            if (file instanceof File) {
              form.append('attachments', file);
            } else {
              // Для уже загруженных файлов
              form.append('keep_attachments', file.id);
            }
          });
          
          // Сохраняем ответ если был
          if (this.replyTo) {
            form.append('reply_to_id', this.replyTo.id);
          }
          
          await axios.patch(
            `/api/tasks/${this.taskId}/messages/${this.editingMessage.id}/`,
            form,
            {
              headers: {
                'Content-Type': 'multipart/form-data',
                Authorization: `Bearer ${localStorage.getItem('token')}`
              }
            }
          );
          
          await this.fetchMessages();
          this.cancelEdit();
        } else {
          // Оригинальная логика отправки нового сообщения
          const form = new FormData();
          if (this.newMessage.trim()) form.append('text', this.newMessage);
          if (this.replyTo) form.append('reply_to_id', this.replyTo.id);
          this.attachments.forEach(file => form.append('attachments', file));

          await axios.post(`/api/tasks/${this.taskId}/messages/`, form, {
            headers: {
              'Content-Type': 'multipart/form-data',
              Authorization: `Bearer ${localStorage.getItem('token')}`
            }
          });

          await this.fetchMessages();
          this.newMessage = '';
          this.attachments = [];
          this.replyTo = null;
        }
        
        this.scrollToBottom();
      } catch (error) {
        console.error('Ошибка отправки сообщения:', error.response && error.response.data);
        alert(`Ошибка: ${(error.response && error.response.data && error.response.data.error) || 'Неизвестная ошибка'}`);
      }
    },
    async deleteMessage(message) {
      if (confirm('Удалить сообщение?')) {
        try {
          await axios.delete(`/api/tasks/${this.taskId}/messages/${message.id}/`);
          await this.fetchMessages();
        } catch (error) {
          console.error('Ошибка удаления:', error);
        }
      }
    },
    copyMessage(message) {
      navigator.clipboard.writeText(message.text);
    },
    cancelEdit() {
      this.editingMessage = null;
      this.newMessage = '';
      this.replyTo = null;
      this.attachments = [];
    },

    editMessage(message) {
      if (message.is_deleted) return;
      this.editingMessage = message;
      this.newMessage = message.text || '';
      
      // Сохраняем оригинальные вложения и ответ
      this.replyTo = message.reply_to 
        ? {...message.reply_to} 
        : null;
        
      this.attachments = message.attachments.length
        ? [...message.attachments] // Копируем вложения
        : [];
      
      this.$refs.input.focus();
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
    this.startPolling();
  },
  beforeUnmount() {
    clearInterval(this.pollInterval);
  },
};
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 500px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: #fff;
}

.messages-list {
  flex: 1;
  padding: 15px;
  overflow-y: auto;
  background: #f8f9fa;
}

.date-divider {
  text-align: center;
  margin: 20px 0;
  color: #6c757d;
  font-size: 0.9em;
  position: relative;
}

.date-divider:before,
.date-divider:after {
  content: "";
  flex: 1;
  border-bottom: 1px solid #dee2e6;
  margin: auto 10px;
}

.message-item {
  display: flex;
  margin-bottom: 15px;
  position: relative;
}

.message-item.own {
  flex-direction: row-reverse;
}

.message-item.own .message-content {
  margin-left: auto;
}

.avatar img {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  margin-right: 12px;
}

.message-content {
  max-width: 75%;
  min-width: 200px;
  position: relative;
}

.message-header {
  display: flex;
  align-items: center;
  margin-bottom: 5px;
}

.sender-name {
  font-weight: 600;
  margin-right: 8px;
}

.message-time {
  color: #6c757d;
  font-size: 0.8em;
}

.edited-mark {
  color: #6c757d;
  font-size: 0.8em;
  margin-left: 5px;
}

.message-body {
  background: #fff;
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.message-item.own .message-body {
  background: #e3f2fd;
}

.text {
  margin: 0;
  color: #212529;
  line-height: 1.5;
}

.attachments {
  margin-top: 10px;
}

.attachment-item {
  display: flex;
  align-items: center;
  margin: 8px 0;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 8px;
}

.attachment-preview {
  width: 40px;
  height: 40px;
  margin-right: 10px;
  flex-shrink: 0;
}

.attachment-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 4px;
}

.file-icon {
  width: 100%;
  height: 100%;
  object-fit: contain;
  opacity: 0.7;
}

.attachment-name {
  color: #212529;
  text-decoration: none;
  font-size: 0.9em;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.attachment-name:hover {
  text-decoration: underline;
}

.message-actions {
  position: absolute;
  top: -10px;
  display: flex;
  gap: 3px;
  opacity: 0;
  transition: opacity 0.2s;
  background: white;
  padding: 3px;
  border-radius: 15px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  z-index: 1;
}

.message-item .message-actions {
  right: -15px;
}

.message-item:not(.own) .message-actions {
  left: -5px;
  right: auto;
}

.message-item:not(.own) .message-actions {
  flex-direction: row-reverse;
}

.message-item:hover .message-actions {
  opacity: 1;
}

.message-item.own .message-actions {
  background: #e3f2fd;
  box-shadow: 0 3px 3px rgba(0,0,0,0.1);
}

/* Уменьшаем отступы для компактности */
.message-actions button {
  padding: 0;
  line-height: 1;
}

/* Фикс выравнивания иконок */
.message-actions button img {
  vertical-align: middle;
}

.action-icon {
  width: 16px;
  height: 16px;
  padding: 4px;
  transition: all 0.2s;
  display: block;
}

.action-icon:hover {
  opacity: 1;
}

.deleted-message {
  color: #6c757d;
  font-style: italic;
}

.chat-input-area {
  padding: 15px;
  border-top: 1px solid #dee2e6;
  background: #fff;
  box-sizing: border-box;
}

.replying-to {
  background: #f8f9fa;
  padding: 8px;
  border-radius: 6px;
  margin-bottom: 10px;
}

.selected-files {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.file-item {
  background: #f8f9fa;
  padding: 6px 12px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  font-size: 0.9em;
}

.remove-file-btn {
  margin-left: 8px;
  color: #dc3545;
  background: none;
  border: none;
}

textarea {
  width: calc(100% - 24px); /* Учитываем padding */
  padding: 12px;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  resize: none;
  min-height: 80px;
  margin: 0;
  box-sizing: border-box;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.attach-btn {
  cursor: pointer;
  display: flex;
  align-items: center;
}

button[type="submit"] {
  background: linear-gradient(135deg, #007bff, #0056b3);
  color: white;
  padding: 10px 25px;
  border-radius: 25px;
  border: none;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
  box-shadow: 0 3px 6px rgba(0,123,255,0.2);
}

button[type="submit"]:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 5px 10px rgba(0,123,255,0.3);
}

button[type="submit"]::after {
  content: '➤';
  font-size: 1.1em;
}

button:has(img[src="/icons/copy-icon.png"]) {
  order: 1; /* Перемещаем в конец ряда */
}

.reply-preview {
  border-left: 3px solid #4CAF50;
  padding-left: 10px;
  margin: 10px 0;
  color: #6c757d;
  font-size: 0.9em;
}
</style>