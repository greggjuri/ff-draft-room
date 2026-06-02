import { useEffect, useRef, useState } from 'react'
import './ContextMenu.css'

const TAGS = [
  { key: 'heart',   icon: '❤',  label: 'Love'     },
  { key: 'fire',    icon: '🔥', label: 'Breakout' },
  { key: 'gem',     icon: '💎', label: 'Sleeper'  },
  { key: 'warning', icon: '⚠',  label: 'Risky'    },
  { key: 'cross',   icon: '✚',  label: 'Hurt'     },
  { key: 'skull',   icon: '☠',  label: 'Avoid'    },
  { key: 'flag',    icon: '🚩', label: 'Red flag' },
]

export default function ContextMenu({
  activeTag, position, onTagSelect, onDelete, onClose,
}) {
  const ref = useRef(null)
  const [openSubmenu, setOpenSubmenu] = useState(null)  // null | 'tags' | 'edit'

  useEffect(() => {
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) onClose()
    }
    function handleKey(e) { if (e.key === 'Escape') onClose() }
    document.addEventListener('mousedown', handleClick)
    document.addEventListener('keydown', handleKey)
    return () => {
      document.removeEventListener('mousedown', handleClick)
      document.removeEventListener('keydown', handleKey)
    }
  }, [onClose])

  const x = Math.min(position.x, window.innerWidth - 260)
  const y = Math.min(position.y + 8, window.innerHeight - 80)

  const handleTagClick = (key) => {
    const newTag = key === activeTag ? '' : key
    onTagSelect(newTag)
  }

  const toggleSubmenu = (k) => (e) => {
    e.stopPropagation()
    setOpenSubmenu(prev => prev === k ? null : k)
  }

  const renderParent = (key, label) => {
    const isOpen = openSubmenu === key
    return (
      <button
        type="button"
        className={`cm-item ${isOpen ? 'open' : ''}`}
        onClick={toggleSubmenu(key)}
      >
        <span>{label}</span>
        <span className="cm-arrow">{isOpen ? '▾' : '▸'}</span>
      </button>
    )
  }

  return (
    <div ref={ref} className="context-menu" style={{ left: x, top: y }}>
      <div className={`cm-item-wrapper ${openSubmenu === 'tags' ? 'open' : ''}`}>
        {renderParent('tags', 'Tags')}
        <div className="cm-submenu cm-submenu-tags">
          {TAGS.map(t => (
            <button
              key={t.key}
              type="button"
              className={`cm-tag-row ${activeTag === t.key ? 'active' : ''}`}
              onClick={(e) => { e.stopPropagation(); handleTagClick(t.key) }}
            >
              <span className={`cm-tag-icon tag-${t.key}`}>{t.icon}</span>
              <span className="cm-tag-label">{t.label}</span>
            </button>
          ))}
        </div>
      </div>

      <div className={`cm-item-wrapper ${openSubmenu === 'edit' ? 'open' : ''}`}>
        {renderParent('edit', 'Edit')}
        <div className="cm-submenu cm-submenu-edit">
          <button
            type="button"
            className="cm-edit-row cm-delete"
            onClick={(e) => { e.stopPropagation(); onDelete() }}
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  )
}
