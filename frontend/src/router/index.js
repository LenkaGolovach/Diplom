import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Board from '../components/Board.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/board/:id',
    name: 'Board',
    component: Board,
    props: true
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

