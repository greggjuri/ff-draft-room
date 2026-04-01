import './PlayerRow.css'

export default function PlayerRow({
  player, position, isFirst, isLast, isDraft, draftStatus, onStatusClick,
  onMoveUp, onMoveDown, onNameClick, onDeleteClick,
}) {
  const nameLabel = player.notes ? `${player.name} 📝` : player.name

  const tierClass = player.tier % 2 === 0 ? 'tier-even' : 'tier-odd'
  const statusClass = isDraft ? `status-${draftStatus}` : ''
  const nameClasses = `player-name-btn ${tierClass} ${statusClass}`.trim()

  if (isDraft) {
    return (
      <div className="player-row draft-row">
        <span
          className={`draft-dot status-${draftStatus}`}
          onClick={onStatusClick}
          title="Click to cycle: undrafted → mine → other"
        />
        <span className="player-rank">{player.position_rank}</span>
        <span className={nameClasses}>{nameLabel}</span>
        <span className="player-team">{player.team}</span>
      </div>
    )
  }

  return (
    <div className="player-row">
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

      <button className={nameClasses} onClick={onNameClick}>
        {nameLabel}
      </button>

      <span className="player-team">{player.team}</span>

      <button
        className="control-btn delete-btn"
        onClick={onDeleteClick}
        title="Delete"
      >
        ×
      </button>
    </div>
  )
}
