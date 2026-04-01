import { useRef, useEffect } from 'react'

export default function ResetConfirmDialog({ isOpen, onConfirm, onClose }) {
  const dialogRef = useRef(null)

  useEffect(() => {
    if (isOpen) dialogRef.current?.showModal()
    else dialogRef.current?.close()
  }, [isOpen])

  return (
    <dialog ref={dialogRef} onClose={onClose}>
      <div className="dialog-header">Reset Rankings</div>
      <p style={{ marginBottom: 8 }}>
        Reset to your saved default baseline?
      </p>
      <p style={{ color: 'var(--text-muted)', fontSize: 11, marginBottom: 8 }}>
        If no baseline is set, rankings will be re-seeded from 2025 CSV data.
      </p>
      <p style={{ color: 'var(--danger)', fontSize: 11, marginBottom: 16 }}>
        This cannot be undone.
      </p>
      <div className="dialog-buttons">
        <button className="btn-danger" onClick={onConfirm}>Reset</button>
        <button className="btn-cancel" onClick={onClose}>Cancel</button>
      </div>
    </dialog>
  )
}
