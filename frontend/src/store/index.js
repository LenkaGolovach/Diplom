import { createStore } from 'vuex'
import axios from 'axios'
import neuro from './neuro'
import * as tasks from './tasks'

// Helper function to get base URL for assets
const getBaseUrl = () => {
  return process.env.VUE_APP_API_URL || 'http://localhost:8000';
};

// Helper function to format avatar URL
const formatAvatarUrl = (avatar) => {
  if (!avatar) return 'https://www.gravatar.com/avatar/?d=identicon';
  
  // Check if the avatar is already a full URL
  if (avatar.startsWith('http')) return avatar;

  // Handle relative URLs from backend
  if (avatar.startsWith('/media/')) {
    const baseUrl = getBaseUrl().replace(/\/+$/, '');
    return `${baseUrl}${avatar}`;
  }

  const baseUrl = getBaseUrl().replace(/\/+$/, '');
  const avatarPath = avatar.replace(/^\/+/, '');
  
  // Otherwise, append the base URL
  return `${baseUrl}/${avatarPath}`;
};

// Initialize axios with the token if it exists
const token = localStorage.getItem('token');
if (token) {
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}

export default createStore({
  modules: {
    neuro,
    tasks,
  },
  state: {
    user: null,
    token: token || null
  },
  mutations: {
    setUser(state, user) {
      if (!user) {
        state.user = null;
        return;
      }
      
      // Используем avatar_url из API если доступен, иначе форматируем avatar
      let avatar_url;
      
      if (user.avatar_url) {
        avatar_url = user.avatar_url;
      } else if (user.avatar) {
        avatar_url = formatAvatarUrl(user.avatar);
      } else {
        avatar_url = 'https://www.gravatar.com/avatar/?d=identicon';
      }
      
      state.user = {
        ...user,
        avatar_url
      };
      
      console.log("User updated in store with avatar:", state.user.avatar_url);
    },
    setToken(state, token) {
      state.token = token;
      if (token) {
        localStorage.setItem('token', token);
        // Set the token in axios defaults for all future requests
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      } else {
        localStorage.removeItem('token');
        delete axios.defaults.headers.common['Authorization'];
      }
    },
    logout(state) {
      state.token = null;
      state.user = null;
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
    }
  },
  actions: {
    async login({ commit, dispatch }, credentials) {
      try {
        const response = await axios.post(
          '/api/auth/login/', 
          credentials,
          {
            headers: {
              'Content-Type': 'application/json'
            }
          }
        );
        
        commit('setToken', response.data.access);
        
        // Fetch complete user data
        await dispatch('fetchUser');
        
        return response.data;
      } catch (error) {
        throw error; 
      }
    },
    async register({ commit, dispatch }, credentials) {
      try {
        const response = await axios.post('/api/auth/register/', credentials);
        commit('setToken', response.data.token);
        
        // Fetch complete user data after registration
        await dispatch('fetchUser');
        
        return response.data;
      } catch (error) {
        throw error;
      }
    },
    logout({ commit }) {
      commit('logout');
    },
    async fetchUser({ commit, state }) {
      if (!state.token) return;
      
      try {
        const response = await axios.get('/api/users/me/', {
          headers: {
            Authorization: `Bearer ${state.token}`
          }
        });

        console.log("Fetched user data:", response.data);

        commit('setUser', response.data);
        return response.data;
      } catch (error) {
        console.error('Ошибка загрузки пользователя:', error);
        // If unauthorized, logout
        if (error.response && error.response.status === 401) {
          commit('logout');
        }
        throw error;
      }
    },
    async updateUser({ commit, state }, userData) {
      try {
        console.log("Updating user with data:", userData);
        let contentType = 'application/json';
        let finalData = userData;
        
        // Check if userData is FormData object (for file uploads)
        if (userData instanceof FormData) {
          contentType = 'multipart/form-data';
          console.log("Using FormData for update");
          
          // Для диагностики выведем все поля FormData
          for(let pair of userData.entries()) {
            console.log(pair[0] + ': ' + (pair[1] instanceof File ? `File: ${pair[1].name}` : pair[1]));
          }
        } else {
          // Convert regular object to FormData to handle both text fields and files
          console.log("Converting object to FormData");
          const formData = new FormData();
          
          // Add all properties from userData to formData
          for (const key in userData) {
            if (userData.hasOwnProperty(key)) {
              formData.append(key, userData[key]);
              console.log(`Adding to FormData: ${key}`);
            }
          }
          
          finalData = formData;
        }
        
        const response = await axios.patch('/api/users/me/', finalData, {
          headers: {
            Authorization: `Bearer ${state.token}`,
            'Content-Type': contentType
          }
        });
        
        console.log("User update response:", response.data);
        commit('setUser', response.data);
        return response.data;
      } catch (error) {
        console.error('Error updating user:', error);
        if (error.response) {
            console.error('Response status:', error.response.status);
            console.error('Response data:', error.response.data);
        }
        throw error;
      }
    }
  },
  getters: {
    isAuthenticated: state => !!state.token,
    currentUser: state => state.user,
    token: state => state.token
  }
});