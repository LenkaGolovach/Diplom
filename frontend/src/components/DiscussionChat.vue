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
                <div class="reply-quote-bar"></div>
                <div class="reply-body">
                  <span class="reply-sender">
                    @{{ message.reply_to.sender.name || message.reply_to.sender.email }}
                  </span>
                  <div class="reply-text" v-html="renderMarkdown(message.reply_to.text)"></div>
                </div>
              </div>


              <div class="text" v-if="message.text" v-html="renderMarkdown(message.text)"></div>

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
              <button @click="copyMessage($event,message)">
                <img src="/icons/copy-icon.png" class="action-icon">
              </button>
              <button @click="forwardToNeuro(message)">
                <img src="/icons/ai-avatar.png" class="action-icon" alt="Forward to AI">
              </button>
            </div>
          </div>
        </div>
      </template>
    </div>

    <div v-if="aiThinking" class="ai-thinking">
      <img src="/icons/ai-spinner.png" alt="AI Thinking" class="spinner-icon" />
      <span class="thinking-text">Нейрочат думает...</span>
    </div>

    <div class="chat-input-area">
      <div v-if="replyTo" class="replying-to">
        <span class="reply-to-label">Ответ на:</span>
        <strong class="reply-to-text-preview" v-html="renderMarkdown(replyTo.text)"></strong>
        <button @click="cancelReply" class="cancel-reply-button">×</button>
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

      <div class="main-input-controls">
        <textarea
          ref="input"
          v-model="newMessage"
          placeholder="Напишите сообщение..."
          @keyup.enter.exact.prevent="onSendClick"
        ></textarea>

        <div class="input-actions">
          <label class="attach-btn action-button-wrapper">
            <img src="/icons/attach-icon.png" class="action-icon" alt="Прикрепить">
            <input type="file" multiple @change="handleAttachment" hidden>
          </label>
          <button
            @click="onSendClick"
            :disabled="!isMessageValid"
            class="send-button action-button-wrapper"
            :title="editingMessage ? 'Сохранить изменения' : 'Отправить сообщение'"
          >
            <svg v-if="!editingMessage" class="action-icon" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"></path>
            </svg>
            <svg v-else class="action-icon" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
              <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"></path>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { io } from 'socket.io-client'
