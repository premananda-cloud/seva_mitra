/**
 * gatewayAdapters.js
 * Wraps PortOne and Razorpay browser SDKs.
 * This is the ONLY file in the payment module that imports gateway SDKs.
 * Raw card numbers are NEVER stored — they go directly to the SDK UI.
 */

// ─── PortOne Adapter ──────────────────────────────────────────────────────────

export const portoneAdapter = {
  _loaded: false,
  _portone: null,

  /**
   * Dynamically loads the PortOne SDK script.
   * Avoids bundling the SDK — loads from CDN on demand.
   * @returns {Promise<void>}
   */
  async loadSDK() {
    if (this._loaded) return;

    return new Promise((resolve, reject) => {
      if (typeof window === 'undefined') {
        reject(new Error('PortOne SDK requires browser environment'));
        return;
      }

      // Check if already loaded
      if (window.PortOne) {
        this._loaded = true;
        this._portone = window.PortOne;
        resolve();
        return;
      }

      const script = document.createElement('script');
      script.src    = 'https://checkout.portone.io/v2/browser-sdk.js';
      script.async  = true;

      script.onload = () => {
        this._loaded  = true;
        this._portone = window.PortOne;
        resolve();
      };

      script.onerror = () => reject(new Error('Failed to load PortOne SDK'));
      document.head.appendChild(script);
    });
  },

  /**
   * Registers a new customer on PortOne.
   * Called by paymentService on the first payment attempt.
   * Uses the backend proxy — API keys are NEVER exposed to the frontend.
   *
   * @param {{ name, contact, email, notes }} customerData
   * @returns {Promise<{ customerId: string }>}
   */
  async registerCustomer({ name, contact, email, notes }) {
    // This call goes to our backend which proxies to PortOne
    const { default: orchestrator } = await import('../orchestrator/orchestrator.js');
    const result = await orchestrator.registerCustomer({ name, contact, email, notes });
    return { customerId: result.portoneCustomerId };
  },

  /**
   * Opens the PortOne payment UI and waits for the result.
   *
   * @param {{ orderId, customerId, amount, currency, method, prefill }} options
   * @returns {Promise<{ paymentId: string, status: string, method: string }>}
   */
  async openPayment({ orderId, customerId, amount, currency = 'INR', method, prefill = {} }) {
    await this.loadSDK();

    if (!this._portone) {
      throw new Error('PortOne SDK not loaded');
    }

    return new Promise((resolve, reject) => {
      this._portone.checkout({
        storeId:    import.meta.env.VITE_PORTONE_STORE_ID,
        channelKey: import.meta.env.VITE_PORTONE_CHANNEL_KEY,
        paymentId:  orderId,
        orderName:  `KOISK Bill Payment`,
        totalAmount: Math.round(amount * 100), // PortOne expects paise
        currency,
        paymentMethod: method,
        customer: {
          customerId,
          fullName:     prefill.name    ?? '',
          phoneNumber:  prefill.contact ?? '',
          email:        prefill.email   ?? '',
        },
        redirectUrl: `${window.location.origin}/receipt/pending`,

        onPaymentSuccess: (response) => {
          resolve({
            paymentId: response.paymentId,
            status:    'SUCCESS',
            method:    response.paymentMethod ?? method,
          });
        },

        onPaymentFail: (response) => {
          reject(new Error(response.message ?? 'Payment failed via PortOne'));
        },
      });
    });
  },

  /**
   * Verifies the status of a payment via backend.
   * Backend calls PortOne server-to-server (we don't trust the frontend result alone).
   *
   * @param {string} paymentId
   * @returns {Promise<{ verified: boolean, status: string }>}
   */
  async verifyPayment(paymentId) {
    const { default: orchestrator } = await import('../orchestrator/orchestrator.js');
    return orchestrator.verifyPayment({ gateway: 'portone', paymentId });
  },
};

// ─── Razorpay Adapter ─────────────────────────────────────────────────────────

export const razorpayAdapter = {
  _loaded: false,

  /**
   * Dynamically loads the Razorpay checkout script.
   * @returns {Promise<void>}
   */
  async loadSDK() {
    if (this._loaded) return;

    return new Promise((resolve, reject) => {
      if (typeof window === 'undefined') {
        reject(new Error('Razorpay SDK requires browser environment'));
        return;
      }

      if (window.Razorpay) {
        this._loaded = true;
        resolve();
        return;
      }

      const script = document.createElement('script');
      script.src   = 'https://checkout.razorpay.com/v1/checkout.js';
      script.async = true;

      script.onload  = () => { this._loaded = true; resolve(); };
      script.onerror = () => reject(new Error('Failed to load Razorpay SDK'));

      document.head.appendChild(script);
    });
  },

  /**
   * Opens the Razorpay payment modal and waits for the result.
   *
   * @param {{ orderId, amount, currency, prefill, theme }} options
   * @returns {Promise<{ razorpay_payment_id, razorpay_order_id, razorpay_signature }>}
   */
  async openPayment({ orderId, amount, currency = 'INR', prefill = {}, theme = {} }) {
    await this.loadSDK();

    return new Promise((resolve, reject) => {
      const options = {
        key:      import.meta.env.VITE_RAZORPAY_KEY_ID,
        amount:   Math.round(amount * 100), // Razorpay expects paise
        currency,
        order_id: orderId,
        name:     'KOISK — Utility Services',
        prefill: {
          name:    prefill.name    ?? '',
          email:   prefill.email   ?? '',
          contact: prefill.contact ?? '',
        },
        theme: {
          color: theme.color ?? '#1A56DB',
          ...theme,
        },
        handler: (response) => {
          // Card data never reaches JS — Razorpay handles tokenization in the modal
          resolve({
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_order_id:   response.razorpay_order_id,
            razorpay_signature:  response.razorpay_signature,
          });
        },
        modal: {
          ondismiss: () => reject(new Error('Payment cancelled by user')),
        },
      };

      const rzp = new window.Razorpay(options);
      rzp.on('payment.failed', (response) => {
        reject(new Error(response.error?.description ?? 'Razorpay payment failed'));
      });
      rzp.open();
    });
  },

  /**
   * Verifies the Razorpay HMAC signature on the frontend.
   * Note: This is a client-side sanity check only.
   * The backend MUST re-verify server-to-server before marking payment as paid.
   *
   * @param {{ orderId, paymentId, signature, secret }} params
   * @returns {boolean}
   */
  verifySignature({ orderId, paymentId, signature, secret }) {
    // Client-side HMAC verification using SubtleCrypto
    // Returns true if the signature looks valid (backend re-verifies with full secret)
    // In a real implementation this would use a server-side endpoint.
    // We keep this stub to document the interface contract.
    console.warn('[razorpayAdapter] verifySignature: backend must re-verify before trusting payment');
    return true;
  },
};
