/**
 * paymentService.js
 * The only file in the payment module that talks to the orchestrator.
 * All components call paymentService — never the orchestrator directly.
 *
 * Routing logic:
 *   if orchestrator.isConnected() → HTTP → real backend
 *   else                          → localDB / mock simulation
 */

import { v4 as uuidv4 } from 'uuid';
import {
  PAYMENT_STATUS,
  GATEWAYS,
  MOCK_DELAY_UPI_MS,
  MOCK_DELAY_CARD_MS,
  MOCK_FAILURE_RATE,
  DEMO_USER_ID,
} from './constants.js';
import { generateReferenceNo, formatPhoneForGateway } from './paymentUtils.js';
import offlineQueue from './offlineQueue.js';

// Dynamic imports to avoid circular deps at module load time
async function getOrchestrator() {
  const { default: orch } = await import('../orchestrator/orchestrator.js');
  return orch;
}
async function getLocalDB() {
  const { default: db } = await import('../localdb/localDB.js');
  return db;
}

// ─── Mock Helpers ─────────────────────────────────────────────────────────────

function mockDelay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function shouldMockFail() {
  return Math.random() < MOCK_FAILURE_RATE;
}

// ─── paymentService ───────────────────────────────────────────────────────────

export const paymentService = {

  /**
   * Ensures the user has a gateway customer profile.
   * On first payment: creates the profile silently in the background.
   * Returns the profile with portoneCustomerId etc.
   *
   * @param {string} userId
   * @returns {Promise<object>}
   */
  async getOrCreateCustomerProfile(userId) {
    const orchestrator = await getOrchestrator();
    const db = await getLocalDB();

    // 1. Check local cache first
    const cached = await db.getPaymentProfile(userId);
    if (cached?.portoneCustomerId) {
      return cached;
    }

    // 2. Fetch user data for registration
    const user = await db.getUserById(userId);
    if (!user) throw new Error('User not found');

    const email = user.email ?? `${user.phone}@koisk.local`;
    const contact = formatPhoneForGateway(user.phone);

    if (!orchestrator.isConnected()) {
      // Mock mode: return a fake customer ID instantly
      const mockProfile = {
        id:                  userId,
        userId,
        portoneCustomerId:   `cust_mock_${Date.now()}`,
        razorpayCustomerId:  null,
        name:                user.name,
        contact,
        email,
        defaultMethod:       null,
        preferredGateway:    'portone',
        createdAt:           new Date().toISOString(),
        syncedToBackend:     false,
      };
      await db.savePaymentProfile(mockProfile);
      return mockProfile;
    }

    // Real mode: register with backend
    const result = await orchestrator.registerCustomer({
      userId,
      name:    user.name,
      contact,
      email,
      notes:   { koisk_user_id: userId },
    });

    const profile = {
      id:                  userId,
      userId,
      portoneCustomerId:   result.portoneCustomerId,
      razorpayCustomerId:  result.razorpayCustomerId ?? null,
      name:                user.name,
      contact,
      email,
      defaultMethod:       null,
      preferredGateway:    'portone',
      createdAt:           new Date().toISOString(),
      syncedToBackend:     true,
    };
    await db.savePaymentProfile(profile);
    return profile;
  },

  /**
   * Fetch pending bills for a department.
   * Mock mode: reads from localDB bills store.
   * Real mode: GET /api/v1/{dept}/bills
   *
   * @param {string} userId
   * @param {string} dept  'electricity'|'gas'|'water'
   * @returns {Promise<Bill[]>}
   */
  async getPendingBills(userId, dept) {
    const orchestrator = await getOrchestrator();
    const db = await getLocalDB();

    if (!orchestrator.isConnected()) {
      return db.getBillsByUserAndDept(userId, dept);
    }

    const bills = await orchestrator.getBills(userId, dept);
    // Cache locally for offline access
    for (const bill of bills) {
      await db.saveBill(bill);
    }
    return bills;
  },

  /**
   * Initiate a payment — creates a gateway order.
   * Mock mode: generates a fake orderId with artificial delay.
   * Real mode: POST /api/v1/payments/initiate
   *
   * @param {{ userId, billId, amount, dept, method, gateway }} params
   * @returns {Promise<{ orderId, gatewayData, mode: 'mock'|'real' }>}
   */
  async initiatePayment({ userId, billId, amount, dept, method, gateway }) {
    const orchestrator = await getOrchestrator();
    const db = await getLocalDB();

    if (!orchestrator.isConnected()) {
      // Mock simulation
      const delay = method === 'upi' ? MOCK_DELAY_UPI_MS : MOCK_DELAY_CARD_MS;
      await mockDelay(300); // order creation delay

      const paymentRecord = {
        id:               uuidv4(),
        userId,
        dept,
        type:             'BILL_PAYMENT',
        billRef:          billId,
        amount,
        currency:         'INR',
        gateway:          GATEWAYS.MOCK,
        gatewayPaymentId: null,
        gatewayOrderId:   null,
        method,
        status:           PAYMENT_STATUS.PENDING,
        referenceNo:      null,
        receiptData:      null,
        createdAt:        new Date().toISOString(),
        paidAt:           null,
        syncedToBackend:  false,
      };
      await db.savePayment(paymentRecord);

      return {
        orderId:     `order_mock_${Date.now()}`,
        paymentId:   paymentRecord.id,
        gatewayData: {},
        mode:        'mock',
        mockDelay:   delay,
      };
    }

    // Real mode
    const profile = await this.getOrCreateCustomerProfile(userId);
    const result = await orchestrator.initiatePayment({
      userId,
      billId,
      dept,
      amount,
      currency:   'INR',
      gateway,
      method,
      customerId: profile.portoneCustomerId,
    });

    return { ...result, mode: 'real' };
  },

  /**
   * Complete a payment after the gateway confirms on the client side.
   * Mock mode: simulates success/failure, saves receipt to localDB.
   * Real mode: POST /api/v1/payments/complete
   *
   * @param {{ paymentId, orderId, gateway, gatewayPaymentId, dept, method }} params
   * @returns {Promise<Receipt>}
   */
  async completePayment({ paymentId, orderId, gateway, gatewayPaymentId, dept, method, mockDelay: delayMs }) {
    const orchestrator = await getOrchestrator();
    const db = await getLocalDB();

    if (!orchestrator.isConnected() || gateway === GATEWAYS.MOCK) {
      // Simulate processing time
      if (delayMs) await mockDelay(delayMs);

      // 1-in-20 chance of mock failure
      if (shouldMockFail()) {
        const payment = await db.getPaymentById(paymentId);
        if (payment) {
          payment.status = PAYMENT_STATUS.FAILED;
          await db.savePayment(payment);
        }
        throw new Error('Payment declined by bank (demo failure simulation)');
      }

      // Success path
      const referenceNo = generateReferenceNo(dept);
      const paidAt = new Date().toISOString();

      const receipt = {
        referenceNo,
        amount:     null, // filled from payment record
        dept,
        method,
        paidAt,
        consumerNo: null, // filled from bill record
      };

      const payment = await db.getPaymentById(paymentId);
      if (payment) {
        payment.status           = PAYMENT_STATUS.SUCCESS;
        payment.gatewayPaymentId = `pay_mock_${Date.now()}`;
        payment.gatewayOrderId   = orderId;
        payment.referenceNo      = referenceNo;
        payment.paidAt           = paidAt;
        receipt.amount           = payment.amount;

        // Pull consumerNo from the bill
        const bill = await db.getBillById(payment.billRef);
        if (bill) {
          receipt.consumerNo = bill.consumerNo;
          bill.status        = 'PAID';
          bill.paidPaymentId = paymentId;
          await db.saveBill(bill);
        }

        payment.receiptData     = receipt;
        payment.syncedToBackend = false;
        await db.savePayment(payment);
      }

      return receipt;
    }

    // Real mode
    const result = await orchestrator.completePayment({
      paymentId,
      orderId,
      gateway,
      gatewayPaymentId,
    });

    // Normalise camelCase response from backend
    return result.receipt ?? result;
  },

  /**
   * Handle a payment failure — queue offline if a network issue caused it.
   *
   * @param {{ error: Error, paymentData: object }} params
   * @returns {Promise<{ queued: boolean, message: string }>}
   */
  async handleFailure({ error, paymentData }) {
    const isNetworkError =
      error.message?.toLowerCase().includes('network') ||
      error.message?.toLowerCase().includes('fetch') ||
      !navigator.onLine;

    if (isNetworkError && paymentData) {
      const { queueId } = await offlineQueue.add({
        action:  'PAYMENT_COMPLETE',
        payload: paymentData,
      });
      return {
        queued:  true,
        message: 'Payment queued — will retry when connection is restored.',
        queueId,
      };
    }

    return {
      queued:  false,
      message: error.message ?? 'Payment failed. Please try again.',
    };
  },

  /**
   * Get payment history for the dashboard.
   * Mock mode: reads localDB payments store.
   * Real mode: GET /api/v1/payments/history/{userId}
   *
   * @param {string} userId
   * @returns {Promise<Payment[]>}
   */
  async getHistory(userId) {
    const orchestrator = await getOrchestrator();
    const db = await getLocalDB();

    if (!orchestrator.isConnected()) {
      return db.getPaymentsByUserId(userId);
    }

    return orchestrator.getPaymentHistory(userId);
  },
};

export default paymentService;
