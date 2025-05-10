<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <h2 class="modal-title">Участники доски</h2>
      
      <div class="members-list">
        <div v-for="member in members" :key="member.email" class="member-item">
          <div class="avatar-wrapper">
            <img :src="member.avatar || '/default-avatar.png'" class="avatar">
          </div>
          <div class="member-info">
            <span class="member-email">{{ member.email }}</span>
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
          <span class="btn-icon">🔗</span> Сгенерировать ссылку приглашения
        </button>
        <div v-if="inviteLink" class="invite-link">
          <input :value="inviteLink" readonly class="invite-input">
          <button @click="copyLink" class="copy-btn">Копировать</button>
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
        return this.currentUser 
            && this.board.owner 
            && this.board.owner.email === this.currentUser.email;
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
  },
  mounted() {
    document.body.style.overflow = 'hidden';
  },
  beforeDestroy() {
    document.body.style.overflow = 'auto';
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
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1001;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideIn {
  from { transform: translateY(-20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.modal-content {
  background: rgba(255, 255, 255, 0.9);
  padding: 35px 30px;
  border-radius: 12px;
  max-width: 550px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  position: relative;
  z-index: 1002;
  animation: slideIn 0.3s ease;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.4);
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.1) transparent;
}

.modal-content::-webkit-scrollbar {
  width: 5px;
}

.modal-content::-webkit-scrollbar-track {
  background: transparent;
}

.modal-content::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 10px;
}

.modal-title {
  font-size: 1.8em;
  font-weight: bold;
  margin-bottom: 25px;
  text-align: center;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  color: #2c3e50;
  letter-spacing: 0.3px;
}

.close-btn {
  position: absolute;
  top: 15px;
  right: 15px;
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 8px 15px;
  border-radius: 8px;
  color: #4a5568;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  transform: translateY(-2px);
}

.members-list {
  margin-bottom: 30px;
  max-height: 300px;
  overflow-y: auto;
  padding: 5px;
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.1) transparent;
}

.members-list::-webkit-scrollbar {
  width: 5px;
}

.members-list::-webkit-scrollbar-track {
  background: transparent;
}

.members-list::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 10px;
}

.member-item {
  display: flex;
  align-items: center;
  margin: 10px 0;
  padding: 15px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.7);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.member-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.avatar-wrapper {
  margin-right: 15px;
  position: relative;
}

.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.member-item:hover .avatar {
  transform: scale(1.05);
}

.member-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.member-email {
  font-weight: 600;
  color: #2c3e50;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  font-size: 15px;
  letter-spacing: 0.2px;
}

.role {
  display: block;
  font-size: 0.85em;
  color: #7f8c8d;
  margin-top: 3px;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
}

.remove-btn {
  background: none;
  border: none;
  color: #bdc3c7;
  font-size: 22px;
  cursor: pointer;
  padding: 4px;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.remove-btn:hover {
  background: rgba(231, 76, 60, 0.1);
  color: #e74c3c;
  transform: rotate(90deg);
}

.invite-section {
  margin-top: 25px;
  padding-top: 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  animation: fadeIn 0.5s ease;
}

.invite-btn {
  background: #5b9cff;
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(91, 156, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  letter-spacing: 0.3px;
}

.btn-icon {
  margin-right: 8px;
  font-size: 18px;
}

.invite-btn:hover {
  background: #4a8bff;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(91, 156, 255, 0.4);
}

.invite-link {
  margin-top: 15px;
  display: flex;
  gap: 10px;
  animation: fadeIn 0.4s ease;
}

.invite-input {
  flex: 1;
  padding: 12px 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  font-size: 14px;
  background: rgba(255, 255, 255, 0.8);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.02);
  transition: all 0.3s ease;
}

.copy-btn {
  background: #f0f0f0;
  color: #4a5568;
  padding: 12px 15px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  transition: all 0.3s ease;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}

.copy-btn:hover {
  background: #e0e0e0;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.07);
}

@media (max-width: 768px) {
  .modal-content {
    width: 95%;
    padding: 25px 20px;
  }
  
  .member-item {
    padding: 12px;
  }
  
  .avatar {
    width: 40px;
    height: 40px;
  }
  
  .invite-link {
    flex-direction: column;
  }
  
  .modal-title {
    font-size: 1.5em;
  }
}
</style>