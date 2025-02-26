import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import axios from 'axios'

createApp(App).use(router).mount('#app');
axios.defaults.baseURL = 'http://localhost:8080'
axios.interceptors.request.use(config => {
  const token = store.state.token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
