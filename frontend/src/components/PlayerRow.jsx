import './PlayerRow.css'

export default function PlayerRow({
  player, position, isFirst, isLast,
  onMoveUp, onMoveDown, onNameClick, onDeleteClick,
}) {
  const nameLabel = player.notes ? `${player.name} 📝` : player.name

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

      <button
        className={`player-name-btn ${player.tier % 2 === 0 ? 'tier-even' : 'tier-odd'}`}
        onClick={onNameClick}
      >
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
