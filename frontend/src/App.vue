<template>
  <div>
    <template v-if="showMenu">
      <Sidebar :isOpen="isMenuOpen" @close="closeSidebar" />
      <button 
        class="menu-toggle" 
        :class="{ 'menu-toggle-shifted': isMenuOpen }"
        @click="toggleMenu"
      >
        ☰
      </button>
    </template>
    
    <div class="content" :class="{ 'content-shifted': isMenuOpen && showMenu }">
      <router-view @auth-changed="checkAuthStatus"/>
    </div>
  </div>
</template>

<script>
import Sidebar from './components/Sidebar.vue';

export default {
  components: { Sidebar },
  data() {
    return {
      isMenuOpen: false
    }
  },
  computed: {
    // Изменяем логику - показываем меню на всех страницах, кроме login и register
    showMenu() {
      return !['/login', '/register'].includes(this.$route.path);
    }
  },
  watch: {
    $route() {
      this.isMenuOpen = false;
      this.checkAuthStatus();
    }
  },
  methods: {
    toggleMenu() {
      this.isMenuOpen = !this.isMenuOpen;
    },
    closeSidebar() {
      this.isMenuOpen = false;
    },
    checkAuthStatus() {
      // Если токен существует, но данных пользователя нет, загружаем их
      if (this.$store.getters.isAuthenticated && !this.$store.getters.currentUser) {
        this.$store.dispatch('fetchUser');
      }
    }
  },
  created() {
    // Always try to fetch user data on app startup if we have a token
    if (this.$store.getters.isAuthenticated) {
      this.$store.dispatch('fetchUser').catch(error => {
        // If there's an error fetching user data with the stored token,
        // it might be invalid/expired, so log the user out
        if (error.response && error.response.status === 401) {
          this.$store.dispatch('logout');
          this.$router.push('/login');
        }
      });
    }
  }
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

body {
  margin: 0;
  padding: 0;
  font-family: 'Poppins', 'Segoe UI', 'Roboto', 'Arial', sans-serif;
}

#app {
  font-family: 'Poppins', 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}

.menu-toggle {
  position: fixed;
  top: 20px;
  left: 20px;
  z-index: 2001;
  padding: 12px;
  width: 45px;
  height: 45px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.95);
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
  font-size: 20px;
  color: #333;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.menu-toggle:hover {
  background: rgba(255, 255, 255, 1);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
}

.menu-toggle-shifted {
  left: 270px;
  background: rgba(255, 255, 255, 0.95);
}

.content {
  margin-left: 0;
  transition: all 0.4s cubic-bezier(0.25, 1, 0.5, 1);
  padding: 20px;
}

.content-shifted {
  margin-left: 260px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>