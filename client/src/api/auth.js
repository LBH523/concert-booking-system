import client from './client'

export async function register(username, password) {
  try {
    const response = await client.post('/register', { username, password })
    return response.data
  } catch (err) {
    return {
      status: 'error',
      message:
        err.response?.data?.message ||
        err.response?.data?.error ||
        'Registration failed, please try again later',
    }
  }
}

export async function login(username, password) {
  try {
    const response = await client.post('/login', { username, password })
    return response.data
  } catch (err) {
    return {
      status: 'error',
      message:
        err.response?.data?.message ||
        err.response?.data?.error ||
        'Login failed, please check username/password',
    }
  }
}
