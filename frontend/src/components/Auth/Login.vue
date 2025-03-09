<template>
  <div class="auth-container">
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
        <input
          v-model="password"
          type="password"
          placeholder="Пароль"
          class="auth-input"
          required
        />
        <button type="submit" class="auth-button">Войти</button>
      </form>
      <p class="auth-link">
        Нет аккаунта? <router-link to="/register">Зарегистрироваться</router-link>
      </p>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex';
import axios from 'axios';

export default {
  data() {
    return {
      email: '',
      password: '',
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
    }
  }
};
</script>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: #f5f6f8;
}

.auth-card {
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  width: 300px;
}

.auth-title {
  font-size: 1.5em;
  font-weight: bold;
  margin-bottom: 16px;
  text-align: center;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.auth-input {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.auth-button {
  background: #0079bf;
  color: white;
  border: none;
  padding: 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.auth-button:hover {
  background: #026aa7;
}

.auth-link {
  text-align: center;
  margin-top: 12px;
  font-size: 14px;
}

.auth-link a {
  color: #0079bf;
  text-decoration: none;
}

.auth-link a:hover {
  text-decoration: underline;
}
</style>