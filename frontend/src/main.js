import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store' 
import axios from 'axios'

const app = createApp(App)
app.use(router)
app.use(store) 

axios.defaults.baseURL = 'http://localhost:8000' 
axios.interceptors.request.use(config => {
  const token = localStorage.getItem('token') // Получаем токен напрямую из localStorage
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

app.mount('#app')