import { createRouter, createWebHistory } from 'vue-router';
import Login from '../components/Auth/Login.vue';
import Register from '../components/Auth/Register.vue';
import BoardsList from '../views/BoardsList.vue';
import Board from '../views/Board.vue';
import NeuroChat from '@/views/NeuroChat.vue';

const routes = [
  { path: '/', redirect: '/login' },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../components/Auth/Login.vue'),
    meta: { hideMenu: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../components/Auth/Register.vue'),
    meta: { hideMenu: true }
  },
  { path: '/boards', component: BoardsList, meta: { requiresAuth: true } },
  { path: '/boards/:id', component: Board, meta: { requiresAuth: true }, props: true },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/Profile.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/invite/:token',
    name: 'Invite',
    component: () => import('../views/InviteView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/neuro-chat',
    name: 'NeuroChat',
    component: NeuroChat,
    meta: { requiresAuth: true }
  }
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

router.beforeEach((to, from, next) => {
  const isAuthenticated = localStorage.getItem('token');
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login');
  } else {
    next();
  }
});

router.beforeEach((to, from, next) => {
  const isAuthenticated = localStorage.getItem('token');
  
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login');
  } else if ((to.path === '/login' || to.path === '/register') && isAuthenticated) {
    // Redirect to boards if already authenticated
    next('/boards');
  } else {
    next();
  }
});

export default router;