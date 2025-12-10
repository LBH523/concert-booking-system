<template>
  <div class="container py-4">
    <div class="d-flex align-items-center justify-content-between mb-3">
      <div>
        <h3 class="mb-1">{{ eventInfo?.name || 'Event Detail' }}</h3>
        <p class="text-muted mb-0">Date: {{ eventInfo?.event_date }} | Start: {{ eventInfo?.start_time }}</p>
      </div>
      <button class="btn btn-outline-secondary" @click="goBack">Back to list</button>
    </div>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <div v-if="purchaseMessage" class="alert" :class="purchaseClass">{{ purchaseMessage }}</div>

    <div class="row">
      <div class="col-lg-7 mb-3">
        <div class="d-flex justify-content-between align-items-center mb-2">
          <h5 class="mb-0">Seat Selection</h5>
          <span class="text-muted small">Selected {{ selectedSeatIds.length }}/4</span>
        </div>
        <SeatGrid
          :seats="seats"
          v-model:selected="selectedSeatIds"
          :max-selectable="4"
          @limit-hit="onLimitHit" />
        <p v-if="limitHint" class="text-warning small mt-2">{{ limitHint }}</p>
        <p v-if="loadingSeats" class="text-muted mt-2">Loading seats...</p>
      </div>

      <div class="col-lg-5">
        <div class="card shadow-sm mb-3">
          <div class="card-body">
            <h5 class="card-title mb-3">Tiers & Remaining</h5>
            <ul class="list-unstyled mb-0" v-if="seatTypes.length">
              <li v-for="tier in seatTypes" :key="tier.type" class="d-flex justify-content-between mb-2">
                <span>{{ tier.label }}</span>
                <span>{{ tier.price }} HKD (Remaining {{ tier.remaining }})</span>
              </li>
            </ul>
            <p v-else class="text-muted mb-0">No seat info.</p>
          </div>
        </div>

        <div class="card shadow-sm">
          <div class="card-body">
            <h5 class="card-title mb-3">Order Summary</h5>
            <div v-if="selectedSeatDetails.length">
              <ul class="list-unstyled mb-3">
                <li v-for="seat in selectedSeatDetails" :key="seat.id">
                  Seat {{ seat.row }}-{{ seat.col }} | {{ seatTypeLabel(seat.type) }} | {{ seat.price }} HKD
                </li>
              </ul>
              <div class="d-flex justify-content-between align-items-center border-top pt-2">
                <strong>Total</strong>
                <strong>{{ totalPrice }} HKD</strong>
              </div>
            </div>
            <p v-else class="text-muted">Select seats (max 4).</p>

            <button
              class="btn btn-primary w-100 mt-3"
              :disabled="!selectedSeatIds.length || purchasing"
              @click="handlePurchase">
              {{ purchasing ? 'Submitting...' : 'Submit Order' }}
            </button>
            <button
              class="btn btn-outline-secondary w-100 mt-2"
              type="button"
              :disabled="purchasing || !selectedSeatIds.length"
              @click="selectedSeatIds = []">
              Clear Selection
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import SeatGrid from '../../components/tickets/SeatGrid.vue'
import { getEventDetail, purchase } from '../../api/tickets'

const route = useRoute()
const router = useRouter()
const seats = ref([])
const loadingSeats = ref(false)
const error = ref('')
const purchasing = ref(false)
const purchaseMessage = ref('')
const purchaseSuccess = ref(false)
const selectedSeatIds = ref([])
const limitHint = ref('')
const eventInfo = ref(route.state?.event || null)

const seatTypes = computed(() => summarizeSeats(seats.value))

const selectedSeatDetails = computed(() =>
  seats.value.filter((seat) => selectedSeatIds.value.includes(seat.id))
)

const totalPrice = computed(() =>
  selectedSeatDetails.value.reduce((sum, seat) => sum + Number(seat.price || 0), 0)
)

onMounted(() => {
  loadSeats()
})

async function loadSeats() {
  error.value = ''
  loadingSeats.value = true
  try {
    const res = await getEventDetail(route.params.id)
    if (res.status === 'success') {
      seats.value = res.data || []
    } else {
      error.value = res.message || 'Unable to load seats'
    }
  } catch (err) {
    error.value = err.response?.data?.message || err.message || 'Failed to load seats'
  } finally {
    loadingSeats.value = false
  }
}

function seatTypeLabel(type) {
  if (type === 1) return 'VIP'
  if (type === 2) return 'Standard'
  return 'Economy'
}

function summarizeSeats(list) {
  const map = {}
  list.forEach((seat) => {
    if (!map[seat.type]) {
      map[seat.type] = {
        type: seat.type,
        label: seatTypeLabel(seat.type),
        price: seat.price,
        total: 0,
        reserved: 0,
      }
    }
    map[seat.type].total += 1
    if (seat.is_reserved) map[seat.type].reserved += 1
  })
  return Object.values(map).map((tier) => ({
    ...tier,
    remaining: tier.total - tier.reserved,
  }))
}

function onLimitHit() {
  limitHint.value = 'You can select up to 4 seats per event.'
  setTimeout(() => (limitHint.value = ''), 2000)
}

async function handlePurchase() {
  if (!selectedSeatIds.value.length) return
  purchasing.value = true
  purchaseMessage.value = ''
  purchaseSuccess.value = false
  const maxAttempts = 2
  let attempt = 0
  let lastError = ''

  while (attempt < maxAttempts) {
    try {
      const res = await purchase(route.params.id, selectedSeatIds.value)
      if (res.status === 'success') {
        purchaseMessage.value = `Purchase successful! Order #${res.order_id}, total ${res.total_price} HKD`
        purchaseSuccess.value = true
        selectedSeatIds.value = []
        await loadSeats()
        break
      }
      lastError = res.message || 'Purchase failed'
    } catch (err) {
      lastError = err.response?.data?.message || err.message || 'Purchase failed'
    }

    attempt += 1
    await loadSeats()

    if (attempt >= maxAttempts) {
      purchaseMessage.value = `${lastError}. Please try again.`
      purchaseSuccess.value = false
    }
  }

  purchasing.value = false
}

function goBack() {
  router.push({ name: 'EventBrowse' })
}

const purchaseClass = computed(() => (purchaseSuccess.value ? 'alert-success' : 'alert-danger'))
</script>
