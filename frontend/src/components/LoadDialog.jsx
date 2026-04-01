import { useRef, useEffect, useState } from 'react'
import { getProfiles } from '../api/rankings'

export default function LoadDialog({ isOpen, dirty, onLoad, onClose }) {
  const dialogRef = useRef(null)
  const [profiles, setProfiles] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isOpen) {
      dialogRef.current?.showModal()
      setLoading(true)
      getProfiles()
        .then(setProfiles)
        .catch(() => setProfiles([]))
        .finally(() => setLoading(false))
    } else {
      dialogRef.current?.close()
    }
  }, [isOpen])

  const handleLoad = (name) => {
    if (dirty && !window.confirm('Unsaved changes will be lost. Continue?')) {
      return
    }
    onLoad(name)
  }

  return (
    <dialog ref={dialogRef} onClose={onClose}>
      <div className="dialog-header">Load Profile</div>
      {loading && <p style={{ color: 'var(--text-muted)' }}>Loading...</p>}
      {!loading && profiles.length === 0 && (
        <p style={{ color: 'var(--text-muted)', marginBottom: 16 }}>
          No profiles saved yet.
        </p>
      )}
      {!loading && profiles.map(name => (
        <div
          key={name}
          style={{
            display: 'flex', justifyContent: 'space-between',
            alignItems: 'center', padding: '6px 0',
            borderBottom: '1px solid var(--border)',
          }}
        >
          <span>{name}</span>
          <button className="btn-primary" onClick={() => handleLoad(name)}>
            Load
          </button>
        </div>
      ))}
      <div className="dialog-buttons" style={{ marginTop: 16 }}>
        <button className="btn-cancel" onClick={onClose}>Close</button>
      </div>
    </dialog>
  )
}
