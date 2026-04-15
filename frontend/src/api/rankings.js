import { getToken } from '../auth/cognito'

const BASE = '/api/rankings'

async function authHeaders() {
  const token = await getToken()
  const headers = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`
  return headers
}

async function request(url, options = {}) {
  const headers = await authHeaders()
  const res = await fetch(url, {
    ...options,
    headers: { ...headers, ...options.headers },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed: ${res.status}`)
  }
  return res.json()
}

export const getPositionPlayers = (position) =>
  request(`${BASE}/${position}`)

export const reorderPlayers = (position, rank_a, rank_b) =>
  request(`${BASE}/${position}/reorder`, {
    method: 'POST',
    body: JSON.stringify({ rank_a, rank_b })
  })

export const addPlayer = (position, name, team, tier) =>
  request(`${BASE}/${position}/add`, {
    method: 'POST',
    body: JSON.stringify({ name, team, tier })
  })

export const deletePlayer = (position, rank) =>
  request(`${BASE}/${position}/${rank}`, { method: 'DELETE' })

export const updateNotes = (position, rank, notes) =>
  request(`${BASE}/${position}/${rank}/notes`, {
    method: 'PUT',
    body: JSON.stringify({ notes })
  })

export const saveRankings = () =>
  request(`${BASE}/save`, { method: 'POST' })

export const getProfiles = () =>
  request(`${BASE}/profiles`)

export const saveAs = (name) =>
  request(`${BASE}/save-as`, {
    method: 'POST',
    body: JSON.stringify({ name })
  })

export const loadProfileApi = (name) =>
  request(`${BASE}/load`, {
    method: 'POST',
    body: JSON.stringify({ name })
  })

export const resetRankings = () =>
  request(`${BASE}/reset`, { method: 'POST' })

export const setDefaultSeed = () =>
  request(`${BASE}/set-default`, { method: 'POST' })
