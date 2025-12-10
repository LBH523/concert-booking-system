<template>
  <div class="container py-4" style="max-width: 540px">
    <h2 class="mb-2">Login / Register</h2>
    <p class="text-muted mb-3">
      Login to book seats; registration does not auto-login, please switch back to Login after registering.
    </p>

    <div class="card shadow-sm">
      <div class="card-body">
        <form @submit.prevent="handleSubmit">
          <div class="mb-3">
            <label class="form-label" for="username">Username</label>
            <input
              id="username"
              v-model.trim="form.username"
              type="text"
              class="form-control"
              placeholder="Enter username"
              :disabled="submitting"
              required />
          </div>

          <div class="mb-3">
            <label class="form-label" for="password">Password</label>
            <input
              id="password"
              v-model.trim="form.password"
              type="password"
              class="form-control"
              placeholder="Enter password"
              autocomplete="current-password"
              :disabled="submitting"
              required />
          </div>

          <div class="d-flex justify-content-between align-items-center mb-3">
            <div class="form-check">
              <input
                id="mode-login"
                v-model="mode"
                class="form-check-input"
                type="radio"
                value="login"
                name="mode" />
              <label class="form-check-label" for="mode-login">Login</label>
            </div>
            <div class="form-check">
              <input
                id="mode-register"
                v-model="mode"
                class="form-check-input"
                type="radio"
                value="register"
                name="mode" />
              <label class="form-check-label" for="mode-register">Register</label>
            </div>
            <span class="badge bg-light text-dark">{{ modeLabel }}</span>
          </div>

          <div class="d-grid gap-2">
            <button class="btn btn-primary" type="submit" :disabled="submitting">
              {{ submitting ? 'Submitting...' : submitLabel }}
            </button>
            <button class="btn btn-outline-secondary" type="button" @click="resetForm" :disabled="submitting">
              Clear
            </button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="message" class="alert mt-3" :class="messageClass">{{ message }}</div>
    <p v-if="sessionId" class="text-success small mt-2">Session-ID: {{ sessionId }}</p>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { login, register } from '../api/auth'

const form = reactive({ username: '', password: '' })
const mode = ref('login')
const submitting = ref(false)
const message = ref('')
const messageType = ref('')
const router = useRouter()
const route = useRoute()

const sessionId = computed(() => localStorage.getItem('session_id') || '')
const isLoginMode = computed(() => mode.value === 'login')
const submitLabel = computed(() => (isLoginMode.value ? 'Login and save Session' : 'Create account'))
const modeLabel = computed(() => (isLoginMode.value ? 'Mode: Login' : 'Mode: Register'))
const messageClass = computed(() => (messageType.value === 'success' ? 'alert-success' : 'alert-danger'))

function resetForm() {
  form.username = ''
  form.password = ''
  message.value = ''
  messageType.value = ''
}

function ensureFields() {
  if (!form.username || !form.password) {
    throw new Error('Username and password are required')
  }
}

async function handleRegister() {
  const res = await register(form.username, form.password)
  if (res.status === 'success') {
    messageType.value = 'success'
    message.value = 'Registration successful, please switch to Login to continue.'
    return
  }
  if (res.status === 'fail' && res.message === 'Username already exists') {
    throw new Error('Username already exists, please choose another one')
  }
  throw new Error(res.message || 'Registration failed, please try again')
}

async function handleLogin() {
  const res = await login(form.username, form.password)
  if (res.status === 'success' && res.session_id) {
    localStorage.setItem('session_id', res.session_id)
    const adminFlag = res.is_admin !== undefined ? (res.is_admin ? '1' : '0') : '0'
    localStorage.setItem('is_admin', adminFlag)
    messageType.value = 'success'
    message.value = 'Login successful. Session saved.'
    const redirect = route.query.redirect || '/'
    router.replace(redirect)
    return
  }
  if (res.status === 'fail') {
    throw new Error(res.message === 'Invalid credentials' ? 'Invalid username or password' : res.message || 'Login failed')
  }
  throw new Error(res.message || 'Login failed, please try again')
}

async function handleSubmit() {
  submitting.value = true
  message.value = ''

  try {
    ensureFields()
    if (isLoginMode.value) {
      await handleLogin()
    } else {
      await handleRegister()
    }
  } catch (err) {
    messageType.value = 'error'
    message.value = err.response?.data?.message || err.message || 'Operation failed, please try again'
  } finally {
    submitting.value = false
  }
}
</script>
