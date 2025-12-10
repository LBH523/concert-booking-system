import client from './client'

export function fetchOrders(status) {
  return client.get('/show_orders', { params: { status } })
}

export function cancelOrder(orderId) {
  return client.post('/cancel_order', null, { params: { id: orderId } })
}
