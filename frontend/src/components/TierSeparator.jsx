import { useRef, useCallback } from 'react'
import './TierSeparator.css'

export default function TierSeparator({
  position, upperTier, lowerTier,
  upperCount, lowerCount, rowHeight,
  onBoundaryMove, upperPlayers, lowerPlayers,
}) {
  const dragRef = useRef(null)
  const isUpdatingRef = useRef(0)

  const trackUpdate = (maybePromise) => {
    if (!maybePromise || typeof maybePromise.then !== 'function') return
    isUpdatingRef.current += 1
    const clear = () => { isUpdatingRef.current -= 1 }
    maybePromise.then(clear, clear)
  }

  const handleSnap = useCallback((direction) => {
    if (direction === 'down' && lowerCount > 1 && lowerPlayers.length > 0) {
      trackUpdate(onBoundaryMove(position, lowerPlayers[0].position_rank, upperTier))
    } else if (direction === 'up' && upperCount > 1 && upperPlayers.length > 0) {
      trackUpdate(onBoundaryMove(
        position,
        upperPlayers[upperPlayers.length - 1].position_rank,
        lowerTier,
      ))
    }
  }, [position, upperTier, lowerTier, upperCount, lowerCount,
      upperPlayers, lowerPlayers, onBoundaryMove])

  const startDrag = useCallback((startY) => {
    const state = { accum: 0 }
    dragRef.current = state

    const onMove = (clientY) => {
      const delta = clientY - startY
      const totalAccum = state.accum + delta
      startY = clientY

      state.accum = totalAccum
      const step = rowHeight || 29

      while (state.accum >= step) {
        handleSnap('down')
        state.accum -= step
      }
      while (state.accum <= -step) {
        handleSnap('up')
        state.accum += step
      }
    }

    const onEnd = () => {
      dragRef.current = null
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', onEnd)
      document.removeEventListener('touchmove', handleTouchMove)
      document.removeEventListener('touchend', onEnd)
    }

    const handleMouseMove = (e) => onMove(e.clientY)
    const handleTouchMove = (e) => {
      if (e.touches.length > 0) onMove(e.touches[0].clientY)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', onEnd)
    document.addEventListener('touchmove', handleTouchMove, { passive: true })
    document.addEventListener('touchend', onEnd)
  }, [rowHeight, handleSnap])

  const onMouseDown = (e) => {
    if (isUpdatingRef.current > 0) return
    e.preventDefault()
    startDrag(e.clientY)
  }

  const onTouchStart = (e) => {
    if (isUpdatingRef.current > 0) return
    if (e.touches.length > 0) startDrag(e.touches[0].clientY)
  }

  return (
    <div
      className="tier-separator"
      onMouseDown={onMouseDown}
      onTouchStart={onTouchStart}
    >
      <div className="tier-separator-line" />
      <span className="tier-separator-grip">⠿</span>
      <div className="tier-separator-line" />
    </div>
  )
}