import { mapState } from 'vuex'
import MarkdownIt from 'markdown-it'
import he from 'he'

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
      const cu = this.currentUser || {}
      const storeUser = this.user || {}
      return (cu.id != null) ? cu : storeUser
    },
    allMessages() { return this.internalMessages },
    isMessageValid() { return (this.newMessage && this.newMessage.trim()) || this.attachments.length },
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

  created() {
    this.md = new MarkdownIt({ html: false, linkify: true, typographer: true, breaks: true })
  },

  methods: {
    decodeHtml(str) { return str ? he.decode(str) : '' },
    renderMarkdown(text) {
      const decoded = this.decodeHtml(text)
      return this.md.render(decoded)
    },
    formatTime(ts) { return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) },
    formatDateDivider(dateStr) {
      const date = new Date(dateStr)
      return new Intl.DateTimeFormat('ru-RU',{ day:'numeric',month:'long',year:'numeric',weekday:'short' }).format(date).replace(/,/g,'')
    },
    isImage(type) { return type && type.startsWith('image/') },
    isVideo(type) { return type && type.startsWith('video/') },
    startReply(message) { this.replyTo = { id: message.id, text: message.text||'', sender: message.sender }; this.$nextTick(()=>this.$refs.input.focus()) },
    cancelReply() { this.replyTo = null },
    handleAttachment(e) { this.attachments.push(...Array.from(e.target.files)) },
    removeAttachment(i) { this.attachments.splice(i,1) },

    async loadMessages() {
      if (this.fetchMessages) {
        await this.fetchMessages().catch(e=>console.warn(e))
        if (Array.isArray(this.messages)) this.internalMessages = this.messages
      } else if (this.taskId!=null) {
        const { data } = await axios.get(`/api/tasks/${this.taskId}/messages/`,{ params:{ expand:'reply_to.sender,attachments'}, headers:{ Authorization:`Bearer ${localStorage.getItem('token')}` } })
        this.internalMessages = data
      }
    },

    async onSendClick() {
      const form = new FormData()
      if (this.newMessage.trim()) form.append('text', this.newMessage)
      if (this.replyTo) form.append('reply_to_id', this.replyTo.id)
      this.attachments.forEach(f=>form.append('attachments',f))

      if (this.editingMessage) {
        const updated = this.sendMessage ? await this.sendMessage(this.editingMessage.id, form) : (await axios.patch(`/api/tasks/${this.taskId}/messages/${this.editingMessage.id}/`, form, { headers:{ Authorization:`Bearer ${localStorage.getItem('token')}` } })).data
        const idx = this.internalMessages.findIndex(m=>m.id===this.editingMessage.id)
        if (idx!==-1) this.internalMessages.splice(idx,1,updated)
        this.editingMessage=null
      } else {
        const tmpId=Date.now(), tmp={id:tmpId,text:this.newMessage,sender:this.current,created_at:new Date().toISOString(),attachments:[]}
        this.internalMessages.push(tmp); this.scrollToBottom()
        try {
          const response = this.sendMessage ? await this.sendMessage(null,form) : await axios.post(`/api/tasks/${this.taskId}/messages/`, form, { headers:{ Authorization:`Bearer ${localStorage.getItem('token')}` } })
          const real = response.data||response; const i=this.internalMessages.findIndex(m=>m.id===tmpId); if(i!==-1) this.internalMessages.splice(i,1,real)
          const channel=this.socketQuery.neuroChat?'neuro-chat':'task'; this.socket.emit(`${channel}:message-created`, real)
        } catch(e){ this.internalMessages=this.internalMessages.filter(m=>m.id!==tmpId); throw e }
      }
      this.newMessage=''; this.attachments=[]; this.replyTo=null
    },

    cancelEdit() { this.editingMessage=null },
    async deleteMessage(msg) {
      if(!confirm('Удалить сообщение?'))return; this.internalMessages=this.internalMessages.filter(m=>m.id!==msg.id)
      if(this.sendMessage) await this.sendMessage(msg.id,null,'delete')
      else await axios.delete(`/api/tasks/${this.taskId}/messages/${msg.id}/`,{ headers:{ Authorization:`Bearer ${localStorage.getItem('token')}` } })
    },
    copyMessage(event, message) {
      // находим ближайший .message-item от кнопки
      const btn = event.currentTarget;
      const item = btn.closest('.message-item');
      if (!item) {
        // fallback — просто текст из модели
        return navigator.clipboard.writeText(message.text || '');
      }
      // внутри него ищем отрендеренный блок .text
      const textEl = item.querySelector('.text');
      const toCopy = textEl
        ? textEl.innerText.trim()
        : (message.text || '');

      navigator.clipboard.writeText(toCopy);
    },
    async forwardToNeuro(message) {
      // Сброс предыдущего состояния
      this.replyTo = { id: message.id, text: message.text || '', sender: message.sender }
      this.attachments = []

      // Подтянуть каждое вложение по URL и превратить в File
      for (const att of message.attachments) {
        try {
          const res = await fetch(att.url)
          const blob = await res.blob()
          const file = new File([blob], att.name, { type: att.type })
          this.attachments.push(file)
        } catch (err) {
          console.warn('Не удалось загрузить вложение для пересылки', att.url, err)
        }
      }

      // Префилдим новое сообщение подсказкой (по желанию)
      this.newMessage = 'Пожалуйста, сделай краткое содержание…';
      // запомним в сторе
      this.$store.commit('neuro/setForwarded', {
        text:   this.newMessage,
        replyTo: this.replyTo,
        attachments: this.attachments
      });
      // перейдём в нейрочат
      this.$router.push({ name:'NeuroChat' });
    },
    editMessage(msg){if(msg.is_deleted)return; this.editingMessage=msg; this.newMessage=msg.text||''; this.replyTo=msg.reply_to?{...msg.reply_to}:null; this.attachments=msg.attachments.length?[...msg.attachments]:[]; this.$refs.input.focus()},
    scrollToBottom(){this.$nextTick(()=>{const el=this.$el.querySelector('.messages-list'); el.scrollTop=el.scrollHeight})}
  },

  mounted() {
    this.socket = io('http://localhost:8000', {
      path: '/socket.io',
      transports: ['websocket'],
      query: this.socketQuery
    });

    const isNeuroChat = this.socketQuery && this.socketQuery.neuroChat;
    const channel = isNeuroChat ? 'neuro-chat' : 'task';

    this.socket.on('connect', () => {
      console.log(`[DiscussionChat] Socket connected, SID: ${this.socket.id}, Channel: ${channel}`);
    });

    // Единый обработчик для создания сообщений
    this.socket.on(`${channel}:message-created`, (msg) => {
      if (isNeuroChat && msg.sender && msg.sender.email === 'ai@localhost') {
        msg.sender.name   = 'Нейрочат';
        msg.sender.avatar = this.iconPath;
      }
      console.log(`[DiscussionChat] Event "${channel}:message-created". Raw MSG:`, msg ? { ...msg } : msg);

      if (msg && msg.id && this.internalMessages) {
        if (!this.internalMessages.some(m => m.id === msg.id)) {
          console.log(`[DiscussionChat] New message id ${msg.id}. Processing...`);

          let finalMsg = { ...msg }; 

          if (isNeuroChat && finalMsg.sender && finalMsg.sender.email === 'ai@localhost') {
            console.log(`[DiscussionChat] AI message (id: ${finalMsg.id}) detected. Modifying sender info.`);
            finalMsg.sender = {
              ...(finalMsg.sender || {}), 
              name: 'Нейрочат',        
              avatar: this.iconPath      
            };
          }
          
          this.internalMessages.push(finalMsg);
          console.log(`[DiscussionChat] Message id ${finalMsg.id} pushed to internalMessages. New length: ${this.internalMessages.length}`);
          this.scrollToBottom();
        } else {
          console.log(`[DiscussionChat] Message id ${msg.id} already exists in internalMessages. Skipping.`);
        }
      } else {
        let errorReason = '';
        if (!msg) errorReason = 'Message object is null/undefined.';
        else if (!msg.id) errorReason = `Message ID is missing (id: ${msg.id}).`;
        else if (!this.internalMessages) errorReason = 'internalMessages is not available.';
        console.log(`[DiscussionChat] Invalid message received or prerequisites not met for "${channel}:message-created". Reason: ${errorReason} Raw MSG:`, msg ? { ...msg } : msg);
      }
    });

    this.socket.on(`${channel}:message-updated`, upd => {
      console.log(`[DiscussionChat] Event "${channel}:message-updated". Raw UPD:`, upd ? { ...upd } : upd);
      if (upd && upd.id && this.internalMessages) {
        const idx = this.internalMessages.findIndex(m => m.id === upd.id);
        if (idx !== -1) {
          const updatedMessage = { ...this.internalMessages[idx], ...upd };
           if (isNeuroChat && updatedMessage.sender && updatedMessage.sender.email === 'ai@localhost') {
            updatedMessage.sender.name = 'Нейрочат';
            updatedMessage.sender.avatar = this.iconPath;
          }
          this.$set(this.internalMessages, idx, updatedMessage);
          console.log(`[DiscussionChat] Message id ${upd.id} updated at index ${idx}.`);
        } else {
          console.log(`[DiscussionChat] Message id ${upd.id} for update not found in internalMessages.`);
        }
      }
    });

    this.socket.on(`${channel}:message-deleted`, d => {
      console.log(`[DiscussionChat] Event "${channel}:message-deleted". Raw D:`, d ? { ...d } : d);
      if (d && d.id && this.internalMessages) {
        this.internalMessages = this.internalMessages.filter(m => m.id !== d.id);
        console.log(`[DiscussionChat] Message id ${d.id} deleted.`);
      }
    });

    this.loadMessages().then(() => {
      this.scrollToBottom();
    });
  },

  beforeUnmount(){ if(this.socket) this.socket.disconnect() }
}
</script>

