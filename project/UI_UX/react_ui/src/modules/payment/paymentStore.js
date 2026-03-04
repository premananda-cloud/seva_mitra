/**
 * paymentStore.js
 * Zustand store for all payment UI state.
 * Only the PaymentFlow component family should read/write this store.
 *
 * NOTE: cardData is in-memory ONLY — never persisted to localDB or localStorage.
 *       clearCardData() MUST be called immediately after the SDK payment call.
 */

import { create } from 'zustand';
import { PAYMENT_STEPS, GATEWAYS, PAYMENT_METHODS } from './constants.js';

const initialCardData = { number: '', expiry: '', cvv: '', name: '' };

const usePaymentStore = create((set, get) => ({
  // ─── Wizard Step ─────────────────────────────────────────────────────────
  step: PAYMENT_STEPS.IDLE,

  // ─── Active Bill ──────────────────────────────────────────────────────────
  activeBill: null,

  // ─── Gateway & Method Selection ───────────────────────────────────────────
  selectedGateway: GATEWAYS.PORTONE,
  selectedMethod:  null,

  // ─── Input Values (in-memory only — never persisted) ─────────────────────
  upiId:    '',
  cardData: { ...initialCardData },

  // ─── Processing State ─────────────────────────────────────────────────────
  loading:  false,
  error:    null,
  orderId:  null,

  // ─── Completed Payment ────────────────────────────────────────────────────
  receipt: null,

  // ─── Offline State ────────────────────────────────────────────────────────
  isOffline:   false,
  queuedCount: 0,

  // ─── Actions ─────────────────────────────────────────────────────────────

  setStep: (step) => set({ step, error: null }),

  setActiveBill: (bill) => set({ activeBill: bill }),

  setGateway: (gateway) => set({ selectedGateway: gateway }),

  setMethod: (method) => set({ selectedMethod: method, upiId: '', cardData: { ...initialCardData } }),

  setUpiId: (id) => set({ upiId: id }),

  setCardData: (data) =>
    set((state) => ({
      cardData: { ...state.cardData, ...data },
    })),

  setLoading: (loading) => set({ loading }),

  setError: (error) => set({ error, loading: false }),

  setOrderId: (orderId) => set({ orderId }),

  setReceipt: (receipt) => set({ receipt, step: PAYMENT_STEPS.SUCCESS }),

  setOffline: (isOffline) => set({ isOffline }),

  setQueuedCount: (count) => set({ queuedCount: count }),

  /**
   * Clears raw card data from memory immediately after SDK call.
   * MUST be called right after gateway.openPayment() is invoked.
   */
  clearCardData: () => set({ cardData: { ...initialCardData } }),

  /**
   * Full reset — called on logout and after the receipt is dismissed.
   * Does NOT reset isOffline or queuedCount (those reflect network state).
   */
  reset: () =>
    set({
      step:            PAYMENT_STEPS.IDLE,
      activeBill:      null,
      selectedGateway: GATEWAYS.PORTONE,
      selectedMethod:  null,
      upiId:           '',
      cardData:        { ...initialCardData },
      loading:         false,
      error:           null,
      orderId:         null,
      receipt:         null,
    }),
}));

export default usePaymentStore;
