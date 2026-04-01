import PlayerRow from './PlayerRow'
import './TierGroup.css'

export default function TierGroup({
  position, tierNum, players, lastRank, isDraft, getDraftStatus, onStatusClick,
  onReorder, onNotesOpen, onAddOpen, onDeleteOpen,
}) {
  const tierClass = tierNum % 2 === 0 ? 'tier-even' : 'tier-odd'

  return (
    <div className="tier-group">
      <div className={`tier-header ${tierClass}`}>
        — TIER {tierNum} —
      </div>

      {players.map(player => (
        <PlayerRow
          key={player.position_rank}
          player={player}
          position={position}
          isFirst={player.position_rank === 1}
          isLast={player.position_rank === lastRank}
          isDraft={isDraft}
          draftStatus={isDraft ? getDraftStatus(position, player.position_rank) : 'undrafted'}
          onStatusClick={() => onStatusClick(position, player.position_rank)}
          onMoveUp={() => onReorder(position, player.position_rank - 1, player.position_rank)}
          onMoveDown={() => onReorder(position, player.position_rank, player.position_rank + 1)}
          onNameClick={() => !isDraft && onNotesOpen(player, position)}
          onDeleteClick={() => onDeleteOpen(player, position)}
        />
      ))}

      {!isDraft && (
        <button
          className="add-tier-btn"
          onClick={() => onAddOpen(position, tierNum)}
        >
          + {position} · Tier {tierNum}
        </button>
      )}
    </div>
  )
}
