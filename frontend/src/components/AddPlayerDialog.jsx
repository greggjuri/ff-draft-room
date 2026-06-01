import { useRef, useEffect, useState } from 'react'
import './AddPlayerDialog.css'

const POSITIONS = ['QB', 'RB', 'WR', 'TE']

const INITIAL = {
  name: '', team: '', position: 'QB', tier: '1',
  bye_week: '', adp: '',
  projected_points: '', risk: '', upside: '',
  outlook: '',
}

export default function AddPlayerDialog({ isOpen, onAdd, onClose }) {
  const dialogRef = useRef(null)
  const [f, setF] = useState(INITIAL)
  const [error, setError] = useState('')

  useEffect(() => {
    if (isOpen) {
      setF(INITIAL); setError('')
      dialogRef.current?.showModal()
    } else {
      dialogRef.current?.close()
    }
  }, [isOpen])

  const set = (k) => (e) => setF(prev => ({ ...prev, [k]: e.target.value }))

  const handleAdd = async () => {
    const name = f.name.trim()
    const team = f.team.trim().toUpperCase()
    const position = f.position
    const tier = parseInt(f.tier, 10)
    if (!name || !team) { setError('Name and team are required'); return }
    if (!POSITIONS.includes(position)) { setError('Pick a position'); return }
    if (!Number.isInteger(tier) || tier < 1) { setError('Tier must be ≥ 1'); return }

    const parseFloatOrNull = (s) => s.trim() === '' ? null : Number(s)
    const body = {
      name, team, tier,
      bye_week: f.bye_week.trim() === '' ? null : parseInt(f.bye_week, 10),
      adp: f.adp.trim(),
      projected_points: parseFloatOrNull(f.projected_points),
      risk: parseFloatOrNull(f.risk),
      upside: parseFloatOrNull(f.upside),
      outlook: f.outlook,
    }
    for (const k of ['bye_week', 'projected_points', 'risk', 'upside']) {
      if (body[k] !== null && Number.isNaN(body[k])) {
        setError(`${k} must be a number`); return
      }
    }

    try { await onAdd(position, body) }
    catch (err) { setError(err.message) }
  }

  return (
    <dialog ref={dialogRef} onClose={onClose} className="add-player-dialog">
      <div className="dialog-header">Add Player</div>
      {error && <div className="dialog-error">{error}</div>}

      <div className="add-grid">
        <label className="full">
          <span>Name *</span>
          <input className="dialog-input" value={f.name} onChange={set('name')} />
        </label>

        <label>
          <span>Team *</span>
          <input className="dialog-input" value={f.team} maxLength={4} onChange={set('team')} />
        </label>
        <label>
          <span>Position *</span>
          <select className="dialog-input" value={f.position} onChange={set('position')}>
            {POSITIONS.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </label>

        <label>
          <span>Tier *</span>
          <input className="dialog-input" type="number" min="1" value={f.tier} onChange={set('tier')} />
        </label>
        <label>
          <span>Bye Week</span>
          <input className="dialog-input" type="number" min="1" max="18" value={f.bye_week} onChange={set('bye_week')} />
        </label>

        <label>
          <span>ADP</span>
          <input className="dialog-input" value={f.adp} placeholder="e.g. 3.05" onChange={set('adp')} />
        </label>
        <label>
          <span>Projected Points</span>
          <input className="dialog-input" type="number" step="0.1" value={f.projected_points} onChange={set('projected_points')} />
        </label>

        <label>
          <span>Risk</span>
          <input className="dialog-input" type="number" step="0.1" min="0" max="10" value={f.risk} onChange={set('risk')} />
        </label>
        <label>
          <span>Upside</span>
          <input className="dialog-input" type="number" step="0.1" min="0" max="10" value={f.upside} onChange={set('upside')} />
        </label>

        <label className="full">
          <span>Outlook</span>
          <textarea className="dialog-input add-outlook" rows="4" value={f.outlook} onChange={set('outlook')} />
        </label>
      </div>

      <div className="dialog-buttons">
        <button className="btn-primary" onClick={handleAdd}>Add</button>
        <button className="btn-cancel" onClick={onClose}>Cancel</button>
      </div>
    </dialog>
  )
}
