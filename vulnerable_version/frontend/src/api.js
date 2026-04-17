const BASE_URL = 'http://127.0.0.1:8000/api'

export function getCurrentUser() {
  const raw = localStorage.getItem('admission_user')
  return raw ? JSON.parse(raw) : null
}

export function saveCurrentUser(user) {
  localStorage.setItem('admission_user', JSON.stringify(user))
}

export function clearCurrentUser() {
  localStorage.removeItem('admission_user')
}

export async function request(path, options = {}) {
  const user = getCurrentUser()
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  }

  if (user?.role) {
    headers['X-Role'] = user.role
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers
  })

  return response.json()
}
