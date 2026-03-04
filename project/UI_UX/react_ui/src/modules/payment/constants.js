// ─── Payment Method Codes ────────────────────────────────────────────────────
export const PAYMENT_METHODS = {
  UPI:         'upi',
  CARD:        'card',
  NET_BANKING: 'netbanking',
};

// ─── Gateway Names ────────────────────────────────────────────────────────────
export const GATEWAYS = {
  PORTONE:  'portone',
  RAZORPAY: 'razorpay',
  MOCK:     'mock',
};

export const GATEWAY_DISPLAY_NAMES = {
  portone:  'PortOne',
  razorpay: 'Razorpay',
  mock:     'Demo',
};

// ─── Payment Status Strings ───────────────────────────────────────────────────
// These must match backend exactly (Section 3.3 of spec)
export const PAYMENT_STATUS = {
  PENDING:        'PENDING',
  SUCCESS:        'SUCCESS',
  FAILED:         'FAILED',
  OFFLINE_QUEUED: 'OFFLINE_QUEUED',
};

// Backend uses lowercase — map for API responses
export const BACKEND_STATUS_MAP = {
  pending:        'PENDING',
  paid:           'SUCCESS',
  failed:         'FAILED',
  refunded:       'FAILED',
  offline_queued: 'OFFLINE_QUEUED',
};

// ─── Payment Wizard Steps ─────────────────────────────────────────────────────
export const PAYMENT_STEPS = {
  IDLE:              'IDLE',
  BILL_SUMMARY:      'BILL_SUMMARY',
  METHOD_SELECT:     'METHOD_SELECT',
  INPUT:             'INPUT',
  PROCESSING:        'PROCESSING',
  SUCCESS:           'SUCCESS',
  FAILED:            'FAILED',
  OFFLINE_QUEUED:    'OFFLINE_QUEUED',
};

// ─── Departments ──────────────────────────────────────────────────────────────
export const DEPARTMENTS = {
  ELECTRICITY: 'electricity',
  GAS:         'gas',
  WATER:       'water',
};

export const DEPT_DISPLAY_NAMES = {
  electricity: 'Electricity',
  gas:         'Gas',
  water:       'Water',
};

export const DEPT_ICONS = {
  electricity: '⚡',
  gas:         '🔥',
  water:       '💧',
};

// ─── Offline Queue Actions ────────────────────────────────────────────────────
export const QUEUE_ACTIONS = {
  PAYMENT_INITIATE:   'PAYMENT_INITIATE',
  PAYMENT_COMPLETE:   'PAYMENT_COMPLETE',
  CUSTOMER_REGISTER:  'CUSTOMER_REGISTER',
};

export const QUEUE_STATUS = {
  PENDING: 'PENDING',
  SYNCED:  'SYNCED',
  FAILED:  'FAILED',
};

// ─── Card Networks ────────────────────────────────────────────────────────────
export const CARD_NETWORKS = {
  VISA:       'visa',
  MASTERCARD: 'mastercard',
  RUPAY:      'rupay',
  AMEX:       'amex',
};

// ─── Misc ─────────────────────────────────────────────────────────────────────
export const CURRENCY = 'INR';
export const MAX_RETRY_COUNT = 3;
export const MOCK_DELAY_UPI_MS  = 1500;
export const MOCK_DELAY_CARD_MS = 1800;
export const MOCK_FAILURE_RATE  = 1 / 20; // 1-in-20 chance of mock failure

export const DEMO_USER_ID = 'demo-user-ramesh-001';
