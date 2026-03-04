/**
 * MODULE 1 — AUTHENTICATION LAYER
 * Zustand store — global auth state
 *
 * Handles: login, register, logout, session rehydration
 * Persists session to LocalDB (Module 3)
 * Notifies Orchestrator (Module 4) for eventual backend sync
 */

import { create } from 'zustand'
import { v4 as uuidv4 } from 'uuid'
import localDB from '/src/modules/localdb/localDB.js'
import orchestrator from '/src/modules/orchestrator/orchestrator.js'

// Simple PIN "hash" for demo — replace with bcrypt in production
const hashPin = (pin) => pin  // TODO: use bcrypt when backend connects

const validatePhone = (phone) => /^[6-9]\d{9}$/.test(phone)
const validatePin   = (pin)   => /^\d{4}$/.test(pin)

export const useAuthStore = create((set, get) => ({
  user:    null,
  loading: false,
  error:   null,

  // ── Init ───────────────────────────────────────────────────────
  // Called on app mount — rehydrate session from LocalDB
  initFromStorage: async () => {
    try {
      const raw = localStorage.getItem('koisk_session')
      if (!raw) return
      const { userId, expiresAt } = JSON.parse(raw)
      if (Date.now() > expiresAt) {
        localStorage.removeItem('koisk_session')
        return
      }
      const user = await localDB.getUserById(userId)
      if (user) set({ user })
    } catch {
      localStorage.removeItem('koisk_session')
    }
  },

  // ── Register ───────────────────────────────────────────────────
  register: async ({ name, phone, pin, pinConfirm, consumerId }) => {
    set({ loading: true, error: null })

    // Validate
    if (!name?.trim())          return set({ loading: false, error: 'auth.errors.name_required' })
    if (!validatePhone(phone))  return set({ loading: false, error: 'auth.errors.phone_invalid' })
    if (!validatePin(pin))      return set({ loading: false, error: 'auth.errors.pin_length' })
    if (pin !== pinConfirm)     return set({ loading: false, error: 'auth.errors.pin_mismatch' })

    // Check duplicate
    const existing = await localDB.getUserByPhone(phone)
    if (existing) return set({ loading: false, error: 'auth.errors.already_registered' })

    // Create user — UUID generated here so it's stable across sync
    const user = {
      id:         uuidv4(),
      name:       name.trim(),
      phone,
      pinHash:    hashPin(pin),
      consumerId: consumerId?.trim() || null,
      language:   localStorage.getItem('koisk_language') || 'en',
      isDemo:     false,
      syncedToBackend: false,
      createdAt:  new Date().toISOString(),
    }

    await localDB.createUser(user)
    await get()._createSession(user)

    // Notify orchestrator — will sync to backend when connected
    orchestrator.onUserRegistered(user)

    set({ user, loading: false })
    return { success: true }
  },

  // ── Login ──────────────────────────────────────────────────────
  login: async ({ phone, pin }) => {
    set({ loading: true, error: null })

    if (!validatePhone(phone)) return set({ loading: false, error: 'auth.errors.phone_invalid' })
    if (!validatePin(pin))     return set({ loading: false, error: 'auth.errors.pin_length' })

    const user = await localDB.getUserByPhone(phone)
    if (!user || user.pinHash !== hashPin(pin)) {
      return set({ loading: false, error: 'auth.errors.invalid_credentials' })
    }

    await get()._createSession(user)
    set({ user, loading: false })
    return { success: true }
  },

  // ── Demo Login ─────────────────────────────────────────────────
  loginDemo: async () => {
    set({ loading: true, error: null })
    const user = await localDB.getUserByPhone('+919876543210') // BUG FIX: match E.164 format used in localDB seed data
    if (!user) return set({ loading: false, error: 'auth.errors.generic' })
    await get()._createSession(user)
    set({ user, loading: false })
    return { success: true }
  },

  // ── Logout ─────────────────────────────────────────────────────
  logout: async () => {
    const user = get().user
    if (user) {
      await localDB.clearSession(user.id)
      orchestrator.onUserLoggedOut(user.id)
    }
    localStorage.removeItem('koisk_session')
    set({ user: null, error: null })
  },

  // ── Helpers ────────────────────────────────────────────────────
  _createSession: async (user) => {
    const expiresAt = Date.now() + 8 * 60 * 60 * 1000 // 8 hours
    // BUG FIX: localDB.saveSession(session) accepts one object, not (userId, data).
    // 'id' is the keyPath; 'userId' feeds the byUserId index.
    const session = { id: user.id, userId: user.id, expiresAt, createdAt: Date.now() }
    await localDB.saveSession(session)
    localStorage.setItem('koisk_session', JSON.stringify({ userId: user.id, expiresAt }))
  },

  clearError: () => set({ error: null }),
}))
