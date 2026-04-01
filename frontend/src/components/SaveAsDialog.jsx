import { useRef, useEffect, useState } from 'react'

export default function SaveAsDialog({ isOpen, onSave, onClose }) {
  const dialogRef = useRef(null)
  const inputRef = useRef(null)
  const [name, setName] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (isOpen) {
      setName('')
      setError('')
      dialogRef.current?.showModal()
      setTimeout(() => inputRef.current?.focus(), 50)
    } else {
      dialogRef.current?.close()
    }
  }, [isOpen])

  const handleSave = async () => {
    if (!name.trim()) {
      setError('Profile name is required')
      return
    }
    try {
      await onSave(name.trim())
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <dialog ref={dialogRef} onClose={onClose}>
      <div className="dialog-header">Save Rankings As</div>
      {error && <div className="dialog-error">{error}</div>}
      <input
        ref={inputRef}
        className="dialog-input"
        placeholder="Profile name"
        value={name}
        onChange={e => setName(e.target.value)}
        onKeyDown={e => e.key === 'Enter' && handleSave()}
      />
      <div className="dialog-buttons">
        <button className="btn-primary" onClick={handleSave}>Save</button>
        <button className="btn-cancel" onClick={onClose}>Cancel</button>
      </div>
    </dialog>
  )
}