<style scoped>
/* Общие стили чата */
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%; /* Занимает всю доступную высоту родителя */
  background-color: #f4f7f9; /* Слегка отличающийся фон для области чата */
  border-radius: 8px;
  overflow: hidden;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
}

.messages-list {
  flex-grow: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

/* Стили для разделителя дат */
.date-divider {
  text-align: center;
  margin: 20px 0;
  color: #888;
  font-size: 0.85em;
}

/* Стили для одного сообщения */
.message-item {
  display: flex;
  margin-bottom: 15px;
  max-width: 75%; /* Сообщения не должны быть слишком широкими */
  align-items: flex-end; /* Выравнивание аватара и облачка сообщения по низу */
}

.message-item.own {
  align-self: flex-end;
  flex-direction: row-reverse; /* Аватар справа для своих сообщений */
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  margin: 0 10px;
  flex-shrink: 0;
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.message-content {
  background-color: #ffffff;
  padding: 10px 15px;
  border-radius: 18px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
  position: relative; /* Для "хвостика" */
}

.message-item.own .message-content {
  background-color: #e0f0ff; /* Светло-голубой для своих сообщений */
}

/* "Хвостики" для сообщений (псевдоэлементы) */
.message-content::before {
  content: '';
  position: absolute;
  bottom: 5px;
  width: 0;
  height: 0;
  border: 8px solid transparent;
}

.message-item:not(.own) .message-content::before {
  left: -10px; /* Хвостик слева */
  border-right-color: #ffffff;

}

.message-item.own .message-content::before {
  right: -10px; /* Хвостик справа */
  border-left-color: #e0f0ff;
}


.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.sender-name {
  font-weight: 600;
  font-size: 0.9em;
  color: #333;
}

.message-item.own .sender-name {
  /* Можно скрыть свое имя, если не нужно */
  /* display: none; */
}

.message-time {
  font-size: 0.75em;
  color: #777;
}

.edited-mark {
  font-size: 0.7em;
  color: #aaa;
  margin-left: 5px;
}

.message-body {
  font-size: 0.95em;
  line-height: 1.5;
  color: #2c3e50;
}

.message-body .text {
  white-space: pre-wrap; /* Сохраняем переносы строк */
  word-wrap: break-word; /* Перенос длинных слов */
}

.deleted-message {
  font-style: italic;
  color: #aaa;
  font-size: 0.9em;
}

/* Действия с сообщением (появляются при наведении) */
.message-actions {
  opacity: 0;
  transition: opacity 0.2s ease-in-out;
  margin-left: 5px; /* Небольшой отступ от контента сообщения */
  position: absolute; /* Позиционируем относительно .message-content или .message-item */
  right: 10px;
  bottom: -10px; /* Немного ниже сообщения */
  background: #fff;
  border-radius: 15px;
  padding: 2px 5px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  z-index: 10;
  display: flex;
}

.message-item:hover .message-actions {
  opacity: 1;
}
.message-item.own .message-actions {
    left: 10px;
    right: auto;
}


.message-actions button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 5px;
}

.action-icon {
  width: 16px;
  height: 16px;
  opacity: 0.7;
}

.message-actions button:hover .action-icon {
  opacity: 1;
}


/* Область ввода сообщения */
.chat-input-area {
  padding: 10px 15px;
  background-color: #ffffff;
  border-top: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column; 
  gap: 10px; 
}

.main-input-controls {
  display: flex;
  align-items: flex-end; /* Выравниваем по нижнему краю textarea и кнопок */
  width: 100%;
}

.chat-input-area textarea {
  flex-grow: 1;
  padding: 10px 15px; /* Немного уменьшил паддинг для лучшего вида с кнопками */
  border: 1px solid #dcdcdc;
  border-radius: 20px;
  resize: none;
  font-size: 0.95em;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  min-height: 22px; /* Соответствует line-height + padding */
  line-height: 1.4; /* Базовая высота строки */
  max-height: 120px; 
  overflow-y: auto;
  /* margin-right: 10px; - Удалено, теперь управление отступами через input-actions */
}

.chat-input-area textarea:focus {
  outline: none;
  border-color: #5a9bd4;
  box-shadow: 0 0 0 2px rgba(90, 155, 212, 0.2);
}

.input-actions {
  display: flex;
  align-items: center; /* Иконки выровнены по центру внутри своих кнопок */
  margin-left: 10px; /* Отступ слева от textarea */
  gap: 8px; /* Расстояние между кнопками "скрепка" и "отправить" */
}

/* Общий стиль для оберток кнопок-иконок в области ввода */
.action-button-wrapper {
  background: none;
  border: none;
  padding: 0; /* Убираем внутренний padding, так как SVG будет центрироваться */
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%; /* Круглая форма */
  width: 40px;  /* Фиксированная ширина */
  height: 40px; /* Фиксированная высота */
  transition: background-color 0.2s ease;
  box-sizing: border-box;
}

.action-button-wrapper:hover {
  background-color: #f0f0f0; /* Легкий фон при наведении */
}

.action-button-wrapper:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: transparent; /* Убираем фон при наведении для неактивной кнопки */
}

