import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store' 
import axios from 'axios'
// import '@fortawesome/fontawesome-free/css/all.css'; // Удаляем, так как переходим на SVG для иконки поиска

/* import the fontawesome core */
// import { library } from '@fortawesome/fontawesome-svg-core'

/* import specific icons */
// import { faSearch, faUser, faTasks, faComments, faSignOutAlt, faPlus, faEdit, faTrash, faCopy, faReply, faPaperclip, faThList, faUserCircle, faProjectDiagram, faChevronDown, faChevronUp, faFileAlt, faCog, faQuestionCircle } from '@fortawesome/free-solid-svg-icons'

/* import font awesome icon component */
// import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

/* add icons to the library */
// library.add(faSearch, faUser, faTasks, faComments, faSignOutAlt, faPlus, faEdit, faTrash, faCopy, faReply, faPaperclip, faThList, faUserCircle, faProjectDiagram, faChevronDown, faChevronUp, faFileAlt, faCog, faQuestionCircle)

const app = createApp(App)

/* add font awesome icon component */
// app.component('font-awesome-icon', FontAwesomeIcon)

app.use(router)
app.use(store) 

// Настраиваем базовый URL для axios
axios.defaults.baseURL = process.env.VUE_APP_API_URL || 'http://localhost:8000'
axios.defaults.withCredentials = true;

// Настраиваем глобальные заголовки
axios.defaults.headers.common['Accept'] = 'application/json';

// Добавляем токен авторизации, если он есть
const token = localStorage.getItem('token');
if (token) {
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}

// Настраиваем перехватчик ответов
axios.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;
    
    // Подробное логирование ошибок
    console.error('Axios error:', error);
    if (error.response) {
      console.error('Status:', error.response.status);
      console.error('Data:', error.response.data);
      console.error('Headers:', error.response.headers);
    }
    
    // Обработка 401 ошибки (неавторизован)
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        
        // Если нет токена обновления, перенаправляем на страницу входа
        if (!refreshToken) {
          store.commit('logout');
          router.push('/login');
          return Promise.reject(error);
        }
        
        // Пытаемся обновить токен
        const response = await axios.post('/api/auth/token/refresh/', { refresh: refreshToken });
        
        localStorage.setItem('access_token', response.data.access);
        axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access}`;
        originalRequest.headers.Authorization = `Bearer ${response.data.access}`;
        
        return axios(originalRequest);
      } catch (refreshError) {
        // Если не удалось обновить токен, выходим из системы
        console.error('Failed to refresh token:', refreshError);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        store.commit('logout');
        router.push('/login');
        return Promise.reject(error);
      }
    }
    
    return Promise.reject(error);
  }
);

app.mount('#app')