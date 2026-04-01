import { useRef, useEffect, useState } from 'react'

export default function NotesDialog({ isOpen, player, position, onSave, onClose }) {
  const dialogRef = useRef(null)
  const [notes, setNotes] = useState(player?.notes || '')

  useEffect(() => {
    if (isOpen) dialogRef.current?.showModal()
    else dialogRef.current?.close()
  }, [isOpen])

  useEffect(() => {
    if (player) setNotes(player.notes || '')
  }, [player])

  return (
    <dialog ref={dialogRef} onClose={onClose}>
      <div className="dialog-header">
        📋 {player?.name} · {player?.team}
      </div>
      <textarea
        className="dialog-textarea"
        value={notes}
        onChange={e => setNotes(e.target.value)}
        placeholder="Add scouting notes..."
      />
      <div className="dialog-buttons">
        <button className="btn-primary" onClick={() => onSave(notes)}>Save</button>
        <button className="btn-cancel" onClick={onClose}>Close</button>
      </div>
    </dialog>
  )
}
