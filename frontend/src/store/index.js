import { createStore } from 'vuex'
import axios from 'axios'

export default createStore({
  state: {
    user: null,
    token: localStorage.getItem('token') || null
  },
  mutations: {
    setUser(state, user) {
      state.user = user
    },
    setToken(state, token) {
      state.token = token
      localStorage.setItem('token', token)
    },
    logout(state) {
      state.user = null
      state.token = null
      localStorage.removeItem('token')
    }
  },
  actions: {
    async login({ commit }, credentials) {
      const response = await axios.post('/api/auth/login/', credentials)
      commit('setToken', response.data.token)
      commit('setUser', response.data.user)
    },
    async register({ commit }, credentials) {
      const response = await axios.post('/api/auth/register/', credentials)
      commit('setToken', response.data.token)
      commit('setUser', response.data.user)
    },
    logout({ commit }) {
      commit('logout')
    }
  },
  getters: {
    isAuthenticated: state => !!state.token
  }
})