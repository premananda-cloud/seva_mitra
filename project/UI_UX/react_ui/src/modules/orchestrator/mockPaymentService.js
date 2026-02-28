// mockPaymentService.js
export const mockPaymentService = {
  async initiate({ method, amount }) {
    await new Promise(resolve => setTimeout(resolve, 300));
    const paymentId = `pay_mock_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    return {
      orderId: `order_mock_${Date.now()}`,
      paymentId: paymentId,
      gateway: 'mock',
      gatewayData: {
        mockQrCode: 'https://via.placeholder.com/200x200?text=Mock+UPI+QR',
        mockUpiId: 'mock@payments',
      },
      expiresAt: new Date(Date.now() + 15 * 60000).toISOString(),
      mockDelay: method === 'upi' ? 2000 : 1000,
      mode: 'mock',
    };
  },
  
  async complete({ paymentId, orderId }) {
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return {
      receipt: {
        referenceNo: `REF-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
        amount: null,
        dept: 'electricity',
        method: 'upi',
        paidAt: new Date().toISOString(),
        consumerNo: 'CONS-MH-001234',
        transactionId: paymentId,
        orderId: orderId,
      }
    };
  },
};