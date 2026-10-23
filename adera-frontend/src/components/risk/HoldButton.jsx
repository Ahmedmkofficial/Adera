import { useEffect, useRef, useState } from 'react'

const HOLD_MS = 1500

export default function HoldButton({ children, onComplete }) {
  const timer = useRef(null)
  const [holding, setHolding] = useState(false)

  // if the sheet closes mid-hold, don't fire later
  useEffect(() => () => clearTimeout(timer.current), [])

  function start() {
    if (timer.current) return
    setHolding(true)
    timer.current = setTimeout(() => {
      timer.current = null
      setHolding(false)
      onComplete()
    }, HOLD_MS)
  }

  function cancel() {
    clearTimeout(timer.current)
    timer.current = null
    setHolding(false)
  }

  function isActivationKey(e) {
    return e.key === 'Enter' || e.key === ' '
  }

  return (
    <button
      type="button"
      className={`rk-hold${holding ? ' is-holding' : ''}`}
      onPointerDown={start}
      onPointerUp={cancel}
      onPointerLeave={cancel}
      onPointerCancel={cancel}
      onKeyDown={(e) => {
        if (isActivationKey(e) && !e.repeat) {
          e.preventDefault()
          start()
        }
      }}
      onKeyUp={(e) => isActivationKey(e) && cancel()}
      onBlur={cancel}
      onContextMenu={(e) => e.preventDefault()}
    >
      <span>{children}</span>
      <span className="rk-hold-bar" aria-hidden="true" />
    </button>
  )
}