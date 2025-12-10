import client from './client'

export async function addEvent(formData) {
  const res = await client.post('/add_event', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

export async function editEvent(payload) {
  const res = await client.post('/edit_event', payload)
  return res.data
}

export async function deleteEvent(eventId) {
  const res = await client.post('/delete_event', { event_id: eventId })
  return res.data
}

export async function fetchAllEvents() {
  const res = await client.get('/search_events', { params: { keyword: '' } })
  return res.data
}
