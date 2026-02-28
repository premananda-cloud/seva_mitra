/**
 * orchestrator_payment_additions.js
 * ════════════════════════════════════════════════════════════════════════════
 * MERGE INSTRUCTION:
 *   Copy the methods below into the existing orchestrator.js class/object,
 *   replacing the stub payment methods described in Section 1.17 of the spec.
 *
 *   Also add the mockPaymentService import at the top of orchestrator.js:
 *     import { mockPaymentService } from './mockPaymentService.js';
 * ════════════════════════════════════════════════════════════════════════════
 *
 * These replace stubs matching:
 *   onPaymentRequested(paymentData) { ... }
 */

// ─── Dependencies (already assumed to be in orchestrator.js) ─────────────────
// import axios from 'axios';

// ─── New payment routing methods ─────────────────────────────────────────────

const paymentMethods = {

  /**
   * Register a user as a customer on PortOne (via backend proxy).
   * Mock mode: returns a fake customer ID instantly.
   *
   * @param {{ userId, name, contact, email, notes }} userData
   * @returns {Promise<{ portoneCustomerId: string, razorpayCustomerId: string|null }>}
   */
  async registerCustomer(userData) {
    if (!this._backendConnected) {
      return {
        portoneCustomerId:  `cust_mock_${Date.now()}`,
        razorpayCustomerId: null,
      };
    }

    const response = await axios.post(
      `${this._backendBaseUrl}/api/v1/payments/customer/register`,
      userData,
      { headers: this._authHeaders() }
    );

    return response.data;
  },

  /**
   * Create a payment order on the chosen gateway.
   * Mock mode: simulates order creation with 300ms delay.
   *
   * @param {{ userId, billId, dept, amount, currency, gateway, method, customerId }} payload
   * @returns {Promise<{ orderId, gateway, gatewayData, expiresAt }>}
   */
  async initiatePayment(payload) {
    if (!this._backendConnected) {
      return mockPaymentService.initiate(payload);
    }

    const response = await axios.post(
      `${this._backendBaseUrl}/api/v1/payments/initiate`,
      payload,
      { headers: this._authHeaders() }
    );

    return response.data;
  },

  /**
   * Complete a payment after the gateway confirms on the client side.
   * Mock mode: simulates receipt generation.
   *
   * @param {{ paymentId, orderId, gateway, gatewayPaymentId }} payload
   * @returns {Promise<{ receipt }>}
   */
  async completePayment(payload) {
    if (!this._backendConnected) {
      return mockPaymentService.complete(payload);
    }

    const response = await axios.post(
      `${this._backendBaseUrl}/api/v1/payments/complete`,
      payload,
      { headers: this._authHeaders() }
    );

    return response.data;
  },

  /**
   * Poll payment status.
   * @param {{ gateway: string, paymentId: string }} params
   * @returns {Promise<{ verified: boolean, status: string }>}
   */
  async verifyPayment({ gateway, paymentId }) {
    if (!this._backendConnected) {
      return { verified: true, status: 'SUCCESS' };
    }

    const response = await axios.get(
      `${this._backendBaseUrl}/api/v1/payments/status/${paymentId}`,
      { headers: this._authHeaders() }
    );

    return response.data;
  },

  /**
   * Fetch payment history for a user.
   * @param {string} userId
   * @returns {Promise<Payment[]>}
   */
  async getPaymentHistory(userId) {
    if (!this._backendConnected) {
      const { default: localDB } = await import('../localdb/localDB.js');
      return localDB.getPaymentsByUserId(userId);
    }

    const response = await axios.get(
      `${this._backendBaseUrl}/api/v1/payments/history/${userId}`,
      { headers: this._authHeaders() }
    );

    return response.data;
  },

  /**
   * Fetch pending bills for a department.
   * @param {string} userId
   * @param {string} dept
   * @returns {Promise<Bill[]>}
   */
  async getBills(userId, dept) {
    if (!this._backendConnected) {
      const { default: localDB } = await import('../localdb/localDB.js');
      return localDB.getBillsByUserAndDept(userId, dept);
    }

    const response = await axios.get(
      `${this._backendBaseUrl}/api/v1/${dept}/bills`,
      { params: { userId }, headers: this._authHeaders() }
    );

    return response.data;
  },
};

export default paymentMethods;


// ─────────────────────────────────────────────────────────────────────────────
// mockPaymentService.js
// Create this as a sibling file: modules/orchestrator/mockPaymentService.js
// ─────────────────────────────────────────────────────────────────────────────
//
// import { generateReferenceNo } from '../payment/paymentUtils.js';
// import { MOCK_DELAY_UPI_MS, MOCK_DELAY_CARD_MS } from '../payment/constants.js';
//
// export const mockPaymentService = {
//   async initiate({ method }) {
//     await new Promise(r => setTimeout(r, 300));
//     return {
//       orderId:     `order_mock_${Date.now()}`,
//       paymentId:   crypto.randomUUID(),
//       gateway:     'mock',
//       gatewayData: {},
//       expiresAt:   new Date(Date.now() + 15 * 60000).toISOString(),
//       mockDelay:   method === 'upi' ? MOCK_DELAY_UPI_MS : MOCK_DELAY_CARD_MS,
//       mode:        'mock',
//     };
//   },
//   async complete({ paymentId, orderId }) {
//     const refNo = generateReferenceNo('electricity');
//     return {
//       receipt: {
//         referenceNo: refNo,
//         amount:      null,
//         dept:        'electricity',
//         method:      'upi',
//         paidAt:      new Date().toISOString(),
//         consumerNo:  null,
//       }
//     };
//   },
// };
