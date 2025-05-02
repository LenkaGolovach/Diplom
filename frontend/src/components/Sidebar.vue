<template>
  <div class="sidebar" :class="{ 'sidebar-open': isOpen }">
    <div class="sidebar-header">
      <h2>Меню</h2>
    </div>
    <div class="sidebar-content">
      <router-link to="/boards" class="sidebar-item">
        <span>Доски</span>
      </router-link>
      <router-link to="/search" class="sidebar-item">
        <span>Поиск задач</span>
      </router-link>
      <div class="user-info" v-if="currentUser">
        <img :src="currentUser.avatar" alt="Avatar" class="avatar" v-if="currentUser.avatar">
        <div class="user-details">
          <span class="user-name">{{ currentUser.first_name }} {{ currentUser.last_name }}</span>
          <span class="user-email">{{ currentUser.email }}</span>
        </div>
        <button @click="logout" class="logout-button">Выйти</button>
      </div>
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
  top: 0;
  left: -250px;
  width: 250px;
  height: 100vh;
  background-color: #f5f5f5;
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
  transition: 0.3s;
  z-index: 1000;
}

.sidebar-open {
  left: 0;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #ddd;
}

.sidebar-header h2 {
  margin: 0;
  font-size: 1.5em;
}

.sidebar-content {
  padding: 20px;
}

.sidebar-item {
  display: block;
  padding: 10px;
  color: #333;
  text-decoration: none;
  border-radius: 4px;
  margin-bottom: 5px;
  transition: background-color 0.3s;
}

.sidebar-item:hover {
  background-color: #e0e0e0;
}

.sidebar-item.router-link-active {
  background-color: #e0e0e0;
  font-weight: bold;
}

.user-info {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ddd;
}

.avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  margin-bottom: 10px;
}

.user-details {
  margin-bottom: 10px;
}

.user-name {
  display: block;
  font-weight: bold;
}

.user-email {
  display: block;
  font-size: 0.9em;
  color: #666;
}

.logout-button {
  width: 100%;
  padding: 8px;
  background-color: #ff4444;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.logout-button:hover {
  background-color: #cc0000;
}
</style>