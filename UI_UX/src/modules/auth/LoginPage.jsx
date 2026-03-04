import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from './authStore'
import { clsx } from 'clsx'

export default function LoginPage() {
  const { t, i18n } = useTranslation()
  const navigate    = useNavigate()
  const { login, loginDemo, loading, error, clearError } = useAuthStore()

  const [phone, setPhone] = useState('')
  const [pin,   setPin]   = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    clearError()
    const result = await login({ phone, pin })
    if (result?.success) navigate('/dashboard')
  }

  const handleDemo = async () => {
    clearError()
    const result = await loginDemo()
    if (result?.success) navigate('/dashboard')
  }

  return (
    <div className="screen bg-koisk-surface">
      {/* Top bar */}
      <div className="bg-koisk-navy px-6 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-white/70 hover:text-white transition-colors">
          <span>←</span>
          <span className="font-body text-sm">{t('nav.back')}</span>
        </Link>
        <span className="font-display font-bold text-white text-lg">KOISK</span>
        <button
          onClick={() => navigate('/')}
          className="text-white/50 hover:text-koisk-accent font-body text-sm transition-colors"
        >
          {t('language.change')}
        </button>
      </div>

      <div className="flex-1 flex items-center justify-center px-6 py-10">
        <div className="w-full max-w-md animate-fade-up">

          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-koisk-teal/10 rounded-3xl flex items-center justify-center mx-auto mb-4">
              <span className="text-3xl">🔐</span>
            </div>
            <h1 className="heading-display text-3xl mb-1">{t('auth.login_title')}</h1>
            <p className="text-koisk-muted font-body">{t('auth.login_subtitle')}</p>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-2xl animate-fade-in">
              <p className="text-red-700 font-body text-sm text-center">{t(error)}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="input-label">{t('auth.phone')}</label>
              <input
                type="tel"
                inputMode="numeric"
                value={phone}
                onChange={e => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                placeholder={t('auth.phone_placeholder')}
                className="input-field"
                autoComplete="tel"
                required
              />
            </div>

            <div>
              <label className="input-label">{t('auth.pin')}</label>
              <input
                type="password"
                inputMode="numeric"
                value={pin}
                onChange={e => setPin(e.target.value.replace(/\D/g, '').slice(0, 4))}
                placeholder={t('auth.pin_placeholder')}
                className="input-field tracking-[0.5em] text-2xl"
                maxLength={4}
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading || phone.length < 10 || pin.length < 4}
              className="btn-primary w-full mt-2"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <Spinner />
                  {t('common.loading')}
                </span>
              ) : t('auth.login_btn')}
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-3 my-6">
            <div className="flex-1 h-px bg-koisk-blue/10" />
            <span className="text-koisk-muted text-sm font-body">{t('auth.or_divider')}</span>
            <div className="flex-1 h-px bg-koisk-blue/10" />
          </div>

          {/* Demo button */}
          <button
            onClick={handleDemo}
            disabled={loading}
            className="w-full p-4 rounded-2xl border-2 border-dashed border-koisk-teal/40 text-koisk-teal font-display font-semibold text-base hover:bg-koisk-teal/5 transition-all active:scale-95 disabled:opacity-40"
          >
            <span className="block">{t('auth.use_demo')}</span>
            <span className="block text-xs font-body font-normal text-koisk-muted mt-1">
              {t('auth.demo_hint')}
            </span>
          </button>

          {/* Register link */}
          <p className="text-center mt-6 text-koisk-muted font-body">
            {t('auth.no_account')}{' '}
            <Link to="/register" className="text-koisk-teal font-semibold hover:underline">
              {t('auth.register_link')}
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

function Spinner() {
  return (
    <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  )
}
