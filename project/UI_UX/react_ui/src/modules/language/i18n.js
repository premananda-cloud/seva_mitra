/**
 * MODULE 2 — LANGUAGE CONFIGURATION
 *
 * TO ADD A NEW LANGUAGE:
 *   1. Create src/modules/language/locales/[code].json
 *   2. Import it below and add to `resources`
 *   3. Add to SUPPORTED_LANGUAGES in config/languages.js
 *   That's it. Zero component changes needed.
 */

import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import en from './locales/en.json'
import hi from './locales/hi.json'
import od from './locales/od.json'
import te from './locales/te.json'
import ta from './locales/ta.json'
import kn from './locales/kn.json'
import mr from './locales/mr.json'
import ma from './locales/ma.json'

const resources = {
  en: { translation: en },
  hi: { translation: hi },
  od: { translation: od },
  te: { translation: te },
  ta: { translation: ta },
  kn: { translation: kn },
  mr: { translation: mr },
  ma: { translation: ma }
}

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: localStorage.getItem('koisk_language') || 'en',
    fallbackLng: 'en',
    interpolation: { escapeValue: false },
  })

// Persist language choice whenever it changes
i18n.on('languageChanged', (lng) => {
  localStorage.setItem('koisk_language', lng)
})

export default i18n
