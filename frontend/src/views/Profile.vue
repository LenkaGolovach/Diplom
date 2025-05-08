<template>
  <div class="profile-page">
    <div class="profile-container">
      <h1 class="profile-title">Профиль пользователя</h1>
      
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <span>Загрузка данных...</span>
      </div>
      
      <div v-else class="profile-section">
        <div class="avatar-section">
          <div class="avatar-container">
            <img :src="avatarUrl" class="avatar" alt="Avatar">
          </div>
          <button class="change-avatar-btn" @click="changeAvatar">
            <span class="btn-icon">📷</span> Сменить аватар
          </button>
          <input type="file" hidden ref="avatarInput" @change="uploadAvatar" accept="image/*">
        </div>

        <div class="form-section">
          <div class="form-group">
            <label>Имя</label>
            <input v-model="userData.first_name" type="text" placeholder="Введите имя">
          </div>

          <div class="form-group">
            <label>Фамилия</label>
            <input v-model="userData.last_name" type="text" placeholder="Введите фамилию">
          </div>

          <div class="form-group">
            <label>Email</label>
            <input v-model="userData.email" type="email" readonly>
          </div>

          <button class="save-btn" @click="saveProfile" :disabled="saving">
            <span class="btn-icon">💾</span> {{ saving ? 'Сохранение...' : 'Сохранить' }}
          </button>
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
        // Always fetch fresh user data from the API
        await this.$store.dispatch('fetchUser');
        const user = this.$store.state.user;
        
        if (user) {
          this.userData = {
            first_name: user.first_name || '',
            last_name: user.last_name || '',
            email: user.email || '',
          };
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
      
      // Проверяем размер файла (ограничение 5MB)
      if (file.size > 5 * 1024 * 1024) {
        alert('Размер файла не должен превышать 5MB');
        this.saving = false;
        return;
      }

      // Проверяем тип файла
      const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml'];
      if (!allowedTypes.includes(file.type)) {
        alert('Пожалуйста, загрузите изображение (JPEG, PNG, GIF, WEBP или SVG)');
        this.saving = false;
        return;
      }

      try {
        console.log('Загрузка файла:', file.name, 'тип:', file.type, 'размер:', file.size);
        
        // Вернемся к использованию axios, с правильными настройками
        const formData = new FormData();
        formData.append('avatar', file);
        
        const token = localStorage.getItem('token');
        
        // Используем axios без установки Content-Type - он сам определит правильный для FormData
        const response = await axios.patch('/api/users/me/', formData, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        console.log('Ответ сервера:', response);
        
        // Перезагружаем пользователя из API
        await this.$store.dispatch('fetchUser');
        
        // Обновляем локальные данные
        await this.loadUserData();
        
        // Показываем успешное уведомление
        alert('Аватар успешно обновлен');
      } catch (error) {
        // Выводим более полную информацию об ошибке для отладки
        console.error('Ошибка загрузки аватара:', error);
        
        let errorMessage = 'Произошла ошибка при загрузке аватара';
        
        if (error.response) {
          // Если ответ от сервера содержит данные
          console.error('Статус ответа:', error.response.status);
          console.error('Заголовки ответа:', error.response.headers);
          
          // Попробуем получить текст ошибки
          try {
            if (error.response.data) {
              if (typeof error.response.data === 'object') {
                errorMessage = JSON.stringify(error.response.data);
              } else {
                errorMessage = String(error.response.data).substring(0, 100); // Ограничиваем длину
              }
            }
          } catch (e) {
            console.error('Ошибка при обработке данных ответа:', e);
          }
        } else if (error.request) {
          errorMessage = 'Сервер не ответил на запрос';
        } else {
          errorMessage = `Ошибка: ${error.message}`;
        }
        
        alert(errorMessage);
      } finally {
        this.saving = false;
        // Очищаем значение input[type=file] для возможности повторной загрузки того же файла
        this.$refs.avatarInput.value = '';
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
  min-height: 100vh;
  width: 100%;
  padding: 40px 20px;
  background: linear-gradient(135deg, 
    #ffffff 0%,
    #fff5f5 25%,
    #f8f7ff 50%,
    #fff5f5 75%,
    #ffffff 100%
  );
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow-y: auto;
}

.profile-container {
  max-width: 900px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 16px;
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  padding: 40px;
  animation: fadeIn 0.5s ease;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.profile-title {
  font-size: 2.5em;
  color: #2c3e50;
  margin: 0 0 30px 0;
  font-weight: 600;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  letter-spacing: 0.5px;
  text-align: center;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 50px;
  font-size: 18px;
  color: #5e6c84;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(91, 156, 255, 0.2);
  border-left-color: #5b9cff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.profile-section {
  display: flex;
  gap: 60px;
  margin-top: 20px;
  animation: slideUp 0.6s ease;
  justify-content: center;
  flex-wrap: wrap;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 200px;
  max-width: 220px;
}

.avatar-container {
  position: relative;
  width: 180px;
  height: 180px;
  border-radius: 50%;
  margin-bottom: 25px;
  overflow: hidden;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
  border: 4px solid white;
  transition: all 0.3s ease;
}

.avatar-container:hover {
  transform: scale(1.05);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: all 0.3s ease;
}

.change-avatar-btn {
  background: #5b9cff;
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 500;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 15px rgba(91, 156, 255, 0.3);
  margin-bottom: 15px;
}

.change-avatar-btn:hover {
  background: #4a8bff;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(91, 156, 255, 0.4);
}

.btn-icon {
  margin-right: 8px;
  font-size: 18px;
}

.form-section {
  flex: 1;
  padding: 25px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  min-width: 280px;
  max-width: 500px;
}

.form-group {
  margin-bottom: 25px;
  margin-right: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #2c3e50;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  font-size: 16px;
  letter-spacing: 0.3px;
}

.form-group input {
  width: 100%;
  padding: 15px;
  border: 1px solid #ccc;
  border-radius: 8px;
  font-size: 16px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  transition: all 0.3s ease;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.03);
}

.form-group input:focus {
  border-color: #5a9bd4;
  box-shadow: 0 0 0 3px rgba(90, 155, 212, 0.2);
  outline: none;
}

.form-group input[readonly] {
  background-color: #f8f9fa;
  cursor: not-allowed;
  color: #6c757d;
}

.save-btn {
  background: #27ae60;
  color: white;
  padding: 14px 28px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  margin-top: 30px;
  font-size: 16px;
  font-weight: 500;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 15px rgba(39, 174, 96, 0.3);
  letter-spacing: 0.3px;
}

.save-btn:hover {
  background: #219653;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(39, 174, 96, 0.4);
}

.save-btn:disabled {
  background: #a0aec0;
  transform: none;
  box-shadow: none;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .profile-container {
    padding: 30px 20px;
  }
  
  .profile-title {
    font-size: 2em;
  }
  
  .profile-section {
    flex-direction: column;
    gap: 30px;
    align-items: center;
  }
  
  .avatar-section {
    min-width: auto;
    max-width: 100%;
  }
  
  .form-section {
    min-width: 100%;
  }
  
  .avatar-container {
    width: 150px;
    height: 150px;
  }
}
</style>