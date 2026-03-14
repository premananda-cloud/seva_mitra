/**
 * IdleOverlay.jsx
 * Full-screen overlay shown when the user has been idle.
 * Counts down remaining seconds and lets them continue or auto-logs out.
 */
import { useEffect, useRef } from 'react'

export default function IdleOverlay({ remaining, onContinue }) {
  const btnRef = useRef(null)

  // Auto-focus the "Stay" button so kiosk users can tap Enter
  useEffect(() => {
    btnRef.current?.focus()
  }, [])

  // Percentage for the countdown ring (0→100 as remaining goes 30→0)
  const pct = Math.max(0, Math.min(1, remaining / 30))
  const r = 36
  const circ = 2 * Math.PI * r
  const dash = circ * pct

  return (
    <div
      role="alertdialog"
      aria-modal="true"
      aria-label="Session timeout warning"
      className="fixed inset-0 z-[100] flex items-center justify-center bg-koisk-navy/80 backdrop-blur-md animate-fade-in"
    >
      <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-sm w-full mx-4 text-center animate-bounce-in">

        {/* Countdown ring */}
        <div className="relative w-24 h-24 mx-auto mb-5">
          <svg
            className="w-full h-full -rotate-90"
            viewBox="0 0 88 88"
            aria-hidden="true"
          >
            {/* Track */}
            <circle
              cx="44" cy="44" r={r}
              fill="none"
              stroke="#F0F4FA"
              strokeWidth="8"
            />
            {/* Progress */}
            <circle
              cx="44" cy="44" r={r}
              fill="none"
              stroke={remaining <= 10 ? '#EF4444' : '#0B6E6E'}
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={`${dash} ${circ}`}
              style={{ transition: 'stroke-dasharray 0.9s linear, stroke 0.3s' }}
            />
          </svg>
          <span className={`
            absolute inset-0 flex items-center justify-center
            font-display font-bold text-3xl
            ${remaining <= 10 ? 'text-koisk-danger' : 'text-koisk-teal'}
          `}>
            {remaining}
          </span>
        </div>

        <h2 className="heading-display text-xl mb-2">Still there?</h2>
        <p className="text-koisk-muted font-body text-sm leading-relaxed mb-6">
          You'll be logged out in{' '}
          <span className={`font-semibold ${remaining <= 10 ? 'text-koisk-danger' : 'text-koisk-navy'}`}>
            {remaining} second{remaining !== 1 ? 's' : ''}
          </span>
          {' '}due to inactivity.
        </p>

        <button
          ref={btnRef}
          onClick={onContinue}
          className="btn-primary w-full focus-visible:outline focus-visible:outline-2 focus-visible:outline-koisk-teal"
        >
          Yes, continue session
        </button>
      </div>
    </div>
  )
}
