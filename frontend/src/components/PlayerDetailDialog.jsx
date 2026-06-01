import { useRef, useEffect, useState } from 'react'
import './PlayerDetailDialog.css'

export default function PlayerDetailDialog({ isOpen, player, onSave, onClose }) {
  const dialogRef = useRef(null)
  const [notes, setNotes] = useState(player?.notes ?? '')

  useEffect(() => {
    if (isOpen) dialogRef.current?.showModal()
    else dialogRef.current?.close()
  }, [isOpen])

  // Reset textarea when a different player is selected
  useEffect(() => {
    if (player) setNotes(player.notes ?? '')
  }, [player])

  if (!player) return null

  // Build metadata segments, omitting empties. ADP is a string ("",
  // "3.05"); projected_points / bye_week are number or null.
  const segments = []
  if (player.projected_points != null) {
    segments.push(`Proj ${player.projected_points}`)
  }
  if (player.adp) {
    segments.push(`ADP ${player.adp}`)
  }
  if (player.bye_week != null) {
    segments.push(`Bye ${player.bye_week}`)
  }

  return (
    <dialog ref={dialogRef} onClose={onClose} className="player-detail-dialog">
      <div className="pdd-header">
        <span className="pdd-title">
          📋 {player.name} · {player.position} · {player.team}
        </span>
        <button className="pdd-close" onClick={onClose} aria-label="Close">✕</button>
      </div>

      <div className="pdd-body">
        <section className="pdd-left">
          {segments.length > 0 && (
            <div className="pdd-meta">{segments.join(' · ')}</div>
          )}
          {player.outlook
            ? <div className="pdd-outlook">{player.outlook}</div>
            : <div className="pdd-outlook-empty">No outlook available.</div>}
        </section>

        <section className="pdd-right">
          <textarea
            className="dialog-textarea pdd-notes"
            value={notes}
            onChange={e => setNotes(e.target.value)}
            placeholder="Add scouting notes..."
          />
          <div className="dialog-buttons pdd-buttons">
            <button className="btn-primary" onClick={() => onSave(notes)}>Save</button>
            <button className="btn-cancel" onClick={onClose}>Close</button>
          </div>
        </section>
      </div>
    </dialog>
  )
}
