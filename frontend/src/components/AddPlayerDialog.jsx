import { useRef, useEffect, useState } from 'react'

export default function AddPlayerDialog({ isOpen, position, tier, onAdd, onClose }) {
  const dialogRef = useRef(null)
  const [name, setName] = useState('')
  const [team, setTeam] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (isOpen) {
      setName('')
      setTeam('')
      setError('')
      dialogRef.current?.showModal()
    } else {
      dialogRef.current?.close()
    }
  }, [isOpen])

  const handleAdd = async () => {
    if (!name.trim() || !team.trim()) {
      setError('Name and team are required')
      return
    }
    try {
      await onAdd(position, name.trim(), team.trim().toUpperCase(), tier)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <dialog ref={dialogRef} onClose={onClose}>
      <div className="dialog-header">Add Player</div>
      <div style={{ color: 'var(--text-muted)', marginBottom: 12, fontSize: 11 }}>
        {position} · Tier {tier}
      </div>
      {error && <div className="dialog-error">{error}</div>}
      <input
        className="dialog-input"
        placeholder="Player name"
        value={name}
        onChange={e => setName(e.target.value)}
      />
      <input
        className="dialog-input"
        placeholder="Team (e.g. BUF)"
        value={team}
        maxLength={4}
        onChange={e => setTeam(e.target.value)}
      />
      <div className="dialog-buttons">
        <button className="btn-primary" onClick={handleAdd}>Add</button>
        <button className="btn-cancel" onClick={onClose}>Cancel</button>
      </div>
    </dialog>
  )
}