/* Стиль для SVG и IMG иконок внутри кнопок */
.action-button-wrapper .action-icon {
  width: 20px; /* Размер иконки */
  height: 20px;
  fill: currentColor; /* Позволяет SVG наследовать цвет текста, если нужно */
  color: #555; /* Основной цвет иконок, можно изменить */
  opacity: 0.7; /* Начальная прозрачность, как было для img */
}
.action-button-wrapper:hover .action-icon {
  opacity: 1;
  color: #333; /* Цвет иконки при наведении */
}
.action-button-wrapper:disabled .action-icon,
.action-button-wrapper:disabled:hover .action-icon {
  opacity: 0.5;
  color: #999; /* Цвет неактивной иконки */
}


/* Уведомления об ответе/редактировании */
.replying-to,
.editing-notice {
  padding: 8px 12px;
  background-color: #eef5ff;
  border-left: 3px solid #5b9cff;
  border-radius: 4px;
  font-size: 0.85em;
  color: #333;
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%; 
  box-sizing: border-box;
}

.reply-preview {
  display: flex;
  background-color: #f0f0f0;
  border-radius: 8px;
  padding: 6px 10px;
  margin-bottom: 8px;
  position: relative;
  overflow: hidden;
}

.reply-quote-bar {
  width: 4px;
  background-color: #5b9cff;  /* цвет «пимпочки» как в Telegram */
  border-radius: 2px;
  margin-right: 8px;
}

