<template>
  <div class="container py-4">
    <div class="d-flex align-items-center justify-content-between mb-4">
      <h2 class="mb-0">Event List</h2>
      <div class="d-flex gap-2">
        <input
          v-model="keyword"
          type="text"
          class="form-control"
          placeholder="Search name or date (YYYY-MM-DD)"
          @keyup.enter="fetchEvents" />
        <button class="btn btn-primary" @click="fetchEvents" :disabled="loading">
          {{ loading ? 'Searching...' : 'Search' }}
        </button>
        <button class="btn btn-outline-secondary" type="button" @click="resetSearch" :disabled="loading">
          Clear
        </button>
      </div>
    </div>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <div v-if="!loading && !events.length" class="alert alert-warning">
      No events yet, try another keyword or date.
    </div>

    <div v-if="loading" class="text-muted">Loading...</div>

    <div class="row g-3" v-if="!loading">
      <div class="col-md-6" v-for="event in pagedEvents" :key="event.id">
        <div class="card h-100 shadow-sm">
          <div class="row g-0 h-100">
            <div class="col-4">
              <img
                v-if="event.poster_url"
                :src="event.poster_url"
                alt="poster"
                class="img-fluid h-100 w-100"
                style="object-fit: cover;" />
              <div v-else class="bg-light h-100 d-flex align-items-center justify-content-center text-muted small">
                No poster
              </div>
            </div>
            <div class="col-8">
              <div class="card-body h-100 d-flex flex-column">
                <div class="d-flex justify-content-between align-items-start mb-2">
                  <div>
                    <h5 class="card-title mb-1">{{ event.name }}</h5>
                    <p class="text-muted small mb-1">Date: {{ event.event_date }}</p>
                    <p class="text-muted small">Start: {{ event.start_time }}</p>
                  </div>
                  <button class="btn btn-outline-primary btn-sm" @click="goToSeatSelection(event)">
                    Seats / Book
                  </button>
                </div>

                <div class="mt-auto">
                  <div v-if="seatSummaries[event.id]" class="small text-muted">
                    <p class="mb-1" v-for="tier in seatSummaries[event.id]" :key="tier.type">
                      {{ tier.label }}: {{ tier.price }} HKD (Remaining {{ tier.remaining }})
                    </p>
                  </div>
                  <div v-else class="text-muted small">Loading price/remaining...</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <nav v-if="totalPages > 1" class="mt-4">
      <ul class="pagination">
        <li class="page-item" :class="{ disabled: currentPage === 1 }">
          <button class="page-link" @click="changePage(currentPage - 1)">Prev</button>
        </li>
        <li
          v-for="page in totalPages"
          :key="page"
          class="page-item"
          :class="{ active: page === currentPage }">
          <button class="page-link" @click="changePage(page)">{{ page }}</button>
        </li>
        <li class="page-item" :class="{ disabled: currentPage === totalPages }">
          <button class="page-link" @click="changePage(currentPage + 1)">Next</button>
        </li>
      </ul>
    </nav>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getEventDetail, searchEvents } from '../../api/tickets'

const keyword = ref('')
const loading = ref(false)
const error = ref('')
const events = ref([])
const seatSummaries = reactive({})
const pageSize = 10
const currentPage = ref(1)
const router = useRouter()

const totalPages = computed(() => Math.max(1, Math.ceil(events.value.length / pageSize)))
const pagedEvents = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return events.value.slice(start, start + pageSize)
})

onMounted(fetchEvents)

function resetSearch() {
  keyword.value = ''
  fetchEvents()
}

async function fetchEvents() {
  loading.value = true
  error.value = ''
  try {
    const response = await searchEvents({ keyword: keyword.value.trim() })
    events.value = response.data || []
    currentPage.value = 1
    preloadSeatSummaries()
  } catch (err) {
    error.value = err.response?.data?.message || err.message || 'Failed to load'
    events.value = []
  } finally {
    loading.value = false
  }
}

async function preloadSeatSummaries() {
  seatSummariesClear()
  const currentBatch = [...events.value]
  await Promise.all(
    currentBatch.map(async (event) => {
      try {
        const res = await getEventDetail(event.id)
        if (res.status === 'success') {
          seatSummaries[event.id] = summarizeSeats(res.data || [])
        }
      } catch (err) {
        console.error('Failed to load prices', err)
      }
    })
  )
}

function summarizeSeats(seats) {
  const map = {}
  seats.forEach((seat) => {
    if (!map[seat.type]) {
      map[seat.type] = {
        type: seat.type,
        price: seat.price,
        label: seatTypeLabel(seat.type),
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

function seatTypeLabel(type) {
  if (type === 1) return 'VIP'
  if (type === 2) return 'Standard'
  return 'Economy'
}

function changePage(page) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
}

function seatSummariesClear() {
  Object.keys(seatSummaries).forEach((key) => delete seatSummaries[key])
}

function goToSeatSelection(event) {
  router.push({
    name: 'SeatSelection',
    params: { id: event.id },
    state: { event },
  })
}
</script>
