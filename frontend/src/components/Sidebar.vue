<template>
  <div class="sidebar" :class="{ 'sidebar-open': isOpen }">
    <div class="sidebar-header">
      <h2>Меню</h2>
    </div>
    <div class="sidebar-content">
      <div class="user-info" v-if="currentUser">
        <img :src="currentUser.avatar" alt="Avatar" class="avatar" v-if="currentUser.avatar">
        <div class="user-details">
          <span class="user-name">{{ currentUser.first_name }} {{ currentUser.last_name }}</span>
          <span class="user-email">{{ currentUser.email }}</span>
        </div>
      </div>
      
      <div class="menu">
        <router-link to="/profile" class="menu-item">
          <span class="icon">👤</span> Профиль
        </router-link>
        <router-link to="/boards" class="menu-item">
          <span class="icon">📋</span> Доски
        </router-link>
        <router-link to="/search" class="menu-item">
          <span class="icon">🔍</span> Поиск задач
        </router-link>
        <router-link to="/neuro-chat" class="menu-item">
          <span class="icon">֎</span> Нейро-чат
        </router-link>
      </div>
      
      <button class="logout-btn" @click="logout">
        <span class="icon">🚪</span> Выйти
      </button>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

export default {
  name: 'Sidebar',
  props: {
    isOpen: {
      type: Boolean,
      required: true
    }
  },
  setup() {
    const store = useStore()
    const router = useRouter()
    const currentUser = computed(() => store.getters.currentUser)

    const logout = async () => {
      await store.dispatch('logout')
      router.push('/login')
    }

    return {
      currentUser,
      logout
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
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.sidebar-open {
  left: 0;
  box-shadow: 5px 0 30px rgba(0, 0, 0, 0.15);
}

.sidebar-header {
  margin-bottom: 20px;
  border-bottom: 1px solid rgba(221, 221, 221, 0.5);
  padding-bottom: 15px;
}

.sidebar-header h2 {
  margin: 0;
  font-size: 1.5em;
  color: #2c3e50;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  font-weight: 500;
}

.sidebar-content {
  display: flex;
  flex-direction: column;
  height: calc(100% - 60px);
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

.user-details {
  text-align: center;
  margin-bottom: 10px;
}

.user-name {
  font-weight: 600;
  font-size: 1.2em;
  margin-bottom: 5px;
  color: #2c3e50;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  letter-spacing: 0.3px;
  display: block;
}

.user-email {
  display: block;
  font-size: 0.9em;
  color: #666;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.menu {
  margin: 20px 0;
  flex-grow: 1;
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
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  font-size: 16px;
  font-weight: 500;
  letter-spacing: 0.3px;
}

.menu-item:hover {
  background: rgba(245, 245, 245, 0.8);
  transform: translateX(5px);
  color: #2c3e50;
}

.menu-item.router-link-exact-active,
.menu-item.router-link-active {
  background: rgba(91, 156, 255, 0.1);
  color: #5b9cff;
  font-weight: 600;
}

.icon {
  margin-right: 12px;
  font-size: 1.2em;
}

.logout-btn {
  margin-top: auto;
  padding: 14px;
  background: rgba(255, 123, 147, 0.1);
  color: #ff7b93;
  border: none;
  border-radius: 12px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
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