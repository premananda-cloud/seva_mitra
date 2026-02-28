/**
 * localDB.js — MODIFIED VERSION
 *
 * Changes from v1:
 *  1. DB_VERSION bumped to 2
 *  2. Three new object stores added in upgrade(): paymentProfiles, payments, bills
 *  3. New seed data added to _seedDemoData()
 *  4. New CRUD helpers added for each new store
 *
 * ════════════════════════════════════════════════════════════════════════════
 * MERGE INSTRUCTION:
 *   This file shows the complete additions needed.
 *   Replace the existing DB_VERSION constant and upgrade() block.
 *   Append the new store helpers and seed data below the existing code.
 * ════════════════════════════════════════════════════════════════════════════
 */

// ─── Change 1: Bump DB_VERSION ────────────────────────────────────────────────
// Was: const DB_VERSION = 1;
const DB_VERSION = 2;

const DB_NAME = 'koiskDB';

// ─── Change 2: New stores in upgrade() ───────────────────────────────────────
// Append this block INSIDE the existing onupgradeneeded handler,
// after the existing stores are created.
//
// if (oldVersion < 2) {
//   /* ── paymentProfiles ── */
//   const profileStore = db.createObjectStore('paymentProfiles', { keyPath: 'id' });
//   profileStore.createIndex('byUserId', 'userId', { unique: true });
//
//   /* ── payments ── */
//   const paymentStore = db.createObjectStore('payments', { keyPath: 'id' });
//   paymentStore.createIndex('byUserId', 'userId');
//   paymentStore.createIndex('byStatus', 'status');
//   paymentStore.createIndex('byDept',   'dept');
//
//   /* ── bills ── */
//   const billStore = db.createObjectStore('bills', { keyPath: 'id' });
//   billStore.createIndex('byUserId', 'userId');
//   billStore.createIndex('byDept',   'dept');
//   billStore.createIndex('byStatus', 'status');
//
//   /* ── syncQueue (for offlineQueue.js) ── */
//   const queueStore = db.createObjectStore('syncQueue', { autoIncrement: true, keyPath: 'id' });
//   queueStore.createIndex('byStatus', 'status');
// }

// ─────────────────────────────────────────────────────────────────────────────
// Everything below is the new helper code to ADD to the existing localDB module.
// ─────────────────────────────────────────────────────────────────────────────

const DEMO_USER_ID = 'demo-user-ramesh-001';

// ─── DB open helper (copy of internal pattern) ────────────────────────────────

function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      const { oldVersion } = event;

      // --- existing stores from v1 (kept here for reference) ---
      // if (oldVersion < 1) { ... existing stores ... }

      if (oldVersion < 2) {
        if (!db.objectStoreNames.contains('paymentProfiles')) {
          const s = db.createObjectStore('paymentProfiles', { keyPath: 'id' });
          s.createIndex('byUserId', 'userId', { unique: true });
        }
        if (!db.objectStoreNames.contains('payments')) {
          const s = db.createObjectStore('payments', { keyPath: 'id' });
          s.createIndex('byUserId', 'userId');
          s.createIndex('byStatus', 'status');
          s.createIndex('byDept',   'dept');
        }
        if (!db.objectStoreNames.contains('bills')) {
          const s = db.createObjectStore('bills', { keyPath: 'id' });
          s.createIndex('byUserId', 'userId');
          s.createIndex('byDept',   'dept');
          s.createIndex('byStatus', 'status');
        }
        if (!db.objectStoreNames.contains('syncQueue')) {
          const s = db.createObjectStore('syncQueue', { autoIncrement: true, keyPath: 'id' });
          s.createIndex('byStatus', 'status');
        }
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror   = () => reject(request.error);
  });
}

function tx(db, storeName, mode = 'readonly') {
  const t = db.transaction(storeName, mode);
  return { store: t.objectStore(storeName), t };
}

function req(r) {
  return new Promise((res, rej) => {
    r.onsuccess = () => res(r.result);
    r.onerror   = () => rej(r.error);
  });
}

// ─── Payment Profile CRUD ─────────────────────────────────────────────────────

