const BASE_URL = 'http://127.0.0.1:8000/api'

export function getCurrentUser() {
  const raw = localStorage.getItem('admission_user')
  return raw ? JSON.parse(raw) : null
}

export function getToken() {
  return localStorage.getItem('admission_token')
}

export function saveCurrentUser(user, token) {
  localStorage.setItem('admission_user', JSON.stringify(user))
  if (token) {
    localStorage.setItem('admission_token', token)
  }
}

export function clearCurrentUser() {
  localStorage.removeItem('admission_user')
  localStorage.removeItem('admission_token')
}

export async function request(path, options = {}) {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers
  })

  return response.json()
}
