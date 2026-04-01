import { useState, useRef, useEffect } from 'react'
import './SearchBar.css'

function highlightMatch(name, query) {
  if (!query) return name
  const idx = name.toLowerCase().indexOf(query.toLowerCase())
  if (idx === -1) return name
  return (
    <>
      {name.slice(0, idx)}
      <strong>{name.slice(idx, idx + query.length)}</strong>
      {name.slice(idx + query.length)}
    </>
  )
}

export default function SearchBar({
  query, onChange, results, onSelectResult, isDraft, getDraftStatus,
}) {
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef(null)

  // Outside click closes dropdown (mousedown on container ref)
  useEffect(() => {
    const handleMouseDown = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleMouseDown)
    return () => document.removeEventListener('mousedown', handleMouseDown)
  }, [])

  // Open dropdown when query has results
  useEffect(() => {
    setIsOpen(query.trim().length > 0)
  }, [query])

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      onChange('')
      setIsOpen(false)
    }
  }

  const handleSelect = (position, rank) => {
    setIsOpen(false)
    onSelectResult(position, rank)
  }

  return (
    <div className="search-container" ref={containerRef}>
      <span className="search-icon">🔍</span>
      <input
        className="search-input"
        type="text"
        placeholder="Search players..."
        value={query}
        onChange={e => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        onFocus={() => query.trim() && setIsOpen(true)}
      />
      {query && (
        <button className="search-clear" onClick={() => onChange('')}>×</button>
      )}

      {isOpen && (
        <div className="search-dropdown">
          {results.length === 0 && query.trim() && (
            <div className="search-no-results">No players found</div>
          )}
          {results.map(({ position, players }) => (
            <div key={position}>
              <div className="search-position-header">{position}</div>
              {players.map(player => {
                const status = isDraft ? getDraftStatus(position, player.position_rank) : null
                const dotClass = status ? `draft-dot status-${status}` : 'search-dot-muted'
                return (
                  <div
                    key={`${position}-${player.position_rank}`}
                    className="search-result-row"
                    onClick={() => handleSelect(position, player.position_rank)}
                  >
                    <span className={dotClass} />
                    <span className="search-result-rank">{player.position_rank}</span>
                    <span className="search-result-name">
                      {highlightMatch(player.name, query)}
                    </span>
                    <span className="search-result-team">{player.team}</span>
                  </div>
                )
              })}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
