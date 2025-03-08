import { createStore } from 'vuex'
import axios from 'axios'

export default createStore({
  state: {
    user: null,
    token: localStorage.getItem('token') || null
  },
  mutations: {
    setUser(state, user) {
      state.user = {
        ...user,
        avatar_url: user.avatar ? 
          `${process.env.VUE_APP_API_URL}${user.avatar}` : 
          'https://www.gravatar.com/avatar/?d=identicon'
      };
    },
    setToken(state, token) {
      state.token = token
      localStorage.setItem('token', token)
    },
    logout() {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      delete axios.defaults.headers.common['Authorization'];
    }
  },
  actions: {
    async login({ commit }, credentials) {
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
          commit('setUser', response.data.user);
          commit('setToken', response.data.access); 
          localStorage.setItem('token', response.data.access);
      } catch (error) {
          throw error; 
      }
    },
    async register({ commit }, credentials) {
      const response = await axios.post('/api/auth/register/', credentials)
      commit('setToken', response.data.token)
      commit('setUser', response.data.user)
    },
    logout({ commit }) {
      commit('logout')
    },
    async fetchUser({ commit }) {
      try {
        const response = await axios.get('/api/users/me/', {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        });
        commit('setUser', response.data);
      } catch (error) {
        console.error('Ошибка загрузки пользователя:', error);
      }
    },
    async updateUser({ commit, state }, formData) {
      try {
        const response = await axios.patch('/api/users/me/', formData, {
          headers: {
            Authorization: `Bearer ${state.token}`,
            'Content-Type': 'multipart/form-data'
          }
        });
        commit('setUser', response.data);
        return response.data;
      } catch (error) {
        throw error;
      }
    }
  },
  getters: {
    isAuthenticated: state => !!state.token
  }
})