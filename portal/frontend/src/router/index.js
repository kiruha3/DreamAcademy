import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import CoursesView from '../views/CoursesView.vue'
import DashboardView from '../views/DashboardView.vue'
import AdminView from '../views/AdminView.vue'
import CourseDetailView from '../views/CourseDetailView.vue'

const routes = [
  { path: '/', name: 'Home', component: HomeView },
  { path: '/login', name: 'Login', component: LoginView },
  { path: '/register', name: 'Register', component: RegisterView },
  { path: '/courses', name: 'Courses', component: CoursesView },
  { path: '/courses/:id', name: 'CourseDetail', component: CourseDetailView },
  { path: '/dashboard', name: 'Dashboard', component: DashboardView },
  { path: '/admin', name: 'Admin', component: AdminView },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
