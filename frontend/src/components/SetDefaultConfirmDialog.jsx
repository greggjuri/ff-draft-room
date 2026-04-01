import { useRef, useEffect } from 'react'

export default function SetDefaultConfirmDialog({ isOpen, onConfirm, onClose }) {
  const dialogRef = useRef(null)

  useEffect(() => {
    if (isOpen) dialogRef.current?.showModal()
    else dialogRef.current?.close()
  }, [isOpen])

  return (
    <dialog ref={dialogRef} onClose={onClose}>
      <div className="dialog-header">Set as Default Baseline</div>
      <p style={{ marginBottom: 16 }}>
        Save current rankings as the baseline for future resets?
      </p>
      <div className="dialog-buttons">
        <button className="btn-primary" onClick={onConfirm}>Set as Default</button>
        <button className="btn-cancel" onClick={onClose}>Cancel</button>
      </div>
    </dialog>
  )
}
