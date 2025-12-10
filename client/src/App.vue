<template>
  <div>
    <nav class="navbar navbar-expand-lg navbar-light bg-light fixed-top shadow-sm">
      <div class="container">
        <RouterLink class="navbar-brand" to="/">Concert Booking</RouterLink>
        <div class="navbar-nav gap-2 align-items-center">
          <RouterLink class="nav-link" to="/tickets">Shows</RouterLink>
          <RouterLink class="nav-link" to="/orders">My Orders</RouterLink>
          <RouterLink v-if="isAdmin" class="nav-link" to="/admin/events">Admin Events</RouterLink>
          <RouterLink v-if="!hasSession" class="nav-link" to="/auth">Login / Register</RouterLink>
          <button
            v-else
            class="btn btn-outline-secondary btn-sm"
            type="button"
            @click="handleLogout">
            Log out
          </button>
        </div>
      </div>
    </nav>
    <main class="container" style="padding-top: 80px">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { RouterView, RouterLink, useRouter } from 'vue-router'

const isAdmin = computed(() => localStorage.getItem('is_admin') === '1')
const hasSession = computed(() => !!localStorage.getItem('session_id'))
const router = useRouter()

function handleLogout() {
  localStorage.removeItem('session_id')
  localStorage.removeItem('is_admin')
  router.push({ path: '/auth' })
}
</script>
