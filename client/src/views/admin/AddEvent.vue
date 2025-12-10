<template>
  <div class="container py-4" style="max-width: 720px">
    <h3 class="mb-3">Add Event</h3>
    <form @submit.prevent="submit">
      <div class="row g-3">
        <div class="col-md-6">
          <label class="form-label">Event Name</label>
          <input v-model="form.name" class="form-control" required />
        </div>
        <div class="col-md-6">
          <label class="form-label">Poster</label>
          <input type="file" class="form-control" accept="image/*" @change="onFile" required />
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
        <button class="btn btn-primary" type="submit" :disabled="submitting">{{ submitting ? 'Submitting...' : 'Submit' }}</button>
        <router-link class="btn btn-outline-secondary" :to="{ name: 'AdminEventList' }">Back to list</router-link>
      </div>
      <div v-if="message" class="mt-3 alert" :class="messageType === 'success' ? 'alert-success' : 'alert-danger'">
        {{ message }}
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { addEvent } from '../../api/adminEvents'

const router = useRouter()
const form = reactive({ name: '', event_date: '', start_time: '', price_1: '', price_2: '', price_3: '' })
const file = ref(null)
const submitting = ref(false)
const message = ref('')
const messageType = ref('')

const priceFields = computed(() => [
  { key: 'price_1', label: 'VIP Price' },
  { key: 'price_2', label: 'Standard Price' },
  { key: 'price_3', label: 'Economy Price' },
])

function onFile(e) {
  file.value = e.target.files[0]
}

async function submit() {
  if (!file.value) {
    message.value = 'Please upload a poster'
    messageType.value = 'error'
    return
  }
  const fd = new FormData()
  Object.entries(form).forEach(([k, v]) => fd.append(k, v))
  fd.append('poster', file.value)
  submitting.value = true
  message.value = ''
  try {
    const res = await addEvent(fd)
    if (res.status === 'success') {
      message.value = 'Added successfully'
      messageType.value = 'success'
      router.replace({ name: 'AdminEventList' })
    } else {
      throw new Error(res.message || 'Add failed')
    }
  } catch (err) {
    message.value = err.response?.data?.message || err.message || 'Add failed'
    messageType.value = 'error'
  } finally {
    submitting.value = false
  }
}
</script>
