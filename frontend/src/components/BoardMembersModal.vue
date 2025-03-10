<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <h2>Участники доски</h2>
      
      <div class="members-list">
        <div v-for="member in members" :key="member.email" class="member-item">
          <img :src="member.avatar || '/default-avatar.png'" class="avatar">
          <div class="member-info">
            <span>{{ member.email }}</span>
            <span class="role">{{ member.role }}</span>
          </div>
          <button 
            v-if="isOwner && member.email !== currentUser.email" 
            @click="removeMember(member)"
            class="remove-btn"
          >
            ×
          </button>
        </div>
      </div>

      <div class="invite-section">
        <button @click="generateInviteLink" class="invite-btn">
          Сгенерировать ссылку приглашения
        </button>
        <div v-if="inviteLink" class="invite-link">
          <input :value="inviteLink" readonly>
          <button @click="copyLink">Копировать</button>
        </div>
      </div>

      <button @click="$emit('close')" class="close-btn">Закрыть</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  props: {
    board: Object,
    currentUser: Object
  },
  data() {
    return {
      inviteLink: null
    };
  },
  computed: {
    members() {
      // Access members through the correct property based on the API response
      return this.board.members || [];
    },
    isOwner() {
      return this.currentUser && this.board.owner === this.currentUser.email;
    }
  },
  methods: {
    async generateInviteLink() {
      try {
        const response = await axios.post(
          `/api/boards/${this.board.id}/generate_invite/`,
          {},
          { 
            headers: { 
              Authorization: `Bearer ${localStorage.getItem('token')}` 
            } 
          }
        );
        this.inviteLink = response.data.invite_link;
      } catch (error) {
        console.error('Ошибка генерации ссылки:', error);
      }
    },
    async removeMember(member) {
      try {
        // Find the member ID from the board's members list
        const memberId = this.getMemberIdByEmail(member.email);
        if (!memberId) {
          console.error('Не удалось найти ID участника');
          return;
        }
        
        await axios.delete(
          `/api/boards/${this.board.id}/members/${memberId}/`,
          { 
            headers: { 
              Authorization: `Bearer ${localStorage.getItem('token')}` 
            } 
          }
        );
        this.$emit('update-members');
      } catch (error) {
        console.error('Ошибка удаления участника:', error);
      }
    },
    async getMemberIdByEmail(email) {
      try {
        const response = await axios.get(
          `/api/boards/${this.board.id}/members/get_by_email/`,
          {
            params: { email },
            headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
          }
        );
        return response.data.id;
      } catch (error) {
        console.error('Ошибка получения ID участника:', error);
        return null;
      }
    },
    copyLink() {
      navigator.clipboard.writeText(this.inviteLink)
        .then(() => {
          alert('Ссылка скопирована в буфер обмена');
        })
        .catch((err) => {
          console.error('Ошибка копирования:', err);
        });
    }
  }
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  position: relative;
}

.close-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 5px;
}

.member-item {
  display: flex;
  align-items: center;
  margin: 10px 0;
  padding: 10px;
  border-bottom: 1px solid #eee;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  margin-right: 15px;
}

.member-info {
  flex: 1;
}

.role {
  display: block;
  font-size: 0.8em;
  color: #666;
}

.remove-btn {
  background: none;
  border: none;
  color: #ff4444;
  font-size: 1.2em;
  cursor: pointer;
  padding: 5px;
}

.invite-section {
  margin-top: 20px;
}

.invite-btn {
  background: #0079bf;
  color: white;
  border: none;
  padding: 10px;
  border-radius: 4px;
  cursor: pointer;
}

.invite-link {
  margin-top: 10px;
  display: flex;
  gap: 10px;
}

.invite-link input {
  flex: 1;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}
</style>