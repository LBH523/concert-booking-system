<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h3 class="mb-0">Orders</h3>
      <select class="form-select w-auto" v-model="selectedStatus">
        <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
    </div>

    <div v-if="message" class="alert" :class="messageClass">{{ message }}</div>
    <div v-if="loading" class="text-muted">Loading...</div>
    <div v-else-if="error" class="alert alert-danger">{{ error }}</div>
    <div v-else-if="!orders.length" class="alert alert-warning">No orders</div>

    <div v-else class="card shadow-sm">
      <div class="card-body p-0">
        <table class="table table-striped mb-0">
          <thead>
            <tr>
              <th scope="col">Order ID</th>
              <th scope="col">Event</th>
              <th scope="col">Total</th>
              <th scope="col">Created At</th>
              <th v-if="isAdmin" scope="col">User</th>
              <th scope="col">Status</th>
              <th scope="col" class="text-end">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="order in orders" :key="order.id">
              <td>{{ order.id }}</td>
              <td>{{ order.name }}</td>
              <td>{{ order.total_price }}</td>
              <td>{{ formatTime(order.created_at) }}</td>
              <td v-if="isAdmin">{{ order.username }}</td>
              <td>{{ statusLabel }}</td>
              <td class="text-end">
                <button
                  v-if="selectedStatus !== '0'"
                  class="btn btn-sm btn-outline-danger"
                  :disabled="cancellingId === order.id"
                  @click="handleCancel(order.id)">
                  {{ cancellingId === order.id ? 'Cancelling...' : 'Cancel Order' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { fetchOrders, cancelOrder } from '../api/orders'

const orders = ref([])
const loading = ref(false)
const error = ref('')
const message = ref('')
const messageType = ref('')
const cancellingId = ref(null)
const selectedStatus = ref('2')

const statusOptions = [
  { value: '2', label: 'All (2)' },
  { value: '1', label: 'Active (1)' },
  { value: '0', label: 'Canceled (0)' },
]

const isAdmin = computed(() => localStorage.getItem('is_admin') === '1')
const statusLabel = computed(() => {
  if (selectedStatus.value === '1') return 'Active'
  if (selectedStatus.value === '0') return 'Canceled'
  return 'Active/Canceled'
})
const messageClass = computed(() => (messageType.value === 'success' ? 'alert-success' : 'alert-danger'))

onMounted(loadOrders)
watch(selectedStatus, loadOrders)

function formatTime(ts) {
  if (!ts) return '-'
  return ts.replace('T', ' ').replace('Z', '')
}

async function loadOrders() {
  loading.value = true
  error.value = ''
  message.value = ''
  try {
    const res = await fetchOrders(selectedStatus.value)
    if (res.data && res.data.status === 'success') {
      orders.value = res.data.data || []
    } else {
      const payload = res.data || {}
      throw new Error(payload.message || 'Load failed')
    }
  } catch (err) {
    error.value = err.response?.data?.message || err.message || 'Load failed'
    orders.value = []
  } finally {
    loading.value = false
  }
}

async function handleCancel(orderId) {
  cancellingId.value = orderId
  message.value = ''
  try {
    const res = await cancelOrder(orderId)
    if (res.data && res.data.status === 'success') {
      message.value = 'Order canceled'
      messageType.value = 'success'
      await loadOrders()
    } else {
      const payload = res.data || {}
      throw new Error(payload.message || 'Cancel failed')
    }
  } catch (err) {
    message.value = err.response?.data?.message || err.message || 'Cancel failed'
    messageType.value = 'error'
  } finally {
    cancellingId.value = null
  }
}
</script>
