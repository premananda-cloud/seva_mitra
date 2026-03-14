import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { SUPPORTED_LANGUAGES, getLanguageByCode } from '@/config/languages'
import { useAuthStore } from '@/modules/auth/authStore'
import { clsx } from 'clsx'

export default function LanguageSelect() {
  const { i18n, t } = useTranslation()
  const navigate   = useNavigate()
  const user       = useAuthStore(s => s.user)

  const current = getLanguageByCode(i18n.language)

  const handleSelect = (code) => {
    i18n.changeLanguage(code)
  }

  const handleContinue = () => {
    navigate(user ? '/dashboard' : '/login')
  }

  return (
    <div className="screen bg-gradient-to-br from-koisk-navy via-koisk-blue to-koisk-teal">
      {/* Background pattern */}
      <div
        className="absolute inset-0 opacity-[0.08]"
        style={{
          backgroundImage: `radial-gradient(circle at 2px 2px, white 1px, transparent 0)`,
          backgroundSize: '40px 40px',
        }}
      />

      <div className="relative flex-1 flex flex-col items-center justify-center px-6 py-12">
        {/* Logo */}
        <div className="animate-fade-up mb-8 text-center">
          <div className="inline-flex items-center gap-3 mb-3">
            <div className="w-12 h-12 rounded-2xl bg-koisk-accent/20 border border-koisk-accent/40 flex items-center justify-center">
              <span className="text-2xl">🏛️</span>
            </div>
            <span className="font-display font-bold text-white text-4xl tracking-tight">
              KOISK
            </span>
          </div>
          <p className="text-koisk-accent/80 font-body text-lg">
            {t('tagline')}
          </p>
        </div>

        {/* Title */}
        <div className="animate-fade-up animation-delay-100 text-center mb-10">
          <h1 className="font-display font-bold text-white text-3xl mb-2">
            {t('language.select_title')}
          </h1>
          <p className="text-white/60 font-body text-lg">
            {t('language.select_subtitle')}
          </p>
        </div>

        {/* Language grid */}
        <div className="animate-fade-up animation-delay-200 w-full max-w-3xl">
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {SUPPORTED_LANGUAGES.map((lang, idx) => {
              const isSelected = i18n.language === lang.code
              return (
                <button
                  key={lang.code}
                  onClick={() => handleSelect(lang.code)}
                  className={clsx(
                    'relative flex flex-col items-center justify-center gap-2',
                    'min-h-[100px] rounded-2xl p-4',
                    'font-display font-semibold text-lg',
                    'transition-all duration-200 active:scale-95',
                    'border-2',
                    isSelected
                      ? 'bg-koisk-accent text-koisk-navy border-koisk-accent shadow-xl shadow-koisk-accent/30 ring-2 ring-white/40'
                      : 'bg-white/10 text-white border-white/20 hover:bg-white/20 hover:border-white/40',
                  )}
                  style={{ animationDelay: `${idx * 60 + 200}ms` }}
                  aria-label={`Select ${lang.name}`}
                  aria-pressed={isSelected}
                >
                  {isSelected && (
                    <span className="absolute top-2 right-2 text-xs bg-koisk-navy/20 rounded-full w-5 h-5 flex items-center justify-center">
                      ✓
                    </span>
                  )}
                  <span className="text-3xl">{lang.flag}</span>
                  <span>{lang.nativeName}</span>
                  {lang.nativeName !== lang.name && (
                    <span className={clsx('text-xs font-body font-normal', isSelected ? 'text-koisk-navy/70' : 'text-white/50')}>
                      {lang.name}
                    </span>
                  )}
                </button>
              )
            })}
          </div>
        </div>

        {/* Current selection + Continue */}
        <div className="animate-fade-up animation-delay-400 mt-10 flex flex-col items-center gap-4">
          <p className="text-white/50 font-body text-sm">
            {t('language.current')}: <span className="text-white font-semibold">{current.nativeName}</span>
          </p>

          <button
            onClick={handleContinue}
            className="btn-primary bg-koisk-accent text-koisk-navy hover:bg-white hover:text-koisk-navy px-12 py-4 text-xl min-w-[220px]"
          >
            {t('language.continue')} →
          </button>
        </div>

        {/* Language count badge */}
        <p className="mt-6 text-white/30 font-body text-xs">
          {SUPPORTED_LANGUAGES.length} languages supported
        </p>
      </div>
    </div>
  )
}
