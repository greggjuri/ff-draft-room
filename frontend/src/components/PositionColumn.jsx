import TierGroup from './TierGroup'
import './PositionColumn.css'

export default function PositionColumn({
  position, players, onReorder, onNotesOpen, onAddOpen, onDeleteOpen,
}) {
  // Group players by tier
  const tierGroups = {}
  for (const p of players) {
    if (!tierGroups[p.tier]) tierGroups[p.tier] = []
    tierGroups[p.tier].push(p)
  }
  const tierNums = Object.keys(tierGroups).map(Number).sort((a, b) => a - b)

  const lastRank = players.length > 0
    ? Math.max(...players.map(p => p.position_rank))
    : 0

  return (
    <div className="position-column">
      <div className="column-header">
        <span className="column-position">{position}</span>
        <span className="column-count">{players.length} players</span>
      </div>

      {tierNums.map(tierNum => (
        <TierGroup
          key={tierNum}
          position={position}
          tierNum={tierNum}
          players={tierGroups[tierNum]}
          lastRank={lastRank}
          onReorder={onReorder}
          onNotesOpen={onNotesOpen}
          onAddOpen={onAddOpen}
          onDeleteOpen={onDeleteOpen}
        />
      ))}

      {players.length === 0 && (
        <div className="empty-column">No players</div>
      )}
    </div>
  )
}