.reply-body {
  flex: 1;
}

.reply-sender {
  font-weight: 600;
  font-size: 0.85em;
  color: #0366d6;
  margin-bottom: 2px;
  display: block;
}

.reply-text {
  font-size: 0.9em;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
}

.replying-to .reply-to-label {
  margin-right: 8px;
  white-space: nowrap;
  flex-shrink: 0;
}

.replying-to .reply-to-text-preview {
  flex-grow: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 8px;
}

.replying-to .cancel-reply-button {
  background: none;
  border: none;
  color: #777;
  font-size: 1.2em;
  cursor: pointer;
  padding: 0 5px;
  flex-shrink: 0;
}

/* Отображение выбранных файлов для прикрепления */
.selected-files {
  padding: 5px 0; 
  width: 100%;
  box-sizing: border-box;
}
.file-item {
  display: inline-flex; /* Чтобы элементы были в строку и можно было управлять отступами */
  align-items: center;
  background-color: #e9ecef;
  padding: 5px 10px;
  border-radius: 15px; /* Скругленные плашки для файлов */
  font-size: 0.8em;
  margin-right: 8px;
  margin-bottom: 5px;
}
.file-name {
  margin-right: 8px;
  color: #495057;
}
.remove-file-btn {
  background: none;
  border: none;
  color: #6c757d;
  cursor: pointer;
  font-size: 1em;
  padding: 0;
  line-height: 1;
}
.remove-file-btn:hover {
  color: #343a40;
}

/* Стили для вложений в сообщениях */
.attachments {
  margin-top: 8px;
}
.attachment-item {
  display: flex;
  align-items: center;
  background-color: #f8f9fa;
  padding: 8px;
  border-radius: 8px;
  margin-bottom: 5px;
  border: 1px solid #e9ecef;
}
.attachment-preview {
  width: 40px;
  height: 40px;
  margin-right: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #e9ecef;
  border-radius: 6px;
  overflow: hidden; /* Обрезка превью, если оно больше контейнера */
}
.attachment-thumb {
  max-width: 100%;
  max-height: 100%;
  object-fit: cover; /* Масштабирование с сохранением пропорций и заполнением */
}
.file-icon {
  width: 24px; /* Размер иконки для обычных файлов */
  height: 24px;
}
.attachment-name {
  font-size: 0.85em;
  color: #007bff;
  text-decoration: none;
}
.attachment-name:hover {
  text-decoration: underline;
}

/* Адаптация для полосы прокрутки (Webkit) */
.messages-list::-webkit-scrollbar {
  width: 8px;
}

.messages-list::-webkit-scrollbar-track {
  background: #f4f7f9; /* Фон трека совпадает с фоном чата */
  border-radius: 4px;
}

.messages-list::-webkit-scrollbar-thumb {
  background: #cdd3d9; /* Цвет ползунка */
  border-radius: 4px;
}

.messages-list::-webkit-scrollbar-thumb:hover {
  background: #b8bfc6; /* Цвет ползунка при наведении */
}

.ai-thinking {
  display: flex;
  align-items: center;
  padding: 8px;
  background-color: transparent;
  border-radius: 8px;
  margin-bottom: 12px;
  margin-left: 12px;
}

.spinner-icon {
  width: 24px;
  height: 24px;
  margin-right: 8px;
  animation: spin 2s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.thinking-text {
  font-style: italic;
  color: #555;
}
</style>