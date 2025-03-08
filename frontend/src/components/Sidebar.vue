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
        <span class="icon">📋</span> Доски
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
  left: -270px;
  top: 0;
  bottom: 0;
  width: 250px;
  background: #fff;
  box-shadow: 2px 0 8px rgba(0,0,0,0.1);
  transition: 0.3s;
  padding: 20px;
  z-index: 1000;
}

.sidebar-open {
  left: 0;
}

.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  margin-bottom: 15px;
  object-fit: cover;
}

.user-name {
  font-weight: 500;
  margin-bottom: 20px;
}

.menu-item {
  display: block;
  padding: 12px;
  color: #333;
  text-decoration: none;
  border-radius: 4px;
  margin: 20px 0;
  transition: background 0.2s;
}

.menu-item:hover {
  background: #f5f5f5;
}

.menu-item.router-link-exact-active {
  background: #e3f2fd;
  color: #1976d2;
}

.icon {
  margin-right: 10px;
}

.logout-btn {
  position: absolute;
  bottom: 20px;
  width: calc(100% - 40px);
  left: 20px;
  right: 20px;
  padding: 12px;
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.logout-btn:hover {
  background: #e9ecef;
}
</style>