export async function getPaymentProfile(userId) {
  const db = await openDB();
  const { store } = tx(db, 'paymentProfiles');
  const index = store.index('byUserId');
  return req(index.get(userId));
}

export async function savePaymentProfile(profile) {
  const db = await openDB();
  const { store } = tx(db, 'paymentProfiles', 'readwrite');
  return req(store.put(profile));
}

// ─── Payment CRUD ─────────────────────────────────────────────────────────────

export async function getPaymentById(id) {
  const db = await openDB();
  const { store } = tx(db, 'payments');
  return req(store.get(id));
}

export async function savePayment(payment) {
  const db = await openDB();
  const { store } = tx(db, 'payments', 'readwrite');
  return req(store.put(payment));
}

export async function getPaymentsByUserId(userId) {
  const db = await openDB();
  const { store } = tx(db, 'payments');
  const index = store.index('byUserId');
  return req(index.getAll(userId));
}

// ─── Bill CRUD ────────────────────────────────────────────────────────────────

export async function getBillById(id) {
  const db = await openDB();
  const { store } = tx(db, 'bills');
  return req(store.get(id));
}

export async function saveBill(bill) {
  const db = await openDB();
  const { store } = tx(db, 'bills', 'readwrite');
  return req(store.put(bill));
}

export async function getBillsByUserAndDept(userId, dept) {
  const db = await openDB();
  const { store } = tx(db, 'bills');
  const all = await req(store.index('byUserId').getAll(userId));
  return dept ? all.filter((b) => b.dept === dept) : all;
}

// ─── Demo Seed Data ───────────────────────────────────────────────────────────
// Call this inside the existing _seedDemoData() function.

