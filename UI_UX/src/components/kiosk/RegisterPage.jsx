import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from './authStore'

export default function RegisterPage() {
  const { t }    = useTranslation()
  const navigate = useNavigate()
  const { register, loading, error, clearError } = useAuthStore()

  const [form, setForm] = useState({
    name: '', phone: '', pin: '', pinConfirm: '', consumerId: '',
  })

  const set = (field) => (e) => {
    clearError()
    let val = e.target.value
    if (field === 'phone')                          val = val.replace(/\D/g, '').slice(0, 10)
    if (field === 'pin' || field === 'pinConfirm') val = val.replace(/\D/g, '').slice(0, 4)
    setForm(f => ({ ...f, [field]: val }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const result = await register(form)
    if (result?.success) navigate('/dashboard')
  }

  const isReady = form.name && form.phone.length === 10 &&
                  form.pin.length === 4 && form.pinConfirm.length === 4

  return (
    <div className="screen bg-koisk-surface">
      {/* Top bar — FIX (High): controls meet min touch target + contrast */}
      <div className="bg-koisk-navy px-6 py-4 flex items-center justify-between">
        <Link
          to="/login"
          className="flex items-center gap-2 text-white hover:text-koisk-accent transition-colors min-h-[44px] min-w-[44px] font-body text-sm"
          aria-label={t('nav.back')}
        >
          <span aria-hidden="true">←</span>
          <span>{t('nav.back')}</span>
        </Link>
        <span className="font-display font-bold text-white text-lg">KOISK</span>
        <div className="min-w-[44px]" />
      </div>

      <div className="flex-1 flex items-center justify-center px-6 py-8">
        <div className="w-full max-w-md animate-fade-up">

          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-koisk-accent/10 rounded-3xl flex items-center justify-center mx-auto mb-4">
              <span className="text-3xl" aria-hidden="true">✨</span>
            </div>
            <h1 className="heading-display text-3xl mb-1">{t('auth.register_title')}</h1>
            <p className="text-koisk-muted font-body">{t('auth.register_subtitle')}</p>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-2xl animate-fade-in" role="alert">
              <p className="text-red-700 font-body text-sm text-center">{t(error)}</p>
            </div>
          )}

          {/* Form — FIX (High): every label has htmlFor matching its input's id */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="reg-name" className="input-label">{t('auth.name')}</label>
              <input
                id="reg-name"
                type="text"
                value={form.name}
                onChange={set('name')}
                placeholder={t('auth.name_placeholder')}
                className="input-field"
                autoCapitalize="words"
                required
                aria-required="true"
              />
            </div>

            <div>
              <label htmlFor="reg-phone" className="input-label">{t('auth.phone')}</label>
              <input
                id="reg-phone"
                type="tel"
                inputMode="numeric"
                value={form.phone}
                onChange={set('phone')}
                placeholder={t('auth.phone_placeholder')}
                className="input-field"
                required
                aria-required="true"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label htmlFor="reg-pin" className="input-label">{t('auth.pin')}</label>
                <input
                  id="reg-pin"
                  type="password"
                  inputMode="numeric"
                  value={form.pin}
                  onChange={set('pin')}
                  placeholder="••••"
                  className="input-field tracking-[0.5em] text-2xl text-center"
                  maxLength={4}
                  required
                  aria-required="true"
                />
              </div>
              <div>
                <label htmlFor="reg-pin-confirm" className="input-label">{t('auth.pin_confirm')}</label>
                <input
                  id="reg-pin-confirm"
                  type="password"
                  inputMode="numeric"
                  value={form.pinConfirm}
                  onChange={set('pinConfirm')}
                  placeholder="••••"
                  className={`input-field tracking-[0.5em] text-2xl text-center ${
                    form.pinConfirm && form.pin !== form.pinConfirm
                      ? 'border-red-400 focus:ring-red-200'
                      : ''
                  }`}
                  maxLength={4}
                  required
                  aria-required="true"
                  aria-invalid={form.pinConfirm && form.pin !== form.pinConfirm ? 'true' : undefined}
                  aria-describedby={form.pinConfirm && form.pin !== form.pinConfirm ? 'pin-mismatch' : undefined}
                />
              </div>
            </div>

            {form.pinConfirm && form.pin !== form.pinConfirm && (
              <p id="pin-mismatch" role="alert" className="text-red-500 text-xs font-body -mt-2">
                {t('auth.errors.pin_mismatch')}
              </p>
            )}

            <div>
              <label htmlFor="reg-consumer-id" className="input-label">{t('auth.consumer_id')}</label>
              <input
                id="reg-consumer-id"
                type="text"
                value={form.consumerId}
                onChange={set('consumerId')}
                placeholder={t('auth.consumer_id_placeholder')}
                className="input-field"
              />
            </div>

            <button
              type="submit"
              disabled={loading || !isReady}
              className="btn-primary w-full mt-2"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <Spinner />
                  {t('common.loading')}
                </span>
              ) : t('auth.register_btn')}
            </button>
          </form>

          {/* Login link */}
          <p className="text-center mt-6 text-koisk-muted font-body">
            {t('auth.have_account')}{' '}
            <Link to="/login" className="text-koisk-teal font-semibold hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-koisk-teal rounded">
              {t('auth.login_link')}
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
