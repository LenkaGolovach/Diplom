<template>
  <div class="profile-page">
    <h1>Профиль пользователя</h1>
    
    <div class="profile-section">
      <div class="avatar-section">
        <img :src="user.avatar_url" class="avatar" alt="Avatar">
        <button class="change-avatar-btn" @click="changeAvatar">
          Сменить аватар
        </button>
        <input type="file" hidden ref="avatarInput" @change="uploadAvatar" accept="image/*">
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
        avatar: null,
        avatar_url: ''
      }
    }
  },
  async created() {
    await this.loadUserData();
  },
  methods: {
    async loadUserData() {
      try {
        const response = await axios.get('/api/users/me/', {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        });
        this.user = {
          ...response.data,
          avatar_url: response.data.avatar ? 
            `${axios.defaults.baseURL}${response.data.avatar}` : 
            'https://www.gravatar.com/avatar/?d=identicon'
        };
      } catch (error) {
        console.error('Ошибка загрузки данных:', error);
      }
    },
    changeAvatar() {
      this.$refs.avatarInput.click();
    },
    async uploadAvatar(e) {
      const file = e.target.files[0];
      if(file) {
        const formData = new FormData();
        formData.append('avatar', file);
        
        try {
          const response = await axios.patch('/api/users/me/', formData, {
            headers: {
              'Content-Type': 'multipart/form-data',
              Authorization: `Bearer ${localStorage.getItem('token')}`
            }
          });
          
          this.user.avatar_url = URL.createObjectURL(file);
          this.$store.commit('setUser', response.data);
        } catch (error) {
          console.error('Ошибка загрузки аватара:', error);
        }
      }
    },
    async saveProfile() {
      try {
        const response = await axios.patch('/api/users/me/', {
          first_name: this.user.first_name,
          last_name: this.user.last_name
        }, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        this.$store.commit('setUser', response.data);
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