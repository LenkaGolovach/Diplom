<template>
  <div class="sidebar" :class="{ 'sidebar-open': isOpen }">
    <div class="user-info" v-if="user">
      <img :src="avatarUrl" class="avatar" alt="Avatar">
      <div class="user-name">{{ fullName }}</div>
    </div>
    
    <nav class="menu">
      <router-link to="/profile" class="menu-item">
        <span class="icon">👤</span> Профиль
      </router-link>
      <router-link to="/boards" class="menu-item">
        <span class="icon">📋</span> Проекты
      </router-link>
      <router-link to="/neuro-chat" class="menu-item">
        <span class="icon">֎</span> Нейро-чат
      </router-link>
    </nav>

    <button class="logout-btn" @click="logout">
      <span class="icon">🚪</span> Выйти
    </button>
  </div>
</template>

<script>
export default {
  computed: {
    user() {
      return this.$store.state.user;
    },
    fullName() {
      if (!this.user) return '';
      return [this.user.first_name, this.user.last_name].filter(Boolean).join(' ') || this.user.email;
    },
    avatarUrl() {
      if (!this.user) return 'https://www.gravatar.com/avatar/?d=identicon';
      return this.user.avatar_url || 'https://www.gravatar.com/avatar/?d=identicon';
    }
  },
  props: {
    isOpen: Boolean,
  },
  methods: {
    logout() {
      this.$store.dispatch('logout');
      this.$router.push('/login');
    }
  }
}
</script>

<style scoped>
.sidebar {
  position: fixed;
  left: -280px;
  top: 0;
  bottom: 0;
  width: 260px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 0 25px rgba(0, 0, 0, 0.1);
  transition: all 0.4s cubic-bezier(0.25, 1, 0.5, 1);
  padding: 30px 20px;
  z-index: 1000;
  border-right: 1px solid rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.sidebar-open {
  left: 0;
  box-shadow: 5px 0 30px rgba(0, 0, 0, 0.15);
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.avatar {
  width: 90px;
  height: 90px;
  border-radius: 50%;
  margin-bottom: 15px;
  object-fit: cover;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  border: 3px solid white;
  transition: transform 0.3s ease;
}

.avatar:hover {
  transform: scale(1.05);
}

.user-name {
  font-weight: 600;
  font-size: 1.2em;
  margin-bottom: 5px;
  color: #2c3e50;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  letter-spacing: 0.3px;
}

.menu {
  margin: 20px 0;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  color: #4a5568;
  text-decoration: none;
  border-radius: 12px;
  margin: 10px 0;
  transition: all 0.3s ease;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  font-size: 16px;
  font-weight: 500;
  letter-spacing: 0.3px;
}

.menu-item:hover {
  background: rgba(245, 245, 245, 0.8);
  transform: translateX(5px);
  color: #2c3e50;
}

.menu-item.router-link-exact-active {
  background: rgba(91, 156, 255, 0.1);
  color: #5b9cff;
  font-weight: 600;
}

.icon {
  margin-right: 12px;
  font-size: 1.2em;
}

.logout-btn {
  position: absolute;
  bottom: 30px;
  width: calc(100% - 40px);
  left: 20px;
  right: 20px;
  padding: 14px;
  background: rgba(255, 123, 147, 0.1);
  color: #ff7b93;
  border: none;
  border-radius: 12px;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  font-size: 16px;
  font-weight: 500;
  letter-spacing: 0.3px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 5px rgba(255, 123, 147, 0.1);
}

.logout-btn:hover {
  background: rgba(255, 123, 147, 0.2);
  transform: translateY(-2px);
  box-shadow: 0 4px 10px rgba(255, 123, 147, 0.2);
}

.logout-btn .icon {
  margin-right: 10px;
}
</style>