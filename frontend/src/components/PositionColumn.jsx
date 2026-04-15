import { useRef, useEffect, useState } from 'react'
import TierGroup from './TierGroup'
import TierSeparator from './TierSeparator'
import './PositionColumn.css'

const POSITION_DEPTH = { QB: 30, RB: 50, WR: 50, TE: 30 }

export default function PositionColumn({
  position, players, isDraft, getDraftStatus, onStatusClick,
  onReorder, onNotesOpen, onAddOpen, onDeleteOpen, onTierMove,
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

  // Measure row height from first PlayerRow
  const firstRowRef = useRef(null)
  const [rowHeight, setRowHeight] = useState(29)

  useEffect(() => {
    if (firstRowRef.current) {
      const h = firstRowRef.current.getBoundingClientRect().height
      if (h > 0) setRowHeight(h)
    }
  }, [players])

  return (
    <div className={`position-column position-${position.toLowerCase()}`}>
      <div className="column-header">
        <span className="column-position">{position}</span>
        <span className="column-depth">depth · {POSITION_DEPTH[position]}</span>
      </div>

      {tierNums.map((tierNum, idx) => (
        <div key={tierNum}>
          {/* Tier separator between adjacent tiers (not before first) */}
          {idx > 0 && !isDraft && (
            <TierSeparator
              position={position}
              upperTier={tierNums[idx - 1]}
              lowerTier={tierNum}
              upperCount={tierGroups[tierNums[idx - 1]].length}
              lowerCount={tierGroups[tierNum].length}
              rowHeight={rowHeight}
              onBoundaryMove={onTierMove}
              upperPlayers={tierGroups[tierNums[idx - 1]]}
              lowerPlayers={tierGroups[tierNum]}
            />
          )}

          <TierGroup
            position={position}
            tierNum={tierNum}
            players={tierGroups[tierNum]}
            lastRank={lastRank}
            isDraft={isDraft}
            getDraftStatus={getDraftStatus}
            onStatusClick={onStatusClick}
            onReorder={onReorder}
            onNotesOpen={onNotesOpen}
            onAddOpen={onAddOpen}
            onDeleteOpen={onDeleteOpen}
            firstRowRef={idx === 0 ? firstRowRef : undefined}
          />
        </div>
      ))}

      {players.length === 0 && (
        <div className="empty-column">No players</div>
      )}
    </div>
  )
}
