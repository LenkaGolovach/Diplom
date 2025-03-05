<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script>
export default {
  created() {
    const token = localStorage.getItem('access_token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      this.$router.push('/login');
    }
  }
}
</script>
