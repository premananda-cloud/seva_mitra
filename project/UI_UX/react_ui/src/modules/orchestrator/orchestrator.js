// orchestrator.js - REAL IMPLEMENTATION
import axios from 'axios';

class Orchestrator {
  constructor() {
    this._backendConnected = false; // Set to true when backend is ready
    this._backendBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:3000';
    this._mockMode = true; // Toggle for development
  }

  isConnected() {
    return this._backendConnected;
  }

  _authHeaders() {
    const token = localStorage.getItem('auth_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  // Payment methods
  async registerCustomer(userData) {
    if (this._mockMode || !this._backendConnected) {
      return {
        portoneCustomerId: `cust_mock_${Date.now()}`,
        razorpayCustomerId: null,
      };
    }

    try {
      const response = await axios.post(
        `${this._backendBaseUrl}/api/v1/payments/customer/register`,
        userData,
        { headers: this._authHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error registering customer:', error);
      throw error;
    }
  }

  async initiatePayment(payload) {
    if (this._mockMode || !this._backendConnected) {
      // Import dynamically to avoid circular dependencies
      const { mockPaymentService } = await import('./mockPaymentService.js');
      return mockPaymentService.initiate(payload);
    }

    try {
      const response = await axios.post(
        `${this._backendBaseUrl}/api/v1/payments/initiate`,
        payload,
        { headers: this._authHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error initiating payment:', error);
      throw error;
    }
  }

  async completePayment(payload) {
    if (this._mockMode || !this._backendConnected) {
      const { mockPaymentService } = await import('./mockPaymentService.js');
      return mockPaymentService.complete(payload);
    }

    try {
      const response = await axios.post(
        `${this._backendBaseUrl}/api/v1/payments/complete`,
        payload,
        { headers: this._authHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error completing payment:', error);
      throw error;
    }
  }

  async verifyPayment({ gateway, paymentId }) {
    if (this._mockMode || !this._backendConnected) {
      return { verified: true, status: 'SUCCESS' };
    }

    try {
      const response = await axios.get(
        `${this._backendBaseUrl}/api/v1/payments/status/${paymentId}`,
        { headers: this._authHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error verifying payment:', error);
      throw error;
    }
  }

  async getPaymentHistory(userId) {
    if (this._mockMode || !this._backendConnected) {
      const localDB = (await import('../localdb/localDB.js')).default;
      return localDB.getPaymentsByUserId(userId);
    }

    try {
      const response = await axios.get(
        `${this._backendBaseUrl}/api/v1/payments/history/${userId}`,
        { headers: this._authHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching payment history:', error);
      return [];
    }
  }

  async getBills(userId, dept) {
    if (this._mockMode || !this._backendConnected) {
      const localDB = (await import('../localdb/localDB.js')).default;
      return localDB.getBillsByUserAndDept(userId, dept);
    }

    try {
      const response = await axios.get(
        `${this._backendBaseUrl}/api/v1/${dept}/bills`,
        { params: { userId }, headers: this._authHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching bills:', error);
      return [];
    }
  }
}

// Create singleton instance
const orchestrator = new Orchestrator();
export default orchestrator;