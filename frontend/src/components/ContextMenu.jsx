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
  const [openSub, setOpenSub] = useState(null)

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

  const toggleSub = (k) => (e) => {
    e.stopPropagation()
    setOpenSub(prev => prev === k ? null : k)
  }

  return (
    <div ref={ref} className="context-menu" style={{ left: x, top: y }}>
      <div
        className={`cm-item ${openSub === 'tags' ? 'open' : ''}`}
        onClick={toggleSub('tags')}
      >
        <span>Tags</span><span className="cm-arrow">▸</span>
        <div className="cm-submenu cm-submenu-tags">
          {TAGS.map(t => (
            <button
              key={t.key}
              className={`cm-tag-row ${activeTag === t.key ? 'active' : ''}`}
              onClick={(e) => { e.stopPropagation(); handleTagClick(t.key) }}
            >
              <span className={`cm-tag-icon tag-${t.key}`}>{t.icon}</span>
              <span className="cm-tag-label">{t.label}</span>
            </button>
          ))}
        </div>
      </div>

      <div
        className={`cm-item ${openSub === 'edit' ? 'open' : ''}`}
        onClick={toggleSub('edit')}
      >
        <span>Edit</span><span className="cm-arrow">▸</span>
        <div className="cm-submenu cm-submenu-edit">
          <button
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
