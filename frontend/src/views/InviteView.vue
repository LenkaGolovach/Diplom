<template>
  <div class="invite-container">
    <div class="invite-content">
      <h2>Приглашение в доску: {{ board.name }}</h2>
      <p>Владелец: {{ board.owner.email }}</p>
      
      <div v-if="!isMember">
        <button @click="acceptInvite" class="accept-btn">Принять приглашение</button>
        <button @click="declineInvite" class="decline-btn">Отклонить</button>
      </div>
      
      <div v-else>
        <p>Вы уже являетесь участником этой доски</p>
        <router-link :to="`/boards/${board.id}`" class="link">
          Перейти к доске
        </router-link>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'; // Добавляем импорт axios

export default {
  data() {
    return {
      board: {},
      isMember: false
    }
  },
  async created() {
    await this.checkMembership()
  },
  methods: {
    async checkMembership() {
      try {
        const response = await axios.post(
          '/api/boards/join/',
          { token: this.$route.params.token },
          { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
        )
        this.isMember = true
        await this.fetchBoardData()
      } catch (error) {
        console.error('Ошибка:', error)
      }
    },
    async fetchBoardData() {
      try {
        const response = await axios.get('/api/boards/', {
          params: {
            invite_token: this.$route.params.token
          }
        })
        if (response.data.length > 0) {
          this.board = response.data[0]
        }
      } catch (error) {
        console.error('Ошибка загрузки доски:', error)
      }
    },
    async acceptInvite() {
      await this.checkMembership()
    },
    declineInvite() {
      this.$router.push('/boards')
    }
  }
}
</script>