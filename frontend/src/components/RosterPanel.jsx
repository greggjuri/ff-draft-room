import { getLogoUrl } from '../utils/teamLogos'
import './RosterPanel.css'

const POSITIONS = ['QB', 'RB', 'WR', 'TE']

const TAG_ICONS = {
  heart:   '❤',
  fire:    '🔥',
  gem:     '💎',
  warning: '⚠',
  cross:   '✚',
  skull:   '☠',
  flag:    '🚩',
}

export default function RosterPanel({ rankings, draftState, isOpen, onToggle }) {
  const myPicks = POSITIONS.reduce((acc, pos) => {
    acc[pos] = (rankings[pos] ?? [])
      .filter(p => draftState[`${pos}-${p.position_rank}`] === 'mine')
    return acc
  }, {})

  const counts = POSITIONS.map(pos => `${pos} ${myPicks[pos].length}`).join(' · ')

  return (
    <>
      <div
        className={`roster-panel-drawer ${isOpen ? 'open' : ''}`}
      >
        {POSITIONS.map(pos => (
          <div key={pos} className={`roster-section position-${pos.toLowerCase()}`}>
            <div className="roster-section-header">
              <span className="roster-section-label">{pos}</span>
              <span className="roster-section-count"> · {myPicks[pos].length}</span>
            </div>
            {myPicks[pos].length === 0 ? (
              <div className="roster-empty">— empty —</div>
            ) : (
              myPicks[pos].map(player => {
                const logoUrl = getLogoUrl(player.team)
                return (
                  <div key={player.position_rank} className="roster-player-row">
                    {player.tag && TAG_ICONS[player.tag] && (
                      <span className={`player-tag tag-${player.tag}`}>
                        {TAG_ICONS[player.tag]}
                      </span>
                    )}
                    <span className="roster-player-name">{player.name}</span>
                    <span className="roster-player-team">{player.team}</span>
                    {logoUrl && (
                      <img
                        src={logoUrl}
                        alt={player.team}
                        className="roster-player-logo"
                        onError={e => { e.currentTarget.style.display = 'none' }}
                      />
                    )}
                  </div>
                )
              })
            )}
          </div>
        ))}
      </div>

      <div className="roster-handle" onClick={onToggle}>
        <span className="roster-handle-label">MY ROSTER</span>
        <span className="roster-handle-counts">{counts}</span>
      </div>
    </>
  )
}
