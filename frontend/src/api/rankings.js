const BASE = '/api/rankings'

async function request(url, options = {}) {
  const res = await fetch(url, options)
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
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ rank_a, rank_b })
  })

export const addPlayer = (position, name, team, tier) =>
  request(`${BASE}/${position}/add`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, team, tier })
  })

export const deletePlayer = (position, rank) =>
  request(`${BASE}/${position}/${rank}`, { method: 'DELETE' })

export const updateNotes = (position, rank, notes) =>
  request(`${BASE}/${position}/${rank}/notes`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ notes })
  })

export const saveRankings = () =>
  request(`${BASE}/save`, { method: 'POST' })
