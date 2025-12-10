<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h3 class="mb-0">Event List</h3>
      <router-link class="btn btn-primary" :to="{ name: 'AdminAddEvent' }">+ Add Event</router-link>
    </div>

    <div v-if="loading" class="text-muted">Loading...</div>
    <div v-else-if="error" class="alert alert-danger">{{ error }}</div>
    <div v-else-if="!events.length" class="alert alert-warning">No events</div>

    <div class="row g-3">
      <div class="col-md-4" v-for="item in events" :key="item.id">
        <div class="card h-100 shadow-sm">
          <img
            v-if="item.poster_url"
            :src="item.poster_url"
            class="card-img-top"
            style="object-fit: cover; height: 180px;"
          />
          <div class="card-body">
            <h5 class="card-title">{{ item.name }}</h5>
            <p class="mb-1 text-muted">Date: {{ item.event_date }} | Start: {{ item.start_time }}</p>
            <p class="mb-1">VIP: {{ item.price_1 }} | Standard: {{ item.price_2 }} | Economy: {{ item.price_3 }}</p>
          </div>
          <div class="card-footer d-flex gap-2">
            <router-link
              class="btn btn-sm btn-outline-primary flex-grow-1"
              :to="{ name: 'AdminEditEvent', params: { id: item.id }, state: { event: item } }"
            >
              Edit
            </router-link>
            <button class="btn btn-sm btn-outline-danger" @click="confirmDelete(item)">Delete</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { fetchAllEvents, deleteEvent } from '../../api/adminEvents'
import { getEventDetail } from '../../api/tickets'

const events = ref([])
const loading = ref(false)
const error = ref('')

onMounted(load)

async function load() {
  loading.value = true
  error.value = ''
  try {
    const res = await fetchAllEvents()
    const list = res.data || res || []
    events.value = list
    await preloadPrices(list)
  } catch (err) {
    error.value = err.response?.data?.message || err.message || 'Failed to load'
  } finally {
    loading.value = false
  }
}

async function preloadPrices(list) {
  await Promise.all(
    (list || []).map(async (item) => {
      try {
        const seats = await getEventDetail(item.id)
        const data = seats.data || seats || []
        data.forEach((s) => {
          if (s.type === 1) item.price_1 = s.price
          if (s.type === 2) item.price_2 = s.price
          if (s.type === 3) item.price_3 = s.price
        })
      } catch (err) {
        console.error('Failed to load prices', err)
      }
    })
  )
}

async function confirmDelete(item) {
  if (!confirm(`Delete "${item.name}"?`)) return
  try {
    await deleteEvent(item.id)
    await load()
  } catch (err) {
    alert(err.response?.data?.message || err.message || 'Delete failed')
  }
}
</script>
