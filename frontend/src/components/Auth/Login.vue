<template>
  <div class="auth-container" :style="{ backgroundImage: 'url(' + backgroundImage + ')' }">
    <div class="auth-card">
      <h2 class="auth-title">Вход</h2>
      <form @submit.prevent="handleLogin" class="auth-form">
        <input
          v-model="email"
          type="email"
          placeholder="Email"
          class="auth-input"
          required
        />
        <div class="password-container">
          <input
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            placeholder="Пароль"
            class="auth-input"
            required
          />
          <button type="button" @click="togglePassword" class="toggle-password">
            {{ showPassword ? 'Скрыть' : 'Показать' }}
          </button>
        </div>
        <button type="submit" class="auth-button">Войти</button>
      </form>
      <div class="auth-link">
        <span>Нет аккаунта?</span><router-link to="/register">Зарегистрироваться</router-link>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex';
import axios from 'axios';
import backgroundImage from '@/assets/background.jpg';

export default {
  data() {
    return {
      email: '',
      password: '',
      showPassword: false,
      backgroundImage: backgroundImage,
    };
  },
  methods: {
    ...mapActions(['login']),
    async handleLogin() {
      try {
        await this.$store.dispatch('login', {
          email: this.email,
          password: this.password
        });
        
        this.$router.push('/boards');
      } catch (error) {
          console.error('Login error details:', error);
          
          // Добавьте проверку на существование response
          let errorMessage = 'Произошла неизвестная ошибка';
          
          if (error.response) {
              // Ошибка с ответом от сервера
              if (error.response.status === 401) {
                  errorMessage = 'Неверный email или пароль';
              } else {
                  errorMessage = `Ошибка сервера: ${error.response.status}`;
              }
          } else if (error.request) {
              // Запрос был сделан, но ответ не получен
              errorMessage = 'Сервер не отвечает';
          } else {
              // Ошибка в настройке запроса
              errorMessage = 'Ошибка в отправке запроса';
          }
          
          alert(errorMessage);
      }
    },
    togglePassword() {
      this.showPassword = !this.showPassword;
    },
  }
};
</script>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  width: 100vw;
  margin: 0;
  padding: 0;
  position: fixed;
  top: 0;
  left: 0;
  background-repeat: no-repeat;
  background-position: center center;
  background-size: cover;
  background-attachment: fixed;
}

.auth-card {
  background: rgba(255, 255, 255, 0.9);
  padding: 45px;
  border-radius: 12px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
  width: 350px;
  z-index: 10;
}

.auth-title {
  font-size: 1.8em;
  font-weight: bold;
  margin-bottom: 20px;
  text-align: center;
  font-family: 'Arial', sans-serif;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.auth-input {
  padding: 12px;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 16px;
  transition: border-color 0.3s;
}

.auth-input:focus {
  border-color: #5a9bd4;
}

.password-container {
  position: relative;
}

.password-container .auth-input {
  padding-right: 142px;
}

.toggle-password {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #5a9bd4;
  cursor: pointer;
  font-size: 14px;
}

.auth-button {
  background: #5a9bd4;
  color: white;
  border: none;
  padding: 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  transition: background 0.3s;
}

.auth-button:hover {
  background: #4a8bc4;
}

.auth-link {
  text-align: center;
  margin-top: 20px;
  font-size: 15px;
  font-family: 'Roboto', 'Arial', sans-serif;
  color: #5d6778;
}

.auth-link a {
  color: #4a8bc4;
  text-decoration: none;
  font-weight: 600;
  margin-left: 5px;
  transition: color 0.3s ease;
}

.auth-link a:hover {
  color: #3a6fa3;
  text-decoration: none;
  border-bottom: 1px solid #3a6fa3;
}
</style>