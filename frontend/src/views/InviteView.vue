<template>
  <div class="invite-view">
    <div class="invite-card">
      <h2 class="invite-title">Приглашение в доску</h2>
      
      <div v-if="board" class="board-info">
        <h3 class="board-name">{{ board.name }}</h3>
        <p v-if="board.owner" class="board-owner">
          Владелец: <span class="owner-email">{{ board.owner.email }}</span>
        </p>
      </div>

      <div v-if="isLoading" class="loading-spinner">
        <div class="spinner"></div>
      </div>

      <div v-else>
        <div v-if="!isMember" class="invite-actions">
          <button @click="acceptInvite" class="btn-accept">
            Принять приглашение
          </button>
          <button @click="declineInvite" class="btn-decline">
            Отклонить
          </button>
        </div>

        <div v-else class="already-member">
          <p>Вы уже являетесь участником этой доски</p>
          <router-link :to="`/boards/${board.id}`" class="btn-go-to-board">
            Перейти к доске
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      board: null,
      isMember: false,
      isLoading: true
    }
  },
  async created() {
    await this.checkInviteValidity();
  },
  methods: {
    async checkInviteValidity() {
      try {
        const response = await axios.get(`/api/boards/check_invite/?token=${this.$route.params.token}`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        this.board = response.data.board;
        this.isMember = response.data.is_member;
        this.isLoading = false;

      } catch (error) {
        if (error.response && error.response.status === 404) {
          alert('Ссылка приглашения недействительна или устарела');
          this.$router.push('/boards');
        } else {
          console.error('Ошибка:', error);
        }
      }
    },

    async acceptInvite() {
      try {
        const response = await axios.post(
          '/api/boards/join/',
          { token: this.$route.params.token },
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('token')}`
            }
          }
        );

        if (response.data.success) {
          this.isMember = true;
          alert('Вы успешно присоединились к доске!');
          this.$router.push(`/boards/${this.board.id}`);
        }
      } catch (error) {
        console.error('Ошибка присоединения:', error);
      }
    },

    declineInvite() {
      this.$router.push('/boards');
    }
  }
}
</script>

<style scoped>
.invite-view {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f6f8;
  padding: 20px;
}

.invite-card {
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 32px;
  max-width: 500px;
  width: 100%;
  text-align: center;
}

.invite-title {
  font-size: 24px;
  font-weight: 600;
  color: #172b4d;
  margin-bottom: 24px;
}

.board-info {
  margin-bottom: 24px;
}

.board-name {
  font-size: 20px;
  font-weight: 500;
  color: #172b4d;
  margin-bottom: 8px;
}

.board-owner {
  font-size: 14px;
  color: #5e6c84;
}

.owner-email {
  font-weight: 500;
  color: #0079bf;
}

.invite-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 24px;
}

.btn-accept,
.btn-decline,
.btn-go-to-board {
  padding: 10px 20px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.btn-accept {
  background-color: #0079bf;
  color: #ffffff;
  border: none;
}

.btn-accept:hover {
  background-color: #026aa7;
}

.btn-decline {
  background-color: #eb5a46;
  color: #ffffff;
  border: none;
}

.btn-decline:hover {
  background-color: #cf513d;
}

.btn-go-to-board {
  background-color: #61bd4f;
  color: #ffffff;
  border: none;
  text-decoration: none;
}

.btn-go-to-board:hover {
  background-color: #5aac44;
}

.already-member {
  margin-top: 24px;
}

.already-member p {
  font-size: 16px;
  color: #5e6c84;
  margin-bottom: 16px;
}

.loading-spinner {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #0079bf;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>