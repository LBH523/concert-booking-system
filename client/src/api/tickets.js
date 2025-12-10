import client from './client'

export async function searchEvents(params = {}) {
  const { keyword = '' } = params || {}
  const response = await client.get('/search_events', {
    params: { keyword },
  })
  return response.data
}

export async function getEventDetail(eventId) {
  const response = await client.get('/get_seats', {
    params: { event_id: eventId },
  })
  return response.data
}

export async function purchase(eventId, seatIds = []) {
  const sessionId = localStorage.getItem('session_id')
  const headers = sessionId ? { 'Session-ID': sessionId } : {}
  const response = await client.post(
    '/book_ticket',
    {
      event_id: eventId,
      seat_ids: seatIds,
    },
    { headers }
  )
  return response.data
}
