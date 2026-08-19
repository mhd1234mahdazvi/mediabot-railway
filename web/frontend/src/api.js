const BASE = '/api'

function token() { return localStorage.getItem('token') }

async function req(method, path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token() ? { Authorization: `Bearer ${token()}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (res.status === 401) { localStorage.removeItem('token'); window.location.reload() }
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const api = {
  login: (username, password) => req('POST', '/auth/login', { username, password }),
  stats: () => req('GET', '/stats'),
  botStatus: () => req('GET', '/stats/bot-status'),
  pause: () => req('POST', '/stats/bot-pause'),
  resume: () => req('POST', '/stats/bot-resume'),
  users: () => req('GET', '/users'),
  addUser: (data) => req('POST', '/users', data),
  removeUser: (id) => req('DELETE', `/users/${id}`),
  banUser: (id, message) => req('POST', `/users/${id}/ban`, { message }),
  unbanUser: (id) => req('POST', `/users/${id}/unban`),
  setLimits: (id, data) => req('PUT', `/users/${id}/limits`, data),
  logs: (params) => req('GET', `/logs?${new URLSearchParams(params)}`),
  clearLogs: () => req('DELETE', '/logs'),
  links: (params) => req('GET', `/links?${new URLSearchParams(params)}`),
  platforms: () => req('GET', '/settings/platforms'),
  togglePlatform: (name) => req('POST', `/settings/platforms/${name}/toggle`),
  getDefaults: () => req('GET', '/settings/defaults'),
  setDefaults: (data) => req('PUT', '/settings/defaults', data),
  bots: () => req('GET', '/bots'),
  addBot: (data) => req('POST', '/bots', data),
  removeBot: (id) => req('DELETE', `/bots/${id}`),
  toggleBot: (id) => req('POST', `/bots/${id}/toggle`),
}