export async function seedPaymentDemoData() {
  const db = await openDB();

  // Bills
  const bills = [
    {
      id: 'BILL-ELEC-202602', userId: DEMO_USER_ID, dept: 'electricity',
      consumerNo: 'ELEC-MH-00234', billMonth: '2026-02',
      amountDue: 1847, dueDate: '2026-03-10T00:00:00Z',
      status: 'PENDING', paidPaymentId: null,
      createdAt: new Date().toISOString(),
    },
    {
      id: 'BILL-WATER-202602', userId: DEMO_USER_ID, dept: 'water',
      consumerNo: 'WAT-MH-00891', billMonth: '2026-02',
      amountDue: 340, dueDate: '2026-03-05T00:00:00Z',
      status: 'PENDING', paidPaymentId: null,
      createdAt: new Date().toISOString(),
    },
    {
      id: 'BILL-GAS-202602', userId: DEMO_USER_ID, dept: 'gas',
      consumerNo: 'GAS-MH-00156', billMonth: '2026-02',
      amountDue: 890, dueDate: '2026-03-15T00:00:00Z',
      status: 'PENDING', paidPaymentId: null,
      createdAt: new Date().toISOString(),
    },
  ];

  // Payment profile for demo user
  const profile = {
    id:                  DEMO_USER_ID,
    userId:              DEMO_USER_ID,
    portoneCustomerId:   'cust_demo_portone_001',
    razorpayCustomerId:  null,
    name:                'Ramesh Kumar',
    contact:             '+919876543210',
    email:               'ramesh@koisk.local',
    defaultMethod:       'upi',
    preferredGateway:    'portone',
    createdAt:           '2026-01-10T08:00:00Z',
    syncedToBackend:     false,
  };

  // Past payments for history display (4 seed records)
  const pastPayments = [
    {
      id: 'pay-demo-001', userId: DEMO_USER_ID, dept: 'electricity',
      type: 'BILL_PAYMENT', billRef: 'BILL-ELEC-202601', amount: 1620,
      currency: 'INR', gateway: 'mock', gatewayPaymentId: 'pay_mock_001',
      gatewayOrderId: 'order_mock_001', method: 'upi',
      status: 'SUCCESS', referenceNo: 'PAY-ELEC-20260202-0031',
      receiptData: { referenceNo: 'PAY-ELEC-20260202-0031', amount: 1620, dept: 'electricity', method: 'upi', paidAt: '2026-02-02T11:14:00Z', consumerNo: 'ELEC-MH-00234' },
      createdAt: '2026-02-02T11:10:00Z', paidAt: '2026-02-02T11:14:00Z', syncedToBackend: false,
    },
    {
      id: 'pay-demo-002', userId: DEMO_USER_ID, dept: 'water',
      type: 'BILL_PAYMENT', billRef: 'BILL-WATER-202601', amount: 290,
      currency: 'INR', gateway: 'mock', gatewayPaymentId: 'pay_mock_002',
      gatewayOrderId: 'order_mock_002', method: 'upi',
      status: 'SUCCESS', referenceNo: 'PAY-WATR-20260205-0032',
      receiptData: { referenceNo: 'PAY-WATR-20260205-0032', amount: 290, dept: 'water', method: 'upi', paidAt: '2026-02-05T09:22:00Z', consumerNo: 'WAT-MH-00891' },
      createdAt: '2026-02-05T09:20:00Z', paidAt: '2026-02-05T09:22:00Z', syncedToBackend: false,
    },
    {
      id: 'pay-demo-003', userId: DEMO_USER_ID, dept: 'gas',
      type: 'BILL_PAYMENT', billRef: 'BILL-GAS-202601', amount: 760,
      currency: 'INR', gateway: 'mock', gatewayPaymentId: 'pay_mock_003',
      gatewayOrderId: 'order_mock_003', method: 'card',
      status: 'SUCCESS', referenceNo: 'PAY-GAS-20260210-0033',
      receiptData: { referenceNo: 'PAY-GAS-20260210-0033', amount: 760, dept: 'gas', method: 'card', paidAt: '2026-02-10T17:45:00Z', consumerNo: 'GAS-MH-00156' },
      createdAt: '2026-02-10T17:44:00Z', paidAt: '2026-02-10T17:45:00Z', syncedToBackend: false,
    },
    {
      id: 'pay-demo-004', userId: DEMO_USER_ID, dept: 'electricity',
      type: 'BILL_PAYMENT', billRef: 'BILL-ELEC-202512', amount: 1930,
      currency: 'INR', gateway: 'mock', gatewayPaymentId: 'pay_mock_004',
      gatewayOrderId: 'order_mock_004', method: 'netbanking',
      status: 'SUCCESS', referenceNo: 'PAY-ELEC-20260104-0028',
      receiptData: { referenceNo: 'PAY-ELEC-20260104-0028', amount: 1930, dept: 'electricity', method: 'netbanking', paidAt: '2026-01-04T14:30:00Z', consumerNo: 'ELEC-MH-00234' },
      createdAt: '2026-01-04T14:28:00Z', paidAt: '2026-01-04T14:30:00Z', syncedToBackend: false,
    },
  ];

  // Write all seed data (skip if already exists)
  const billStore = db.transaction('bills', 'readwrite').objectStore('bills');
  for (const bill of bills) {
    const existing = await req(billStore.get(bill.id));
    if (!existing) await req(billStore.put(bill));
  }

  const profStore = db.transaction('paymentProfiles', 'readwrite').objectStore('paymentProfiles');
  const existingProfile = await req(profStore.get(DEMO_USER_ID));
  if (!existingProfile) await req(profStore.put(profile));

  const payStore = db.transaction('payments', 'readwrite').objectStore('payments');
  for (const payment of pastPayments) {
    const existing = await req(payStore.get(payment.id));
    if (!existing) await req(payStore.put(payment));
  }
}

// ─── getUserById stub ─────────────────────────────────────────────────────────
// This function is called by paymentService — implement it in the real localDB.js
// by reading from the 'users' store. Stub provided here for reference.

export async function getUserById(userId) {
  const db = await openDB();
  const { store } = tx(db, 'users');
  return req(store.get(userId));
}

// ─── Default export (merge into existing localDB default export object) ───────
const localDB = {
  getPaymentProfile,
  savePaymentProfile,
  getPaymentById,
  savePayment,
  getPaymentsByUserId,
  getBillById,
  saveBill,
  getBillsByUserAndDept,
  seedPaymentDemoData,
  getUserById,
};

export default localDB;
