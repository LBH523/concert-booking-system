import { createRouter, createWebHistory } from 'vue-router'
import Books from '../components/Books.vue'
import Ping from '../components/Ping.vue'
import EventBrowse from '../views/Tickets/EventBrowse.vue'
import SeatSelection from '../views/Tickets/SeatSelection.vue'
import Auth from '../views/Auth.vue'
import Orders from '../views/Orders.vue'
import AdminEventList from '../views/admin/AdminEventList.vue'
import AddEvent from '../views/admin/AddEvent.vue'
import EditEvent from '../views/admin/EditEvent.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'EventBrowse',
      component: EventBrowse,
    },
    {
      path: '/books',
      name: 'Books',
      component: Books,
    },
    {
      path: '/ping',
      name: 'ping',
      component: Ping
    },
    {
      path: '/tickets',
      name: 'TicketList',
      component: EventBrowse,
    },
    {
      path: '/tickets/:id',
      name: 'SeatSelection',
      component: SeatSelection,
    },
    {
      path: '/auth',
      name: 'Auth',
      component: Auth,
    },
    {
      path: '/orders',
      name: 'Orders',
      component: Orders,
    },
    {
      path: '/admin/events',
      name: 'AdminEventList',
      component: AdminEventList,
      meta: { requiresAdmin: true },
    },
    {
      path: '/admin/events/add',
      name: 'AdminAddEvent',
      component: AddEvent,
      meta: { requiresAdmin: true },
    },
    {
      path: '/admin/events/:id/edit',
      name: 'AdminEditEvent',
      component: EditEvent,
      meta: { requiresAdmin: true },
    },
  ]
})

const publicPaths = ['/auth', '/ping']

router.beforeEach((to, from, next) => {
  const isPublic = publicPaths.includes(to.path)
  const hasSession = !!localStorage.getItem('session_id')
  const isAdmin = localStorage.getItem('is_admin') === '1'
  const adminOnly = to.meta?.requiresAdmin

  if (!isPublic && !hasSession) {
    return next({ path: '/auth', query: { redirect: to.fullPath } })
  }
  if (adminOnly && !isAdmin) {
    return next({ path: '/auth', query: { redirect: to.fullPath, reason: 'no-admin' } })
  }
  next()
})

export default router
