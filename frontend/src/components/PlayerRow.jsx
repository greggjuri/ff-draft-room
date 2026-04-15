import { forwardRef } from 'react'
import { getLogoUrl } from '../utils/teamLogos'
import { getTeamColor } from '../utils/teamColors'
import './PlayerRow.css'

const TIER_BASES = { odd: '#1A3A5C', even: '#2A5A8C' }
const DRAFT_BASES = { mine: '#1A7A3A', other: '#6B2FA0' }

function buildGradient(base, teamHex) {
  return `linear-gradient(to right, ${base} 0%, ${base} 45%, color-mix(in srgb, ${teamHex} 22%, ${base}) 100%)`
}

const PlayerRow = forwardRef(function PlayerRow({
  player, position, isFirst, isLast, isDraft, draftStatus, onStatusClick,
  onMoveUp, onMoveDown, onNameClick, onDeleteClick,
}, ref) {
  const nameLabel = player.notes ? `${player.name} 📝` : player.name

  const tierClass = player.tier % 2 === 0 ? 'tier-even' : 'tier-odd'
  const statusClass = isDraft ? `status-${draftStatus}` : ''
  const nameClasses = `player-name-btn ${tierClass} ${statusClass}`.trim()

  const teamColor = getTeamColor(player.team)
  let nameStyle
  if (teamColor) {
    const tierBase = player.tier % 2 === 0 ? TIER_BASES.even : TIER_BASES.odd
    const draftBase = DRAFT_BASES[draftStatus] ?? null
    const base = draftBase ?? tierBase
    nameStyle = { background: buildGradient(base, teamColor) }
  }

  const logoUrl = getLogoUrl(player.team)
  const logoEl = logoUrl ? (
    <img
      src={logoUrl}
      alt={player.team}
      className="player-team-logo"
      onError={e => { e.currentTarget.style.display = 'none' }}
    />
  ) : null

  if (isDraft) {
    return (
      <div ref={ref} className="player-row draft-row" data-player-id={`${position}-${player.position_rank}`}>
        <span
          className={`draft-dot status-${draftStatus}`}
          onClick={onStatusClick}
          title="Click to cycle: undrafted → mine → other"
        />
        <span className="player-rank">{player.position_rank}</span>
        <span className={nameClasses} style={nameStyle}>
          <span className="player-name-text">{nameLabel}</span>
          {logoEl}
        </span>
      </div>
    )
  }

  return (
    <div ref={ref} className="player-row" data-player-id={`${position}-${player.position_rank}`}>
      <button
        className="control-btn"
        disabled={isFirst}
        onClick={onMoveUp}
        title="Move up"
      >
        ▲
      </button>

      <button
        className="control-btn"
        disabled={isLast}
        onClick={onMoveDown}
        title="Move down"
      >
        ▼
      </button>

      <span className="player-rank">{player.position_rank}</span>

      <button className={nameClasses} style={nameStyle} onClick={onNameClick}>
        <span className="player-name-text">{nameLabel}</span>
        {logoEl}
      </button>

      <button
        className="control-btn delete-btn"
        onClick={onDeleteClick}
        title="Delete"
      >
        ×
      </button>
    </div>
  )
})

export default PlayerRow
