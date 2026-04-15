import { useRef, useEffect, useState } from 'react'
import { getProfiles, renameProfile, deleteProfileApi } from '../api/rankings'

export default function LoadDialog({
  isOpen, dirty, activeProfile, onLoad, onProfileRenamed, onProfileDeleted, onClose,
}) {
  const dialogRef = useRef(null)
  const [profiles, setProfiles] = useState([])
  const [loading, setLoading] = useState(false)

  // Rename state
  const [renamingProfile, setRenamingProfile] = useState(null)
  const [renameValue, setRenameValue] = useState('')
  const [renameError, setRenameError] = useState('')

  // Delete state
  const [deletingProfile, setDeletingProfile] = useState(null)

  const renameInputRef = useRef(null)

  function refreshProfiles() {
    return getProfiles()
      .then(setProfiles)
      .catch(() => setProfiles([]))
  }

  useEffect(() => {
    if (isOpen) {
      dialogRef.current?.showModal()
      setLoading(true)
      setRenamingProfile(null)
      setDeletingProfile(null)
      refreshProfiles().finally(() => setLoading(false))
    } else {
      dialogRef.current?.close()
    }
  }, [isOpen])

  useEffect(() => {
    if (renamingProfile && renameInputRef.current) {
      renameInputRef.current.focus()
      renameInputRef.current.select()
    }
  }, [renamingProfile])

  const handleLoad = (name) => {
    if (dirty && !window.confirm('Unsaved changes will be lost. Continue?')) {
      return
    }
    onLoad(name)
  }

  const startRename = (name) => {
    setDeletingProfile(null)
    setRenamingProfile(name)
    setRenameValue(name)
    setRenameError('')
  }

  const cancelRename = () => {
    setRenamingProfile(null)
    setRenameError('')
  }

  const handleRename = async (oldName) => {
    setRenameError('')
    try {
      await renameProfile(oldName, renameValue)
      if (activeProfile === oldName) onProfileRenamed(renameValue)
      setRenamingProfile(null)
      await refreshProfiles()
    } catch (err) {
      setRenameError(err.message || 'Rename failed')
    }
  }

  const startDelete = (name) => {
    setRenamingProfile(null)
    setRenameError('')
    setDeletingProfile(name)
  }

  const handleDeleteConfirm = async (name) => {
    try {
      await deleteProfileApi(name)
      if (activeProfile === name) onProfileDeleted()
      setDeletingProfile(null)
      await refreshProfiles()
    } catch {
      setDeletingProfile(null)
    }
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
      {!loading && profiles.map(name => {
        const isActive = activeProfile === name

        // Delete confirm state
        if (deletingProfile === name) {
          return (
            <div key={name} className="load-profile-row">
              <span style={{ color: 'var(--danger)', fontSize: 11 }}>
                Delete &ldquo;{name}&rdquo;?
              </span>
              <div className="load-profile-actions">
                <button className="btn-danger" style={{ fontSize: 10, padding: '3px 8px' }}
                  onClick={() => handleDeleteConfirm(name)}>Confirm</button>
                <button className="btn-cancel" style={{ fontSize: 10, padding: '3px 8px' }}
                  onClick={() => setDeletingProfile(null)}>Cancel</button>
              </div>
            </div>
          )
        }

        // Rename input state
        if (renamingProfile === name) {
          return (
            <div key={name} className="load-profile-row" style={{ flexDirection: 'column', alignItems: 'stretch', gap: 4 }}>
              <div style={{ display: 'flex', gap: 6 }}>
                <input
                  ref={renameInputRef}
                  className="dialog-input"
                  style={{ marginBottom: 0, flex: 1 }}
                  value={renameValue}
                  onChange={e => setRenameValue(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter') handleRename(name)
                    if (e.key === 'Escape') cancelRename()
                  }}
                />
                <button className="btn-primary" style={{ fontSize: 10, padding: '3px 8px' }}
                  onClick={() => handleRename(name)}>Save</button>
                <button className="btn-cancel" style={{ fontSize: 10, padding: '3px 8px' }}
                  onClick={cancelRename}>Cancel</button>
              </div>
              {renameError && (
                <span className="dialog-error" style={{ fontSize: 10 }}>{renameError}</span>
              )}
            </div>
          )
        }

        // Normal row
        return (
          <div key={name} className="load-profile-row">
            <span>
              {name}
              {isActive && <span style={{ color: 'var(--accent)', fontSize: 10, marginLeft: 6 }}>●</span>}
            </span>
            <div className="load-profile-actions">
              <button className="btn-primary" style={{ fontSize: 10, padding: '3px 8px' }}
                onClick={() => handleLoad(name)}>Load</button>
              <button className="btn-cancel" style={{ fontSize: 10, padding: '3px 8px' }}
                onClick={() => startRename(name)}>Rename</button>
              <button className="btn-cancel" style={{ fontSize: 10, padding: '3px 8px', color: 'var(--danger)' }}
                onClick={() => startDelete(name)}>Delete</button>
            </div>
          </div>
        )
      })}
      <div className="dialog-buttons" style={{ marginTop: 16 }}>
        <button className="btn-cancel" onClick={onClose}>Close</button>
      </div>
    </dialog>
  )
}
