import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store' 
import axios from 'axios'

const app = createApp(App)
app.use(router)
app.use(store) 

axios.defaults.baseURL = 'http://localhost:8000' 
axios.defaults.withCredentials = true;
axios.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;
    
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post('/api/auth/token/refresh/', { refresh: refreshToken });
        
        localStorage.setItem('access_token', response.data.access);
        originalRequest.headers.Authorization = `Bearer ${response.data.access}`;
        return axios(originalRequest);
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

app.mount('#app')