/**
 * paymentUtils.js
 * Pure utility functions — no side effects, safe to unit-test in isolation.
 * No imports from other payment modules.
 */

import { CARD_NETWORKS } from './constants.js';

// ─── INR Formatting ───────────────────────────────────────────────────────────

/**
 * Formats a number as an INR currency string.
 * @param {number} amount
 * @returns {string} e.g. '₹1,847.00'
 */
export function formatINR(amount) {
  if (amount == null || isNaN(amount)) return '₹0.00';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

/**
 * Parses an INR-formatted string back to a float.
 * @param {string} str  e.g. '₹1,847.00' or '1847'
 * @returns {number}
 */
export function parseINR(str) {
  if (typeof str === 'number') return str;
  const cleaned = String(str).replace(/[₹,\s]/g, '');
  const val = parseFloat(cleaned);
  return isNaN(val) ? 0 : val;
}

// ─── UPI Validation ───────────────────────────────────────────────────────────

const KNOWN_VPA_HANDLES = [
  'okicici', 'oksbi', 'okaxis', 'okhdfcbank',
  'ybl',     'ibl',  'axl',    'paytm',
  'apl',     'upi',  'icici',  'sbi',
  'hdfc',    'axis', 'kotak',  'yesbank',
];

/**
 * Validates a UPI VPA/ID.
 * @param {string} id  e.g. 'ramesh@okicici'
 * @returns {{ valid: boolean, error: string|null }}
 */
export function validateUPIId(id) {
  if (!id || typeof id !== 'string') {
    return { valid: false, error: 'UPI ID is required' };
  }

  if (/\s/.test(id)) {
    return { valid: false, error: 'UPI ID cannot contain spaces' };
  }

  const parts = id.split('@');
  if (parts.length !== 2) {
    return { valid: false, error: 'UPI ID must contain exactly one @ symbol' };
  }

  const [username, handle] = parts;

  if (username.length < 3 || username.length > 50) {
    return { valid: false, error: 'Username part must be 3–50 characters' };
  }

  if (!/^[a-zA-Z0-9.\-_]+$/.test(username)) {
    return { valid: false, error: 'Username can only contain letters, numbers, dots, hyphens' };
  }

  if (!handle || handle.length === 0) {
    return { valid: false, error: 'Bank handle is required after @' };
  }

  if (id.length > 50) {
    return { valid: false, error: 'UPI ID is too long (max 50 characters)' };
  }

  return { valid: true, error: null };
}

// ─── Card Validation ──────────────────────────────────────────────────────────

/**
 * Luhn algorithm check.
 * @param {string} num  digits only
 * @returns {boolean}
 */
function luhnCheck(num) {
  let sum = 0;
  let isEven = false;
  for (let i = num.length - 1; i >= 0; i--) {
    let digit = parseInt(num[i], 10);
    if (isEven) {
      digit *= 2;
      if (digit > 9) digit -= 9;
    }
    sum += digit;
    isEven = !isEven;
  }
  return sum % 10 === 0;
}

/**
 * Detects card network from card number prefix.
 * @param {string} digits
 * @returns {'visa'|'mastercard'|'rupay'|'amex'|null}
 */
function detectCardNetwork(digits) {
  if (/^4/.test(digits)) return CARD_NETWORKS.VISA;
  if (/^(5[1-5]|2[2-7])/.test(digits)) return CARD_NETWORKS.MASTERCARD;
  if (/^(6[0-9]{15}|508[5-9]|6069|607[0-9]|608[0-4])/.test(digits)) return CARD_NETWORKS.RUPAY;
  if (/^3[47]/.test(digits)) return CARD_NETWORKS.AMEX;
  return null;
}

/**
 * Validates a credit/debit card number using Luhn algorithm.
 * @param {string} num  may include spaces
 * @returns {{ valid: boolean, network: string|null }}
 */
export function validateCardNumber(num) {
  if (!num) return { valid: false, network: null };
  const digits = num.replace(/\s/g, '');
  if (!/^\d+$/.test(digits)) return { valid: false, network: null };
  if (digits.length < 13 || digits.length > 19) return { valid: false, network: null };

  const network = detectCardNetwork(digits);
  const valid = luhnCheck(digits);

  return { valid, network };
}

/**
 * Validates card expiry date.
 * @param {string} mm  e.g. '03'
 * @param {string} yy  e.g. '28'
 * @returns {{ valid: boolean, error: string|null }}
 */
export function validateExpiry(mm, yy) {
  const month = parseInt(mm, 10);
  const year  = parseInt(yy, 10) + 2000;

  if (isNaN(month) || month < 1 || month > 12) {
    return { valid: false, error: 'Invalid month' };
  }

  const now = new Date();
  const expiry = new Date(year, month - 1, 1);
  const thisMonth = new Date(now.getFullYear(), now.getMonth(), 1);

  if (expiry < thisMonth) {
    return { valid: false, error: 'Card has expired' };
  }

  return { valid: true, error: null };
}

/**
 * Validates CVV.
 * Visa/MC/RuPay: 3 digits. Amex: 4 digits.
 * @param {string} cvv
 * @param {string|null} network
 * @returns {{ valid: boolean }}
 */
export function validateCVV(cvv, network) {
  if (!cvv) return { valid: false };
  const digits = cvv.replace(/\D/g, '');
  const required = network === CARD_NETWORKS.AMEX ? 4 : 3;
  return { valid: digits.length === required };
}

/**
 * Masks a card number for display.
 * @param {string} num  raw or space-formatted card number
 * @returns {string}  e.g. '•••• •••• •••• 4242'
 */
export function maskCardNumber(num) {
  if (!num) return '';
  const digits = num.replace(/\s/g, '');
  const last4 = digits.slice(-4);
  const masked = '•'.repeat(Math.max(0, digits.length - 4));
  const combined = masked + last4;
  return combined.replace(/(.{4})/g, '$1 ').trim();
}

// ─── Reference Number ─────────────────────────────────────────────────────────

let _refCounter = 47; // starts at 47 for demo aesthetic

/**
 * Generates a display-friendly payment reference number.
 * @param {string} dept  'electricity'|'gas'|'water'
 * @returns {string}  e.g. 'PAY-ELEC-20260302-0047'
 */
export function generateReferenceNo(dept) {
  const deptCode = {
    electricity: 'ELEC',
    gas:         'GAS',
    water:       'WATR',
  }[dept] ?? 'PAY';

  const now = new Date();
  const dateStr = [
    now.getFullYear(),
    String(now.getMonth() + 1).padStart(2, '0'),
    String(now.getDate()).padStart(2, '0'),
  ].join('');

  _refCounter++;
  const seq = String(_refCounter).padStart(4, '0');

  return `PAY-${deptCode}-${dateStr}-${seq}`;
}

// ─── Phone Formatting ─────────────────────────────────────────────────────────

/**
 * Prepends +91 country code to a 10-digit Indian phone number.
 * @param {string} phone  e.g. '9876543210'
 * @returns {string}  e.g. '+919876543210'
 */
export function formatPhoneForGateway(phone) {
  if (!phone) return '';
  const digits = phone.replace(/\D/g, '');
  if (digits.startsWith('91') && digits.length === 12) return `+${digits}`;
  if (digits.length === 10) return `+91${digits}`;
  return `+${digits}`;
}

// ─── Gateway Helpers ──────────────────────────────────────────────────────────

/**
 * Returns the display name for a gateway code.
 * @param {string} code
 * @returns {string}
 */
export function getGatewayDisplayName(code) {
  const names = { portone: 'PortOne', razorpay: 'Razorpay', mock: 'Demo' };
  return names[code] ?? code;
}

/**
 * Checks if the browser has network connectivity.
 * @returns {boolean}
 */
export function isNetworkAvailable() {
  return typeof navigator !== 'undefined' ? navigator.onLine : true;
}

// ─── Card Auto-Formatting ─────────────────────────────────────────────────────

/**
 * Auto-formats a card number string with spaces every 4 digits.
 * @param {string} raw  raw digits (may already have spaces)
 * @returns {string}  e.g. '4242 4242 4242 4242'
 */
export function formatCardNumber(raw) {
  const digits = raw.replace(/\D/g, '').slice(0, 16);
  return digits.replace(/(.{4})/g, '$1 ').trim();
}

/**
 * Auto-formats expiry input as MM/YY.
 * @param {string} raw
 * @returns {string}  e.g. '03/28'
 */
export function formatExpiry(raw) {
  const digits = raw.replace(/\D/g, '').slice(0, 4);
  if (digits.length <= 2) return digits;
  return `${digits.slice(0, 2)}/${digits.slice(2)}`;
}
