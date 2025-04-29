<template>
  <div class="chat-container">
    <div class="messages-list">
      <template v-for="(group, date) in groupedMessages" :key="date">
        <div class="date-divider">{{ formatDateDivider(date) }}</div>

        <div
          v-for="message in group"
          :key="message.id"
          :class="['message-item', { own: message.sender.id === current.id }]"
        >
          <div class="avatar" v-if="message.sender.id !== current.id">
            <img :src="message.sender.avatar || '/default-avatar.png'" alt="avatar">
          </div>

          <div class="message-content">
            <div class="message-header">
              <span class="sender-name" v-if="message.sender.id !== current.id">
                {{ message.sender.name || message.sender.email }}
              </span>
              <span class="message-time">
                {{ formatTime(message.created_at) }}
                <span v-if="message.is_edited" class="edited-mark">ред.</span>
              </span>
            </div>

            <div class="message-body" v-if="!message.is_deleted">
              <div class="reply-preview" v-if="message.reply_to">
                <span class="reply-sender">
                  @{{ message.reply_to.sender.name || message.reply_to.sender.email }}:
                </span>
                <span class="reply-text">
                  {{ message.reply_to.text || 'вложение' }}
                </span>
              </div>
              <p class="text" v-if="message.text">{{ message.text }}</p>
              <div class="attachments" v-if="message.attachments.length">
                <div v-for="(file, idx) in message.attachments" :key="idx" class="attachment-item">
                  <div class="attachment-preview">
                    <img v-if="isImage(file.type)" :src="file.url" class="attachment-thumb" />
                    <video v-else-if="isVideo(file.type)" :src="file.url" class="attachment-thumb"></video>
                    <img v-else src="/icons/file-icon.png" class="file-icon" />
                  </div>
                  <a :href="file.url" target="_blank" class="attachment-name">{{ file.name }}</a>
                </div>
              </div>
            </div>
            <div v-else class="deleted-message">Сообщение удалено</div>

            <div class="message-actions">
              <button @click="startReply(message)"><img src="/icons/reply-icon.png" class="action-icon"></button>
              <button @click="editMessage(message)" v-if="message.sender.id === current.id">
                <img src="/icons/edit-icon.png" class="action-icon">
              </button>
              <button @click="deleteMessage(message)" v-if="message.sender.id === current.id">
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

    <div v-if="aiThinking" class="ai-thinking">
      <img src="/icons/ai-spinner.gif" alt="loading" class="ai-spinner" />
      ИИ отвечает…
   </div>

    <div class="chat-input-area">
      <div v-if="replyTo" class="replying-to">
        Ответ на: <strong>{{ replyTo.text }}</strong>
        <button @click="cancelReply">×</button>
      </div>

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
        @keyup.enter.exact.prevent="onSendClick"
      ></textarea>

      <div class="input-actions">
        <label class="attach-btn">
          <img src="/icons/attach-icon.png" class="action-icon">
          <input type="file" multiple @change="handleAttachment" hidden>
        </label>
        <button @click="onSendClick" :disabled="!isMessageValid">
          {{ editingMessage ? 'Сохранить' : 'Отправить' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { io } from 'socket.io-client'
import { mapState } from 'vuex'

export default {
  name: 'DiscussionChat',

  props: {
    taskId: { type: [Number, String], default: null },
    fetchMessages: { type: Function, default: null },
    sendMessage: { type: Function, default: null },
    messages: { type: Array, default: null },
    currentUser: { type: Object, default: () => ({ id: null }) },  
    iconPath: { type: String, default: '/default-avatar.png' },
    socketQuery: { type: Object, default: () => ({}) },
    aiThinking: { type: Boolean, default: false }
  },

  data() {
    return {
      internalMessages: [],
      newMessage: '',
      attachments: [],
      replyTo: null,
      editingMessage: null,
      socket: null
    }
  },

  computed: {
    ...mapState(['user']),  

    current() {
      return this.currentUser.id != null ? this.currentUser : this.user  
    },

    // Always render internalMessages, which we initialize from props or load
    allMessages() {
      return this.internalMessages
    },

    isMessageValid() {
      return (this.newMessage && this.newMessage.trim()) || this.attachments.length
    },

    groupedMessages() {
      const groups = {}
      this.allMessages.forEach(msg => {  
        const date = new Date(msg.created_at).toISOString().split('T')[0]
        if (!groups[date]) groups[date] = []
        groups[date].push(msg)
      })
      return groups
    }
  },

  methods: {
    formatTime(ts) {
      return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    },

    formatDateDivider(dateStr) {
      const date = new Date(dateStr)
      return new Intl.DateTimeFormat('ru-RU', {
        day: 'numeric', month: 'long', year: 'numeric', weekday: 'short'
      }).format(date).replace(/,/g, '')
    },

    isImage(type) { return type && type.startsWith('image/') },
    isVideo(type) { return type && type.startsWith('video/') },

    startReply(message) {
      this.replyTo = { id: message.id, text: message.text || 'вложение', sender: message.sender }
      this.$nextTick(() => this.$refs.input.focus())
    },

    cancelReply() { this.replyTo = null },
    handleAttachment(e) { this.attachments.push(...Array.from(e.target.files)) },
    removeAttachment(i) { this.attachments.splice(i, 1) },

    async loadMessages() {
      if (this.fetchMessages) {
        await this.fetchMessages()
        // Sync fetched prop messages into internalMessages
        if (Array.isArray(this.messages)) {
          this.internalMessages = [...this.messages]
        }
      } else if (this.taskId != null) {
        const { data } = await axios.get(
          `/api/tasks/${this.taskId}/messages/`,
          {
            params: { expand: 'reply_to.sender,attachments' },
            headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
          }
        )
        this.internalMessages = data
      }
    },

    async onSendClick() {
      const form = new FormData()
      if (this.newMessage.trim()) form.append('text', this.newMessage)
      if (this.replyTo) form.append('reply_to_id', this.replyTo.id)
      this.attachments.forEach(f => form.append('attachments', f))

      if (this.editingMessage) {
        // PATCH-запрос
        const updated = this.sendMessage
          ? await this.sendMessage(this.editingMessage.id, form)
          : (await axios.patch(
              `/api/tasks/${this.taskId}/messages/${this.editingMessage.id}/`, // Исправлено
              form,
              { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
            )).data

        const idx = this.internalMessages.findIndex(m => m.id === this.editingMessage.id)
        if (idx !== -1) {
          this.internalMessages.splice(idx, 1, updated)
        }
        this.editingMessage = null
      } else {
        // Optimistic UI
        const tmpId = Date.now()
        const tmp = {
          id: tmpId,
          text: this.newMessage,
          sender: this.current,
          created_at: new Date().toISOString(),
          attachments: []
        }
        this.internalMessages.push(tmp)
        this.scrollToBottom()

        try {
          const response = this.sendMessage
            ? await this.sendMessage(null, form)
            : await axios.post(
                `/api/tasks/${this.taskId}/messages/`, // Исправлено
                form,
                { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }} // Исправлено
              )
          const real = response.data || response
          const i = this.internalMessages.findIndex(m => m.id === tmpId)
          if (i !== -1) {
            this.internalMessages.splice(i, 1, real)
          }
          const channel = this.socketQuery.neuroChat ? 'neuro-chat' : 'task'
          this.socket.emit(`${channel}:message-created`, real)
        } catch (e) {
          this.internalMessages = this.internalMessages.filter(m => m.id !== tmpId)
          throw e
        }
      }

      this.newMessage = ''
      this.attachments = []
      this.replyTo = null
    },

    cancelEdit() { this.editingMessage = null },

    async deleteMessage(msg) {
      if (!confirm('Удалить сообщение?')) return

      this.internalMessages = this.internalMessages.filter(m => m.id !== msg.id)

      if (this.sendMessage) {
        await this.sendMessage(msg.id, null, 'delete')
      } else {
        await axios.delete(
          `/api/tasks/${this.taskId}/messages/${msg.id}/`, // Исправлено
          { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }} // Исправлено
        )
      }
    },

    copyMessage(msg) { navigator.clipboard.writeText(msg.text) },
    
    editMessage(msg) {
      if (msg.is_deleted) return
      this.editingMessage = msg
      this.newMessage = msg.text || ''
      this.replyTo = msg.reply_to ? { ...msg.reply_to } : null
      this.attachments = msg.attachments.length ? [...msg.attachments] : []
      this.$refs.input.focus()
    },

    scrollToBottom() {
      this.$nextTick(() => {
        const el = this.$el.querySelector('.messages-list')
        el.scrollTop = el.scrollHeight
      })
    }
  },

  mounted() {
    this.socket = io('http://localhost:8000', {
      path: '/socket.io',
      transports: ['websocket'],
      query: this.socketQuery
    })

    if (this.socketQuery && this.socketQuery.neuroChat) {
    this.socket.on('neuro-chat:message-created', (msg) => {
      if (msg && msg.id) {
        const exists = this.internalMessages.some(m => m.id === msg.id)
        if (!exists) {
          msg.sender = {
            ...msg.sender,
            name: 'Нейрочат',
            avatar: this.iconPath
          }
          this.internalMessages.push(msg)
          this.scrollToBottom()
        }
      }
    })
  }

    this.socket.on('connect', () => {
      console.log('Socket connected, sid =', this.socket.id)
    })

    const channel = this.socketQuery && this.socketQuery.neuroChat ? 'neuro-chat' : 'task'

    this.socket.on(channel + ':message-created', msg => {
      if (msg && msg.id && this.internalMessages) {
        let exists = false
        for (let i = 0; i < this.internalMessages.length; i++) {
          if (this.internalMessages[i].id === msg.id) {
            exists = true
            break
          }
        }
        if (!exists) {
          if (msg.sender && msg.sender.email === 'ai@localhost') {
            msg.sender.name = 'Нейрочат'
            msg.sender.avatar = this.iconPath
          }
          this.internalMessages.push(msg)
          this.scrollToBottom()
        }
      }
    })

    this.socket.on(channel + ':message-updated', upd => {
      if (upd && upd.id && this.internalMessages) {
        for (let i = 0; i < this.internalMessages.length; i++) {
          if (this.internalMessages[i].id === upd.id) {
            this.$set(this.internalMessages, i, upd)
            break
          }
        }
      }
    })

    this.socket.on(channel + ':message-deleted', d => {
      if (d && d.id && this.internalMessages) {
        this.internalMessages = this.internalMessages.filter(function(m) {
          return m.id !== d.id
        })
      }
    })

    this.loadMessages().then(() => {
      this.scrollToBottom()
    })
  },

  beforeUnmount() {
    if (this.socket) this.socket.disconnect()
  }
}
</script>



<style scoped>
.text {
  /* preserve newlines */
  white-space: pre-wrap;
}

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

/* стили для индикатора */
.ai-thinking {
  text-align: center;
  padding: 8px;
  color: #555;
  font-style: italic;
}

.ai-spinner {
  width: 20px;
  vertical-align: middle;
  margin-right: 6px;
}
</style>