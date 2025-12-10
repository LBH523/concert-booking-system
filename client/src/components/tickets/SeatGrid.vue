<template>
  <div class="seat-grid">
    <div class="legend d-flex flex-wrap gap-2 mb-3">
      <span class="badge bg-seat-vip">VIP</span>
      <span class="badge bg-seat-standard">Standard</span>
      <span class="badge bg-seat-economy">Economy</span>
      <span class="badge bg-secondary">Reserved</span>
    </div>

    <div class="grid-wrapper">
      <div
        v-for="row in rows"
        :key="row.rowNumber"
        class="d-flex align-items-center mb-2">
        <div class="seat-row-label me-2">{{ row.rowNumber }}</div>
        <div class="d-flex flex-wrap gap-2">
          <button
            v-for="seat in row.seats"
            :key="seat.id"
            class="seat btn btn-sm"
            :class="seatClasses(seat)"
            :disabled="seat.is_reserved || isDisabled(seat.id)"
            @click="toggleSeat(seat.id)">
            {{ seat.row }}-{{ seat.col }}
          </button>
        </div>
      </div>
    </div>

    <p class="text-muted small mt-2">You can select up to {{ maxSelectable }} tickets.</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  seats: {
    type: Array,
    default: () => [],
  },
  selected: {
    type: Array,
    default: () => [],
  },
  maxSelectable: {
    type: Number,
    default: 4,
  },
})

const emit = defineEmits(['update:selected', 'limit-hit'])

const rows = computed(() => {
  const grouped = {}
  props.seats.forEach((seat) => {
    if (!grouped[seat.row]) grouped[seat.row] = []
    grouped[seat.row].push(seat)
  })
  return Object.keys(grouped)
    .map((rowNumber) => ({
      rowNumber: Number(rowNumber),
      seats: grouped[rowNumber].sort((a, b) => a.col - b.col),
    }))
    .sort((a, b) => a.rowNumber - b.rowNumber)
})

const typeClassMap = {
  1: 'vip',
  2: 'standard',
  3: 'economy',
}

function seatClasses(seat) {
  return {
    [`seat-${typeClassMap[seat.type] || 'standard'}`]: true,
    'seat-selected': props.selected.includes(seat.id),
    'seat-reserved': seat.is_reserved,
  }
}

function isDisabled(seatId) {
  return !props.selected.includes(seatId) && props.selected.length >= props.maxSelectable
}

function toggleSeat(seatId) {
  if (props.selected.includes(seatId)) {
    emit(
      'update:selected',
      props.selected.filter((id) => id !== seatId)
    )
    return
  }

  if (props.selected.length >= props.maxSelectable) {
    emit('limit-hit')
    return
  }

  emit('update:selected', [...props.selected, seatId])
}
</script>

<style scoped>
.seat-grid {
  border: 1px solid #e5e5e5;
  padding: 16px;
  border-radius: 8px;
  background: #fff;
}

.grid-wrapper {
  max-height: 420px;
  overflow: auto;
  padding: 8px;
  border: 1px dashed #e5e5e5;
  border-radius: 6px;
}

.seat-row-label {
  width: 28px;
  text-align: right;
  font-weight: 600;
}

.seat {
  min-width: 70px;
  min-height: 38px;
  border-radius: 6px;
  border: 1px solid #d0d0d0;
  color: #222;
  transition: transform 0.1s ease-in-out, box-shadow 0.1s ease-in-out;
}

.seat:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.seat:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.seat-selected {
  outline: 2px solid #0d6efd;
  box-shadow: 0 0 0 2px rgba(13, 110, 253, 0.25);
}

.seat-reserved {
  background: #f1f3f5 !important;
  color: #6c757d;
}

.seat-vip {
  background: #ffe8cc;
}

.seat-standard {
  background: #e7f5ff;
}

.seat-economy {
  background: #e6fcf5;
}

.bg-seat-vip {
  background: #ff922b !important;
}

.bg-seat-standard {
  background: #228be6 !important;
}

.bg-seat-economy {
  background: #0ca678 !important;
}
</style>
