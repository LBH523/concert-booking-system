<template>
  <div class="container py-4" style="max-width: 720px">
    <h3 class="mb-3">Edit Event</h3>
    <form v-if="event" @submit.prevent="submit">
      <div class="row g-3">
        <div class="col-md-6">
          <label class="form-label">Event Name (read-only)</label>
          <input class="form-control" :value="event.name" disabled />
        </div>
        <div class="col-md-6">
          <label class="form-label">Date</label>
          <input v-model="form.event_date" type="date" class="form-control" required />
        </div>
        <div class="col-md-6">
          <label class="form-label">Start Time</label>
          <input v-model="form.start_time" type="time" class="form-control" required />
        </div>
        <div class="col-md-4" v-for="field in priceFields" :key="field.key">
          <label class="form-label">{{ field.label }}</label>
          <input v-model.number="form[field.key]" type="number" min="0" class="form-control" required />
        </div>
      </div>
      <div class="d-flex gap-2 mt-4">
        <button class="btn btn-primary" type="submit" :disabled="submitting">{{ submitting ? 'Saving...' : 'Save changes' }}</button>
        <router-link class="btn btn-outline-secondary" :to="{ name: 'AdminEventList' }">Back to list</router-link>
      </div>
      <div v-if="message" class="mt-3 alert" :class="messageType === 'success' ? 'alert-success' : 'alert-danger'">
        {{ message }}
      </div>
    </form>
    <div v-else class="text-muted">Loading...</div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { editEvent } from '../../api/adminEvents'
import { getEventDetail } from '../../api/tickets'

const route = useRoute()
const router = useRouter()
const event = ref(route.state?.event || null)
const form = reactive({ event_id: route.params.id, event_date: '', start_time: '', price_1: '', price_2: '', price_3: '' })
const submitting = ref(false)
const message = ref('')
const messageType = ref('')

const priceFields = computed(() => [
  { key: 'price_1', label: 'VIP Price' },
  { key: 'price_2', label: 'Standard Price' },
  { key: 'price_3', label: 'Economy Price' },
])

onMounted(load)

async function load() {
  if (!event.value) {
    try {
      const seatsRes = await getEventDetail(route.params.id)
      event.value = { id: route.params.id, name: `Event ${route.params.id}` }
      fillPriceFromSeats(seatsRes.data || seatsRes || [])
    } catch (err) {
      message.value = err.response?.data?.message || err.message || 'Failed to load'
      messageType.value = 'error'
    }
  } else {
    form.event_date = event.value.event_date || ''
    form.start_time = event.value.start_time || ''
    form.price_1 = event.value.price_1 || ''
    form.price_2 = event.value.price_2 || ''
    form.price_3 = event.value.price_3 || ''
  }
}

function fillPriceFromSeats(seats) {
  seats.forEach((s) => {
    if (s.type === 1) form.price_1 = s.price
    if (s.type === 2) form.price_2 = s.price
    if (s.type === 3) form.price_3 = s.price
  })
}

async function submit() {
  submitting.value = true
  message.value = ''
  try {
    const res = await editEvent({
      event_id: Number(route.params.id),
      event_date: form.event_date,
      start_time: form.start_time,
      price_1: form.price_1,
      price_2: form.price_2,
      price_3: form.price_3,
    })
    if (res.status === 'success') {
      message.value = 'Saved'
      messageType.value = 'success'
      router.replace({ name: 'AdminEventList' })
    } else {
      throw new Error(res.message || 'Save failed')
    }
  } catch (err) {
    message.value = err.response?.data?.message || err.message || 'Save failed'
    messageType.value = 'error'
  } finally {
    submitting.value = false
  }
}
</script>
