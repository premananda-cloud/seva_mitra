import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/modules/auth/authStore'
import localDB from '/src/modules/localdb/localDB.js'
import { clsx } from 'clsx'
import { useKeyboardInput } from "../../hooks/useKeyboardInput"

const SERVICE_TILES = [
  { key: 'electricity', icon: '⚡', color: 'from-amber-400 to-yellow-500',  textColor: 'text-amber-900' },
  { key: 'gas',         icon: '🔥', color: 'from-orange-400 to-red-500',    textColor: 'text-red-900'   },
  { key: 'water',       icon: '💧', color: 'from-blue-400 to-cyan-500',     textColor: 'text-blue-900'  },
  { key: 'municipal',   icon: '🏛️', color: 'from-emerald-400 to-green-500', textColor: 'text-green-900' },
]

const STATUS_CONFIG = {
  COMPLETED:   { label: 'status.completed',  cls: 'badge-success' },
  IN_PROGRESS: { label: 'status.processing', cls: 'badge-warning' },
  APPROVED:    { label: 'status.approved',   cls: 'badge-info'    },
  PENDING:     { label: 'status.pending',    cls: 'badge-muted'   },
  SUBMITTED:   { label: 'status.submitted',  cls: 'badge-info'    },
}

function getGreeting(t) {
  const h = new Date().getHours()
  if (h < 12) return t('dashboard.greeting_morning')
  if (h < 17) return t('dashboard.greeting_afternoon')
  return t('dashboard.greeting_evening')
}

export default function Dashboard() {
  const { t }    = useTranslation()
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const [requests, setRequests] = useState([])
  const [loading,  setLoading]  = useState(true)

  useEffect(() => {
    if (!user) return
    localDB.getRequestsByUser(user.id).then(reqs => {
      const sorted = [...reqs].sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
      setRequests(sorted)
      setLoading(false)
    })
  }, [user])

  const handleLogout = async () => {
    await logout()
    navigate('/')
  }

  const firstName = user?.name?.split(' ')[0] || t('dashboard.welcome')

  return (
    <div className="screen bg-koisk-surface">

      {/* ── Top Nav ─────────────────────────────────────────────── */}
      <div className="bg-koisk-navy px-6 py-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div>
            <p className="text-koisk-accent/70 font-body text-sm">{getGreeting(t)},</p>
            <p className="text-white font-display font-bold text-xl leading-tight">{firstName}</p>
          </div>
          <div className="flex items-center gap-3">
            {user?.isDemo && (
              <span className="badge badge-warning text-xs px-2 py-0.5">DEMO</span>
            )}
            <button
              onClick={handleLogout}
              className="text-white/60 hover:text-white font-body text-sm transition-colors flex items-center gap-1"
            >
              <span>↩</span> {t('nav.logout')}
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 max-w-3xl mx-auto w-full px-4 py-6 space-y-8">

        {/* ── Service Tiles ────────────────────────────────────── */}
        <section className="animate-fade-up">
          <h2 className="heading-display text-lg mb-4 flex items-center gap-2">
            <span>🏢</span> {t('dashboard.services')}
          </h2>
          <div className="grid grid-cols-2 gap-3">
            {SERVICE_TILES.map((svc, i) => (
              <button
                key={svc.key}
                className={clsx(
                  'card-hover p-5 text-left',
                  'animate-fade-up opacity-0-start',
                  `animation-delay-${(i + 1) * 100}`,
                )}
                style={{ animationFillMode: 'forwards' }}
              >
                <div className={clsx(
                  'w-12 h-12 rounded-2xl bg-gradient-to-br flex items-center justify-center mb-3 text-2xl shadow-sm',
                  svc.color,
                )}>
                  {svc.icon}
                </div>
                <p className="font-display font-semibold text-koisk-navy">
                  {t(`services.${svc.key}`)}
                </p>
                <p className="text-koisk-muted text-xs font-body mt-0.5">
                  {t('services.pay_bill')} · {t('services.complaint')}
                </p>
              </button>
            ))}
          </div>
        </section>

        {/* Test input for virtual keyboard */}
        <div className="mt-4 p-4 bg-white rounded-lg">
          <input
            ref={useKeyboardInput()}
            type="text"
            placeholder="Click me to test keyboard"
            className="w-full p-2 border rounded"
          />
        </div>

        {/* ── Recent Activity ──────────────────────────────────── */}
        <section className="animate-fade-up animation-delay-300">
          <h2 className="heading-display text-lg mb-4 flex items-center gap-2">
            <span>📋</span> {t('dashboard.recent_activity')}
          </h2>

          {loading ? (
            <div className="card p-8 flex items-center justify-center">
              <div className="animate-spin h-8 w-8 border-3 border-koisk-teal border-t-transparent rounded-full" />
            </div>
          ) : requests.length === 0 ? (
            <div className="card p-8 text-center text-koisk-muted font-body">
              {t('dashboard.no_activity')}
            </div>
          ) : (
            <div className="space-y-3">
              {requests.slice(0, 5).map((req, i) => {
                const status = STATUS_CONFIG[req.status] || STATUS_CONFIG.SUBMITTED
                return (
                  <div
                    key={req.id}
                    className={clsx(
                      'card p-4 flex items-center justify-between gap-3',
                      'animate-slide-in opacity-0-start',
                    )}
                    style={{ animationDelay: `${i * 80 + 300}ms`, animationFillMode: 'forwards' }}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-display font-semibold text-koisk-navy text-sm truncate">
                        {req.type.replace(/_/g, ' ')}
                      </p>
                      <p className="text-koisk-muted text-xs font-body mt-0.5">
                        {req.reference} · {new Date(req.createdAt).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex flex-col items-end gap-1 shrink-0">
                      <span className={clsx('badge', status.cls)}>{t(status.label)}</span>
                      {req.amount && (
                        <span className="font-display font-bold text-koisk-navy text-sm">
                          {t('common.rupee')}{req.amount.toLocaleString('en-IN')}
                        </span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </section>

        {/* ── Consumer ID chip ─────────────────────────────────── */}
        {user?.consumerId && (
          <div className="animate-fade-up animation-delay-500 card p-4 flex items-center gap-3">
            <span className="text-2xl">🪪</span>
            <div>
              <p className="text-xs text-koisk-muted font-body uppercase tracking-wider">Consumer ID</p>
              <p className="font-mono font-medium text-koisk-navy">{user.consumerId}</p>
            </div>
          </div>
        )}

      </div>
    </div>
  )
}
