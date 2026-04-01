import { useRef, useEffect } from 'react'

export default function DeleteConfirmDialog({ isOpen, player, position, onConfirm, onClose }) {
  const dialogRef = useRef(null)

  useEffect(() => {
    if (isOpen) dialogRef.current?.showModal()
    else dialogRef.current?.close()
  }, [isOpen])

  return (
    <dialog ref={dialogRef} onClose={onClose}>
      <div className="dialog-header">Delete Player</div>
      <p style={{ marginBottom: 8 }}>
        Remove <strong>{player?.name}</strong> ({player?.team}) from {position} rankings?
      </p>
      <p style={{ color: 'var(--text-muted)', fontSize: 11, marginBottom: 16 }}>
        This cannot be undone.
      </p>
      <div className="dialog-buttons">
        <button className="btn-danger" onClick={onConfirm}>Delete</button>
        <button className="btn-cancel" onClick={onClose}>Cancel</button>
      </div>
    </dialog>
  )
}
