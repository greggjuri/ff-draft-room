import { useEffect, useRef } from 'react'
import './TagPicker.css'

const TAGS = [
  { key: 'heart',   label: '❤',  title: 'Love'     },
  { key: 'fire',    label: '🔥', title: 'Breakout'  },
  { key: 'gem',     label: '💎', title: 'Sleeper'   },
  { key: 'warning', label: '⚠',  title: 'Risky'     },
  { key: 'cross',   label: '✚',  title: 'Hurt',  className: 'tag-cross' },
  { key: 'skull',   label: '☠',  title: 'Avoid'     },
  { key: 'flag',    label: '🚩', title: 'Red flag'  },
]

export default function TagPicker({ activeTag, position, onSelect, onClose }) {
  const ref = useRef(null)

  useEffect(() => {
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) onClose()
    }
    function handleKey(e) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('mousedown', handleClick)
    document.addEventListener('keydown', handleKey)
    return () => {
      document.removeEventListener('mousedown', handleClick)
      document.removeEventListener('keydown', handleKey)
    }
  }, [onClose])

  const x = Math.min(position.x, window.innerWidth - 280)
  const y = Math.min(position.y + 8, window.innerHeight - 60)

  function handleSelect(key) {
    const newTag = key === activeTag ? '' : key
    onSelect(newTag)
  }

  return (
    <div
      ref={ref}
      className="tag-picker"
      style={{ left: x, top: y }}
    >
      {TAGS.map(tag => (
        <button
          key={tag.key}
          className={`tag-btn ${tag.className || ''} ${activeTag === tag.key ? 'active' : ''}`}
          title={tag.title}
          onClick={() => handleSelect(tag.key)}
        >
          {tag.label}
        </button>
      ))}
    </div>
  )
}
