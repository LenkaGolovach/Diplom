<template>
  <div class="profile-page">
    <h1>Профиль пользователя</h1>
    
    <div class="profile-section">
      <div class="avatar-section">
        <label for="avatar-upload" class="change-avatar-btn">
          Сменить аватар
        </label>
        <input 
          id="avatar-upload" 
          type="file" 
          hidden
          @change="uploadAvatar"
          accept="image/*"
        >
      </div>

      <div class="form-section">
        <div class="form-group">
          <label>Имя</label>
          <input v-model="user.first_name" type="text">
        </div>

        <div class="form-group">
          <label>Фамилия</label>
          <input v-model="user.last_name" type="text">
        </div>

        <button class="save-btn" @click="saveProfile">Сохранить</button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      user: {
        first_name: '',
        last_name: '',
      }
    }
  },
  computed: {
    avatarUrl() {
      if (this.$store.state.user && this.$store.state.user.avatar_url) {
        return this.$store.state.user.avatar_url;
      }
      return 'https://www.gravatar.com/avatar/?d=identicon';
    }
  },
  async created() {
    await this.loadUserData();
  },
  methods: {
    async loadUserData() {
      try {
        await this.$store.dispatch('fetchUser');
        this.user = {
          first_name: this.$store.state.user.first_name,
          last_name: this.$store.state.user.last_name
        };
      } catch (error) {
        console.error('Ошибка загрузки данных:', error);
      }
    },
    async uploadAvatar(e) {
      const file = e.target.files[0];
      if (file) {
        try {
          const formData = new FormData();
          formData.append('avatar', file);

          const response = await axios.patch('/api/users/me/', formData, {
            headers: {
              'Content-Type': 'multipart/form-data',
              Authorization: `Bearer ${localStorage.getItem('token')}`
            }
          });

          // Обновляем хранилище и локальное состояние
          this.$store.commit('setUser', response.data);
          
          // Принудительно обновляем URL аватара
          this.user.avatar_url = response.data.avatar_url + `?t=${Date.now()}`;

        } catch (error) {
          console.error('Ошибка загрузки аватара:', error);
          alert('Ошибка при обновлении аватара');
        }
      }
    },
    async saveProfile() {
      try {
        await this.$store.dispatch('updateUser', {
          first_name: this.user.first_name,
          last_name: this.user.last_name
        });
        alert('Изменения сохранены');
      } catch (error) {
        console.error('Ошибка сохранения:', error);
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
}

.change-avatar-btn {
  display: inline-block;
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
}

.form-group input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
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
</style>