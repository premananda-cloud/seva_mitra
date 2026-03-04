/**
 * SUPPORTED_LANGUAGES — single source of truth
 * Adding a new entry here automatically updates:
 *   - Language selector UI
 *   - Language badge counts
 *   - Any dropdown that lists languages
 */
export const SUPPORTED_LANGUAGES = [
  { code: 'en', name: 'English',  nativeName: 'English',  flag: '🇬🇧', script: 'Latin'      },
  { code: 'hi', name: 'Hindi',    nativeName: 'हिन्दी',    flag: '🇮🇳', script: 'Devanagari' },
  { code: 'od', name: 'Odia',     nativeName: 'ଓଡ଼ିଆ',    flag: '🇮🇳', script: 'Odia'       },
  { code: 'te', name: 'Telugu',   nativeName: 'తెలుగు',   flag: '🇮🇳', script: 'Telugu'     },
  { code: 'ta', name: 'Tamil',    nativeName: 'தமிழ்',    flag: '🇮🇳', script: 'Tamil'      },
  { code: 'kn', name: 'Kannada',  nativeName: 'ಕನ್ನಡ',    flag: '🇮🇳', script: 'Kannada'    },
  { code: 'mr', name: 'Marathi',  nativeName: 'मराठी',    flag: '🇮🇳', script: 'Devanagari' },
]

export const DEFAULT_LANGUAGE = 'en'

export const getLanguageByCode = (code) =>
  SUPPORTED_LANGUAGES.find(l => l.code === code) || SUPPORTED_LANGUAGES[0]
