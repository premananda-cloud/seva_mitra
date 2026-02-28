/**
 * offlineQueue.js
 * Manages payments that failed due to network loss.
 * Stores queued items in IndexedDB 'syncQueue' store.
 * Auto-flushes when the browser comes back online.
 */

import { QUEUE_ACTIONS, QUEUE_STATUS, MAX_RETRY_COUNT } from './constants.js';
import { isNetworkAvailable } from './paymentUtils.js';

const DB_NAME    = 'koiskDB';
const STORE_NAME = 'syncQueue';

// ─── DB Helpers ───────────────────────────────────────────────────────────────

function openDB() {
  return new Promise((resolve, reject) => {
    // We don't open a new DB — we rely on the existing koiskDB opened by localDB.js.
    // This module accesses the syncQueue store inside that DB.
    const request = indexedDB.open(DB_NAME);
    request.onsuccess = () => resolve(request.result);
    request.onerror  = () => reject(request.error);
  });
}

async function getStore(mode = 'readonly') {
  const db = await openDB();
  const tx = db.transaction(STORE_NAME, mode);
  return { store: tx.objectStore(STORE_NAME), tx, db };
}

function promisifyRequest(req) {
  return new Promise((res, rej) => {
    req.onsuccess = () => res(req.result);
    req.onerror   = () => rej(req.error);
  });
}

// ─── offlineQueue Public API ──────────────────────────────────────────────────

export const offlineQueue = {
  /**
   * Add a failed payment action to the queue.
   * @param {{ action: string, payload: object }} item
   * @returns {Promise<{ queueId: number }>}
   */
  async add({ action, payload }) {
    const { store } = await getStore('readwrite');
    const record = {
      action,
      payload,
      retryCount:  0,
      status:      QUEUE_STATUS.PENDING,
      createdAt:   new Date().toISOString(),
      lastRetryAt: null,
      errorLog:    [],
    };
    const queueId = await promisifyRequest(store.add(record));
    console.log(`[offlineQueue] Queued ${action} as id=${queueId}`);
    return { queueId };
  },

  /**
   * Get all unsynced (PENDING) items.
   * @returns {Promise<Array>}
   */
  async getPending() {
    const { store } = await getStore('readonly');
    const index = store.index('byStatus');
    return promisifyRequest(index.getAll(QUEUE_STATUS.PENDING));
  },

  /**
   * Mark a queue item as successfully synced.
   * @param {number} queueId
   */
  async markSynced(queueId) {
    const { store } = await getStore('readwrite');
    const item = await promisifyRequest(store.get(queueId));
    if (!item) return;
    item.status = QUEUE_STATUS.SYNCED;
    await promisifyRequest(store.put(item));
  },

  /**
   * Mark a queue item as permanently failed.
   * @param {number} queueId
   * @param {string} errorMessage
   */
  async markFailed(queueId, errorMessage) {
    const { store } = await getStore('readwrite');
    const item = await promisifyRequest(store.get(queueId));
    if (!item) return;
    item.status = QUEUE_STATUS.FAILED;
    item.errorLog.push(errorMessage);
    await promisifyRequest(store.put(item));
  },

  /**
   * Attempt to process all PENDING queue items.
   * Called on network restoration or manually.
   * @returns {Promise<{ synced: number, failed: number }>}
   */
  async flush() {
    if (!isNetworkAvailable()) {
      console.log('[offlineQueue] flush() called but still offline — skipping');
      return { synced: 0, failed: 0 };
    }

    const pending = await this.getPending();
    let synced = 0;
    let failed = 0;

    for (const item of pending) {
      try {
        await this._retry(item);
        await this.markSynced(item.id);
        synced++;
      } catch (err) {
        const { store } = await getStore('readwrite');
        const fresh = await promisifyRequest(store.get(item.id));
        fresh.retryCount++;
        fresh.lastRetryAt = new Date().toISOString();
        fresh.errorLog.push(err.message ?? String(err));

        if (fresh.retryCount >= MAX_RETRY_COUNT) {
          fresh.status = QUEUE_STATUS.FAILED;
          failed++;
        }
        await promisifyRequest(store.put(fresh));
      }
    }

    console.log(`[offlineQueue] flush complete — synced=${synced}, failed=${failed}`);
    return { synced, failed };
  },

  /**
   * Internal: attempt to replay a single queue item via the orchestrator.
   * Dynamically imports orchestrator to avoid circular deps.
   */
  async _retry(item) {
    // Dynamically import to avoid circular dependency at module load time
    const { default: orchestrator } = await import('../orchestrator/orchestrator.js');

    switch (item.action) {
      case QUEUE_ACTIONS.PAYMENT_INITIATE:
        return orchestrator.initiatePayment(item.payload);

      case QUEUE_ACTIONS.PAYMENT_COMPLETE:
        return orchestrator.completePayment(item.payload);

      case QUEUE_ACTIONS.CUSTOMER_REGISTER:
        return orchestrator.registerCustomer(item.payload);

      default:
        throw new Error(`Unknown queue action: ${item.action}`);
    }
  },

  /**
   * Register a listener so the queue auto-flushes when network returns.
   * Call once at app startup.
   */
  watchNetwork() {
    if (typeof window === 'undefined') return;

    window.addEventListener('online', () => {
      console.log('[offlineQueue] Network restored — flushing queue');
      this.flush();
    });

    window.addEventListener('offline', () => {
      console.log('[offlineQueue] Network lost — payments will be queued');
    });
  },

  /**
   * Returns the count of PENDING items (used by OfflineBanner).
   * @returns {Promise<number>}
   */
  async getPendingCount() {
    const pending = await this.getPending();
    return pending.length;
  },
};

export default offlineQueue;
