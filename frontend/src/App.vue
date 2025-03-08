<template>
  <div>
    <template v-if="showMenu">
      <Sidebar :isOpen="isMenuOpen" :user="currentUser" />
      <button 
        class="menu-toggle" 
        :class="{ 'menu-toggle-shifted': isMenuOpen }"
        @click="toggleMenu"
      >
        ☰
      </button>
    </template>
    
    <div class="content" :class="{ 'content-shifted': isMenuOpen && showMenu }">
      <router-view/>
    </div>
  </div>
</template>

<script>
import Sidebar from './components/Sidebar.vue';

export default {
  components: { Sidebar },
  data() {
    return {
      isMenuOpen: false,
      currentUser: null
    }
  },
  computed: {
    showMenu() {
      return !['/login', '/register'].includes(this.$route.path)
    }
  },
  watch: {
    $route() {
      this.isMenuOpen = false
    }
  },
  methods: {
    toggleMenu() {
      this.isMenuOpen = !this.isMenuOpen
    },
  },
  created() {
    if (this.$store.getters.isAuthenticated) {
      this.$store.dispatch('fetchUser');
    }
  }
}
</script>

<style>
.menu-toggle {
  position: fixed;
  top: 10px;
  left: 10px;
  z-index: 1001;
  padding: 10px;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  transition: 0.3s;
}

.menu-toggle-shifted {
  left: 260px;
}

.content {
  margin-left: 0;
  transition: 0.3s;
  padding: 20px;
}

.content-shifted {
  margin-left: 250px;
}
</style>