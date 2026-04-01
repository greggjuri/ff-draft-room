import { useRef, useEffect } from 'react'

export default function ExitDraftConfirmDialog({ isOpen, onConfirm, onClose }) {
  const dialogRef = useRef(null)

  useEffect(() => {
    if (isOpen) dialogRef.current?.showModal()
    else dialogRef.current?.close()
  }, [isOpen])

  return (
    <dialog ref={dialogRef} onClose={onClose}>
      <div className="dialog-header">Exit Draft Mode?</div>
      <p style={{ marginBottom: 16 }}>
        All pick markings will be lost.
      </p>
      <div className="dialog-buttons">
        <button className="btn-danger" onClick={onConfirm}>Exit</button>
        <button className="btn-cancel" onClick={onClose}>Stay in Draft</button>
      </div>
    </dialog>
  )
}
