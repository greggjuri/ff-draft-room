import { useState, useEffect } from 'react'
import WarRoom from './components/WarRoom'
import {
  getPositionPlayers,
  reorderPlayers,
  addPlayer,
  deletePlayer,
  updateNotes,
  saveRankings,
} from './api/rankings'

const POSITIONS = ['QB', 'RB', 'WR', 'TE']

export default function App() {
  const [rankings, setRankings] = useState({ QB: [], RB: [], WR: [], TE: [] })
  const [dirty, setDirty] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Dialog state
  const [notesDialog, setNotesDialog] = useState(null)
  const [addDialog, setAddDialog] = useState(null)
  const [deleteDialog, setDeleteDialog] = useState(null)

  // Load all positions on mount
  useEffect(() => {
    Promise.all(
      POSITIONS.map(pos =>
        getPositionPlayers(pos).then(players => [pos, players])
      )
    )
      .then(results => {
        setRankings(Object.fromEntries(results))
        setLoading(false)
      })
      .catch(err => {
        setError('Cannot connect to backend at localhost:8000')
        setLoading(false)
      })
  }, [])

  const handleReorder = async (position, rankA, rankB) => {
    try {
      const updated = await reorderPlayers(position, rankA, rankB)
      setRankings(prev => ({ ...prev, [position]: updated }))
      setDirty(true)
    } catch (err) {
      setError(err.message)
    }
  }

  const handleAdd = async (position, name, team, tier) => {
    const updated = await addPlayer(position, name, team, tier)
    setRankings(prev => ({ ...prev, [position]: updated }))
    setDirty(true)
    setAddDialog(null)
  }

  const handleDelete = async (position, rank) => {
    try {
      const updated = await deletePlayer(position, rank)
      setRankings(prev => ({ ...prev, [position]: updated }))
      setDirty(true)
      setDeleteDialog(null)
    } catch (err) {
      setError(err.message)
    }
  }

  const handleNotesUpdate = async (position, rank, notes) => {
    try {
      await updateNotes(position, rank, notes)
      // Refresh position to get updated player
      const updated = await getPositionPlayers(position)
      setRankings(prev => ({ ...prev, [position]: updated }))
      setDirty(true)
      setNotesDialog(null)
    } catch (err) {
      setError(err.message)
    }
  }

  const handleSave = async () => {
    try {
      await saveRankings()
      setDirty(false)
    } catch (err) {
      setError(err.message)
    }
  }

  if (loading) return <div className="loading">LOADING...</div>

  return (
    <>
      {error && (
        <div className="error-banner">
          {error}
          <button
            onClick={() => setError(null)}
            style={{ marginLeft: 12, background: 'transparent', border: 'none', color: 'white', cursor: 'pointer' }}
          >
            ✕
          </button>
        </div>
      )}
      <WarRoom
        rankings={rankings}
        dirty={dirty}
        onReorder={handleReorder}
        onSave={handleSave}
        notesDialog={notesDialog}
        onNotesOpen={(player, position) => setNotesDialog({ player, position })}
        onNotesClose={() => setNotesDialog(null)}
        onNotesUpdate={handleNotesUpdate}
        addDialog={addDialog}
        onAddOpen={(position, tier) => setAddDialog({ position, tier })}
        onAddClose={() => setAddDialog(null)}
        onAdd={handleAdd}
        deleteDialog={deleteDialog}
        onDeleteOpen={(player, position) => setDeleteDialog({ player, position })}
        onDeleteClose={() => setDeleteDialog(null)}
        onDelete={handleDelete}
      />
    </>
  )
}
