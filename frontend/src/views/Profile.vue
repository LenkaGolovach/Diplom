<template>
  <div class="profile-page">
    <h1>Профиль пользователя</h1>
    
    <div v-if="loading" class="loading">
      Loading...
    </div>
    
    <div v-else class="profile-section">
      <div class="avatar-section">
        <img :src="avatarUrl" class="avatar" alt="Avatar">
        <button class="change-avatar-btn" @click="changeAvatar">
          Сменить аватар
        </button>
        <input type="file" hidden ref="avatarInput" @change="uploadAvatar" accept="image/*">
      </div>

      <div class="form-section">
        <div class="form-group">
          <label>Имя</label>
          <input v-model="userData.first_name" type="text">
        </div>

        <div class="form-group">
          <label>Фамилия</label>
          <input v-model="userData.last_name" type="text">
        </div>

        <div class="form-group">
          <label>Email</label>
          <input v-model="userData.email" type="email" readonly>
        </div>

        <button class="save-btn" @click="saveProfile" :disabled="saving">
          {{ saving ? 'Сохранение...' : 'Сохранить' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      userData: {
        first_name: '',
        last_name: '',
        email: '',
      },
      loading: true,
      saving: false
    }
  },
  computed: {
    avatarUrl() {
      const user = this.$store.state.user;
      if (!user || !user.avatar_url) {
        return 'https://www.gravatar.com/avatar/?d=identicon';
      }
      return user.avatar_url;
    }
  },
  async created() {
    await this.loadUserData();
  },
  methods: {
    async loadUserData() {
      this.loading = true;
      try {
        // Use the store's user data if available
        const storeUser = this.$store.state.user;
        if (storeUser) {
          this.userData = {
            first_name: storeUser.first_name || '',
            last_name: storeUser.last_name || '',
            email: storeUser.email || '',
          };
        } else {
          // Fetch from API if not in store
          await this.$store.dispatch('fetchUser');
          const user = this.$store.state.user;
          if (user) {
            this.userData = {
              first_name: user.first_name || '',
              last_name: user.last_name || '',
              email: user.email || '',
            };
          }
        }
      } catch (error) {
        console.error('Ошибка загрузки данных:', error);
      } finally {
        this.loading = false;
      }
    },
    changeAvatar() {
      this.$refs.avatarInput.click();
    },
    async uploadAvatar(e) {
      const file = e.target.files[0];
      if(!file) return;
      
      this.saving = true;
      const formData = new FormData();
      formData.append('avatar', file);
      
      try {
        await this.$store.dispatch('updateUser', formData);
        // Success notification
        alert('Аватар обновлен');
      } catch (error) {
        console.error('Ошибка загрузки аватара:', error);
        alert('Произошла ошибка при загрузке аватара');
      } finally {
        this.saving = false;
      }
    },
    async saveProfile() {
      this.saving = true;
      try {
        // Create FormData object to properly handle the request
        const formData = new FormData();
        formData.append('first_name', this.userData.first_name);
        formData.append('last_name', this.userData.last_name);
        
        await this.$store.dispatch('updateUser', formData);
        alert('Изменения сохранены');
      } catch (error) {
        console.error('Ошибка сохранения:', error);
        alert('Произошла ошибка при сохранении данных');
      } finally {
        this.saving = false;
      }
    }
  }
}
</script>

<style scoped>
.profile-page {
  max-width: 800px;
  margin: 20px auto;
  padding: 20px;
}

.loading {
  text-align: center;
  padding: 40px;
  font-size: 18px;
  color: #666;
}

.profile-section {
  display: flex;
  gap: 40px;
  margin-top: 30px;
}

.avatar-section {
  text-align: center;
}

.avatar {
  width: 150px;
  height: 150px;
  border-radius: 50%;
  margin-bottom: 15px;
  object-fit: cover;
  border: 1px solid #ddd;
}

.change-avatar-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.form-section {
  flex: 1;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.form-group input[readonly] {
  background-color: #f8f9fa;
  cursor: not-allowed;
}

.save-btn {
  background: #28a745;
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 20px;
}

.save-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .profile-section {
    flex-direction: column;
    gap: 20px;
  }
}
</style>