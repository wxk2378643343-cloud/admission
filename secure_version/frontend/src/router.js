import { createRouter, createWebHistory } from 'vue-router'
import { getCurrentUser } from './api'

const routes = [
  { path: '/login', component: () => import('./views/LoginView.vue') },
  {
    path: '/admin',
    component: () => import('./views/admin/AdminLayout.vue'),
    children: [
      { path: '', component: () => import('./views/admin/DashboardView.vue') },
      { path: 'students', component: () => import('./views/admin/CrudPage.vue'), meta: { title: '学生信息管理', resource: 'students' } },
      { path: 'scores', component: () => import('./views/admin/ScoreManagement.vue') },
      { path: 'plans', component: () => import('./views/admin/CrudPage.vue'), meta: { title: '招生计划管理', resource: 'plans' } },
      { path: 'choices', component: () => import('./views/admin/ChoiceManagement.vue') },
      { path: 'admissions', component: () => import('./views/admin/AdmissionReview.vue') },
      { path: 'notices', component: () => import('./views/admin/CrudPage.vue'), meta: { title: '公告管理', resource: 'notices' } }
    ]
  },
  {
    path: '/student',
    component: () => import('./views/student/StudentLayout.vue'),
    children: [
      { path: '', component: () => import('./views/student/StudentHome.vue') },
      { path: 'profile', component: () => import('./views/student/StudentProfile.vue') },
      { path: 'score', component: () => import('./views/student/StudentScore.vue') },
      { path: 'choices', component: () => import('./views/student/StudentChoices.vue') },
      { path: 'admission', component: () => import('./views/student/StudentAdmission.vue') },
      { path: 'notices', component: () => import('./views/student/StudentNotices.vue') },
      { path: 'password', component: () => import('./views/student/StudentPassword.vue') }
    ]
  },
  { path: '/', redirect: '/login' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, _, next) => {
  const user = getCurrentUser()
  if (to.path === '/login') {
    next()
    return
  }
  if (!user) {
    next('/login')
    return
  }
  if (to.path.startsWith('/admin') && user.role !== 'admin') {
    next('/student')
    return
  }
  if (to.path.startsWith('/student') && user.role !== 'student') {
    next('/admin')
    return
  }
  next()
})

export default router
