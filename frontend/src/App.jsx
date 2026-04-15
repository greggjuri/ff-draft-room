import { useState, useEffect, useMemo } from 'react'
import { AuthProvider, useAuth } from './auth/AuthContext'
import LoginPage from './components/LoginPage'
import WarRoom from './components/WarRoom'
import {
  getPositionPlayers,
  reorderPlayers,
  addPlayer,
  deletePlayer,
  updateNotes,
  saveRankings,
  saveAs,
  loadProfileApi,
  resetRankings,
  setDefaultSeed,
} from './api/rankings'

const POSITIONS = ['QB', 'RB', 'WR', 'TE']

function reloadAllPositions(setRankings) {
  return Promise.all(
    POSITIONS.map(pos =>
      getPositionPlayers(pos).then(players => [pos, players])
    )
  ).then(results => {
    setRankings(Object.fromEntries(results))
  })
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

function AppContent() {
  const { isAuthenticated, loading: authLoading, logout } = useAuth()
  const [rankings, setRankings] = useState({ QB: [], RB: [], WR: [], TE: [] })
  const [dirty, setDirty] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [profileName, setProfileName] = useState('2026 Draft')

  // Dialog state
  const [notesDialog, setNotesDialog] = useState(null)
  const [addDialog, setAddDialog] = useState(null)
  const [deleteDialog, setDeleteDialog] = useState(null)
  const [saveAsDialog, setSaveAsDialog] = useState(false)
  const [loadDialog, setLoadDialog] = useState(false)
  const [resetDialog, setResetDialog] = useState(false)
  const [setDefaultDialog, setSetDefaultDialog] = useState(false)

  // Draft mode state
  const [mode, setMode] = useState('warroom')
  const [draftState, setDraftState] = useState({})
  const [exitDraftDialog, setExitDraftDialog] = useState(false)

  const isDraft = mode === 'draft'
  const hasPicks = Object.keys(draftState).length > 0

  const getDraftStatus = (position, rank) =>
    draftState[`${position}-${rank}`] || 'undrafted'

  const cycleDraftStatus = (position, rank) => {
    const key = `${position}-${rank}`
    const current = draftState[key] || 'undrafted'
    const next = { undrafted: 'mine', mine: 'other', other: 'undrafted' }[current]
    setDraftState(prev => {
      const updated = { ...prev, [key]: next }
      if (next === 'undrafted') delete updated[key]
      return updated
    })
  }

  const enterDraftMode = () => {
    setMode('draft')
    setDraftState({})
  }

  const exitDraftMode = () => {
    if (hasPicks) {
      setExitDraftDialog(true)
    } else {
      setMode('warroom')
      setDraftState({})
    }
  }

  const confirmExitDraft = () => {
    setMode('warroom')
    setDraftState({})
    setExitDraftDialog(false)
  }

  // Search
  const [searchQuery, setSearchQuery] = useState('')

  const searchResults = useMemo(() => {
    if (!searchQuery.trim()) return []
    const q = searchQuery.toLowerCase()
    const results = []
    for (const pos of POSITIONS) {
      const matches = rankings[pos].filter(p =>
        p.name.toLowerCase().includes(q) ||
        p.team.toLowerCase().includes(q)
      ).slice(0, 5)
      if (matches.length > 0) results.push({ position: pos, players: matches })
    }
    return results
  }, [searchQuery, rankings])

  const handleSelectResult = (position, rank) => {
    setSearchQuery('')
    const el = document.querySelector(`[data-player-id="${position}-${rank}"]`)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' })
      el.classList.add('search-highlight')
      setTimeout(() => el.classList.remove('search-highlight'), 1500)
    }
  }

  // Load all positions on mount
  useEffect(() => {
    reloadAllPositions(setRankings)
      .then(() => setLoading(false))
      .catch(() => {
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

  const handleSaveAs = async (name) => {
    const result = await saveAs(name)
    setProfileName(result.name)
    setDirty(false)
    setSaveAsDialog(false)
  }

  const handleLoad = async (name) => {
    try {
      const profile = await loadProfileApi(name)
      setProfileName(profile.name || name)
      await reloadAllPositions(setRankings)
      setDirty(false)
      setLoadDialog(false)
    } catch (err) {
      setError(err.message)
    }
  }

  const handleReset = async () => {
    try {
      await resetRankings()
      await reloadAllPositions(setRankings)
      setProfileName('2026 Draft')
      setDirty(false)
      setResetDialog(false)
    } catch (err) {
      setError(err.message)
    }
  }

  const handleSetDefault = async () => {
    try {
      await setDefaultSeed()
      setSetDefaultDialog(false)
    } catch (err) {
      setError(err.message)
    }
  }

  if (authLoading) return <div className="loading">LOADING...</div>
  if (!isAuthenticated) return <LoginPage />
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
        profileName={profileName}
        mode={mode}
        isDraft={isDraft}
        hasPicks={hasPicks}
        getDraftStatus={getDraftStatus}
        onStatusClick={cycleDraftStatus}
        onEnterDraft={enterDraftMode}
        onExitDraft={exitDraftMode}
        exitDraftDialog={exitDraftDialog}
        onConfirmExitDraft={confirmExitDraft}
        onCancelExitDraft={() => setExitDraftDialog(false)}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        searchResults={searchResults}
        onSelectResult={handleSelectResult}
        onReorder={handleReorder}
        onSave={handleSave}
        onSaveAsOpen={() => setSaveAsDialog(true)}
        onLoadOpen={() => setLoadDialog(true)}
        onResetOpen={() => setResetDialog(true)}
        onSetDefaultOpen={() => setSetDefaultDialog(true)}
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
        saveAsDialog={saveAsDialog}
        onSaveAs={handleSaveAs}
        onSaveAsClose={() => setSaveAsDialog(false)}
        loadDialog={loadDialog}
        onLoad={handleLoad}
        onLoadClose={() => setLoadDialog(false)}
        resetDialog={resetDialog}
        onReset={handleReset}
        onResetClose={() => setResetDialog(false)}
        setDefaultDialog={setDefaultDialog}
        onSetDefault={handleSetDefault}
        onSetDefaultClose={() => setSetDefaultDialog(false)}
      />
    </>
  )
}
