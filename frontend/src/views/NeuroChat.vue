<template>
  <div class="page-wrapper">
    <div class="inner-container">
      <!-- DiscussionChat с рефом для доступа к методам -->
      <DiscussionChat
        v-if="sessionId"
        ref="discussion"
        :key="sessionId"
        class="discussion-chat"
        :fetch-messages="fetchMessages"
        :send-message="sendMessage"
        :messages="messages"
        :current-user="currentUser"
        :socket-query="{ neuroChat: true, session: sessionId }"
        :icon-path="aiAvatar"
        :ai-thinking="aiThinking"
        @forward-to-neuro="handleForwardToNeuro"
      />
    </div>
  </div>
</template>

<script>
import { ref, watch, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { io } from 'socket.io-client'
import DiscussionChat from '@/components/DiscussionChat.vue'

export default {
  name: 'NeuroChat',
  components: { DiscussionChat },
  setup() {
    const store = useStore()
    const sessionId = ref(null)
    const messages = ref([])
    const aiThinking = ref(false)
    const aiAvatar = '/icons/ai-avatar.png'
    const currentUser = ref(store.state.user)

    // Реф на DiscussionChat
    const discussion = ref(null)

    // Для чтения query-параметров
    const route = useRoute()
    const router = useRouter()

    const socket = io('http://localhost:8000', {
      transports: ['websocket'],
      autoConnect: false,
      query: { neuroChat: true, session: null }
    })

    onMounted(async () => {
      // Получаем или создаем сессию
      const { data } = await axios.get('/api/neuro-chat/session/');
      sessionId.value = data.session_id;
      socket.io.opts.query.session = sessionId.value;

      socket.on('neuro-chat:message-created', msg => {
        if (!messages.value.find(m => m.id === msg.id)) {
          messages.value.push(msg);
        }
      });
      socket.connect();

      await fetchMessages();

      // Обработка пересылаемого текста из query
      const fwd = route.query.forwardedText;
      if (fwd && discussion.value && discussion.value.startReply) {
        discussion.value.startReply({ id: null, text: String(fwd), sender: currentUser.value });
      }

      // Обработка вложений, сохранённых в сторе
      const forwarded = store.state.neuro.forwarded;
      if (forwarded && discussion.value) {
        if (forwarded.attachments && forwarded.attachments.length) {
          discussion.value.attachments = forwarded.attachments;
        }
        if (forwarded.replyTo) {
          discussion.value.replyTo = forwarded.replyTo;
        }
        if (forwarded.text) {
          discussion.value.newMessage = forwarded.text;
        }

        // Очистка после переноса
        store.commit('neuro/clearForwarded');
      }
    })


    async function fetchMessages() {
      const { data } = await axios.get('/api/neuro-chat/', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      })
      messages.value = data.map(m => {
        if (m.sender.email === 'ai@localhost') {
          m.sender.avatar = aiAvatar
          m.sender.name = 'Нейрочат'
        }
        return m
      })
    }

    async function sendMessage(messageId, form, action) {
      aiThinking.value = true
      try {
        if (action === 'delete') {
          await axios.delete(`/api/neuro-chat/${messageId}/`, {
            headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
          })
        } else {
          // Добавляем session_id в FormData, если он есть
          if (sessionId.value) {
            form.append('session_id', sessionId.value);
          }

          const { data } = await axios.post('/api/neuro-chat/', form, {
            headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
          })
          socket.emit('neuro-chat:message-created', data)
          return data
        }
      } catch (err) {
        console.error('NeuroChat.sendMessage error', err)
        throw err
      }
    }

    watch(
      () => messages.value.length,
      (newLen, oldLen) => {
        if (aiThinking.value && newLen > oldLen) {
          const last = messages.value[newLen - 1]
          if (last.sender.email === 'ai@localhost') aiThinking.value = false
        }
      }
    )

    function handleForwardToNeuro(message) {
      // Навигируем в тот же маршрут, но с query-параметром
      router.push({ name: 'NeuroChat', query: { forwardedText: message.text || '' } })
    }

    return {
      sessionId,
      messages,
      aiThinking,
      aiAvatar,
      currentUser,
      fetchMessages,
      sendMessage,
      discussion,
      handleForwardToNeuro
    }
  }
}
</script>

<style>
.page-wrapper {
  display: flex;
  justify-content: center;
  height: 100vh; 
  background-color: #eef2f5; 
  padding: 20px; 
  box-sizing: border-box;
}
.inner-container {
  width: 100%;
  max-width: 1000px;  
  display: flex;
  flex-direction: column;
  flex-grow: 1; 
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08); 
  border-radius: 12px; 
  overflow: hidden; 
}

/* Styles for the <DiscussionChat> component instance itself */
.discussion-chat {
  flex: 1;
  display: flex; 
  flex-direction: column;
  overflow: hidden; 
}
</style>