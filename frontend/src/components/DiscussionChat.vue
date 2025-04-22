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
            <template v-if="message.replyTo">
              <div class="reply-preview">
                <span class="reply-sender">@{{ message.replyTo.sender.name }}:</span>
                <span class="reply-text">{{ message.replyTo.text }}</span>
              </div>
            </template>

            <p class="text" v-if="message.text">
              {{ message.text }}
            </p>

            <div class="attachments" v-if="message.attachments.length">
              <div
                v-for="(file, idx) in message.attachments"
                :key="idx"
                class="attachment-item"
              >
                <img v-if="isImage(file.type)" :src="file.url" class="attachment-img" />
                <video v-else-if="isVideo(file.type)" controls class="attachment-video">
                  <source :src="file.url" :type="file.type" />
                </video>
                <a v-else :href="file.url" target="_blank" class="attachment-file">
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

      <textarea
        v-model="newMessage"
        placeholder="Напишите сообщение..."
        @keyup.enter.exact.prevent="sendMessage"
      ></textarea>

      <div class="input-actions">
        <label class="attach-btn">
          📎
          <input type="file" multiple @change="handleAttachment" hidden>
        </label>
        <button @click="sendMessage" :disabled="!newMessage.trim() && !attachments.length">
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
  methods: {
    async fetchMessages() {
      const { data } = await axios.get(`/api/tasks/${this.taskId}/messages/`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      this.messages = data;
      this.scrollToBottom();
    },
    formatTime(ts) {
      return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    },
    isImage(type) { return type.startsWith('image/'); },
    isVideo(type) { return type.startsWith('video/'); },
    startReply(message) {
      this.replyTo = message;
      this.$nextTick(() => this.$refs.input.focus());
    },
    cancelReply() {
      this.replyTo = null;
    },
    async handleAttachment(event) {
      const files = Array.from(event.target.files);
      this.attachments.push(...files);
    },
    async sendMessage() {
      try {
        const form = new FormData();
        
        if (this.newMessage.trim()) {
          form.append('text', this.newMessage);
        }
        
        if (this.replyTo) {
          form.append('reply_to', this.replyTo.id);
        }
        
        this.attachments.forEach(file => {
          form.append('attachments', file);
        });

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

        this.messages.push(response.data);
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
    // можно подписаться на вебсокеты для реального времени
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
.reply-preview {
  border-left: 3px solid #5b9cff;
  padding-left: 6px;
  margin-bottom: 4px;
  font-size: 13px;
  color: #64748b;
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
</style>
