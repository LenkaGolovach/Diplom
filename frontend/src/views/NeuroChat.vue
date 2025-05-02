<!-- src/views/NeuroChat.vue -->
<template>
  <div class="page-wrapper">
    <div class="inner-container">
      <DiscussionChat class="discussion-chat"
        :fetch-messages="fetchMessages"
        :send-message="sendMessage"
        :messages="messages"
        :current-user="currentUser"
        :socket-query="{ neuroChat: true }"
        :icon-path="aiAvatar"
        :ai-thinking="aiThinking"
      />
    </div>
  </div>
</template>

<script>
import { ref, watch } from 'vue'
import { useStore } from 'vuex'
import axios from 'axios'
import { io } from 'socket.io-client'
import DiscussionChat from '@/components/DiscussionChat.vue'

export default {
  name: 'NeuroChat',
  components: { DiscussionChat },
  setup() {
    const store = useStore()
    const messages = ref([])
    const aiThinking = ref(false)
    const aiAvatar = '/icons/ai-avatar.png'
    const currentUser = ref(store.state.user)

    const socket = io('http://localhost:8000', {
      transports: ['websocket'],
      query: { neuroChat: true }
    })

    async function fetchMessages() {
      const { data } = await axios.get('/api/neuro-chat/', {
        headers: { 
          Authorization: `Bearer ${localStorage.getItem('token')}` // Исправлено
        }
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
          await axios.delete(`/api/neuro-chat/${messageId}/`, { // Исправлено
            headers: { 
              Authorization: `Bearer ${localStorage.getItem('token')}` // Исправлено
            }
          })
        } else {
          const { data } = await axios.post('/api/neuro-chat/', form, {
            headers: { 
              Authorization: `Bearer ${localStorage.getItem('token')}` // Исправлено
            }
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
          const last = messages.value[messages.value.length - 1]
          if (last.sender.email === 'ai@localhost') {
            aiThinking.value = false
          }
        }
      }
    )

    return {
      fetchMessages,
      sendMessage,
      messages,
      currentUser,
      aiAvatar,
      aiThinking
    }
  }
}
</script>

<style>
.page-wrapper {
  display: flex;
  justify-content: center;
  height: 100vh;
}
.inner-container {
  width: 100%;
  max-width: 1200px;  /* whatever limit you like */
  display: flex;
  flex-direction: column;
}
.discussion-chat {
  flex: 1;            /* fill remaining vertical space */
}
</style>