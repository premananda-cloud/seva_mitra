/**
 * PaymentFlow.jsx
 * Top-level payment wizard — 3-step flow.
 * Manages the IDLE → BILL_SUMMARY → METHOD_SELECT → PROCESSING → SUCCESS/FAILED state machine.
 * Delegates rendering to sub-components based on current step.
 *
 * Props:
 *   billId  {string}    — which bill to pay
 *   dept    {string}    — 'electricity'|'gas'|'water'
 *   onClose {function}  — called when citizen exits without paying
 */

import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import usePaymentStore from '../../modules/payment/paymentStore.js';
import paymentService from '../../modules/payment/paymentService.js';
import { portoneAdapter, razorpayAdapter } from '../../modules/payment/gatewayAdapters.js';
import { formatINR, isNetworkAvailable } from '../../modules/payment/paymentUtils.js';
import {
  PAYMENT_STEPS,
  GATEWAYS,
  DEPT_ICONS,
  DEPT_DISPLAY_NAMES,
} from '../../modules/payment/constants.js';
import OfflineBanner from './OfflineBanner.jsx';
import PaymentMethodSelector from './PaymentMethodSelector.jsx';

// ─── Step indicator ───────────────────────────────────────────────────────────

function StepDots({ current }) {
  const steps = ['Summary', 'Method', 'Done'];
  const idx = { BILL_SUMMARY: 0, METHOD_SELECT: 1, INPUT: 1, PROCESSING: 2, SUCCESS: 2, FAILED: 2 };
  const active = idx[current] ?? 0;

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px', justifyContent: 'center' }}>
      {steps.map((label, i) => (
        <React.Fragment key={label}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
            <div style={{
              width:           '28px', height: '28px',
              borderRadius:    '50%',
              backgroundColor: i <= active ? '#1A56DB' : '#E5E7EB',
              color:           i <= active ? 'white' : '#9CA3AF',
              display:         'flex', alignItems: 'center', justifyContent: 'center',
              fontWeight:      700, fontSize: '13px',
              transition:      'background-color 0.2s',
            }}>
              {i < active ? '✓' : i + 1}
            </div>
            <span style={{ fontSize: '11px', color: i <= active ? '#1A56DB' : '#9CA3AF' }}>{label}</span>
          </div>
          {i < steps.length - 1 && (
            <div style={{
              flex:            1,
              height:          '2px',
              backgroundColor: i < active ? '#1A56DB' : '#E5E7EB',
              marginBottom:    '16px',
              transition:      'background-color 0.2s',
            }} />
          )}
        </React.Fragment>
      ))}
    </div>
  );
}

// ─── Bill Summary (Step 1) ────────────────────────────────────────────────────

function BillSummary({ bill, dept, onContinue, onClose }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{
        backgroundColor: '#F0F9FF',
        border:          '1px solid #BAE6FD',
        borderRadius:    '12px',
        padding:         '20px',
        display:         'flex',
        flexDirection:   'column',
        gap:             '12px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '28px' }}>{DEPT_ICONS[dept] ?? '🏠'}</span>
          <div>
            <h2 style={{ margin: 0, fontSize: '18px', color: '#0C4A6E' }}>
              {DEPT_DISPLAY_NAMES[dept] ?? dept} Bill
            </h2>
            <p style={{ margin: '2px 0 0', fontSize: '13px', color: '#0369A1' }}>
              Consumer: {bill.consumerNo}
            </p>
          </div>
        </div>

        {[
          ['Billing Period', formatBillMonth(bill.billMonth)],
          ['Due Date',       formatDate(bill.dueDate)],
        ].map(([label, value]) => (
          <div key={label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px' }}>
            <span style={{ color: '#6B7280' }}>{label}</span>
            <span style={{ color: '#111827', fontWeight: 500 }}>{value}</span>
          </div>
        ))}

        <hr style={{ border: 'none', borderTop: '1px solid #BAE6FD', margin: '4px 0' }} />

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontWeight: 700, fontSize: '16px', color: '#0C4A6E' }}>Amount Due</span>
          <span style={{ fontWeight: 800, fontSize: '24px', color: '#0369A1' }}>
            {formatINR(bill.amountDue)}
          </span>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '10px' }}>
        <button
          type="button"
          onClick={onClose}
          style={{
            flex:            1,
            padding:         '14px',
            border:          '2px solid #E5E7EB',
            borderRadius:    '10px',
            backgroundColor: 'white',
            color:           '#6B7280',
            fontSize:        '15px',
            cursor:          'pointer',
          }}
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={onContinue}
          style={{
            flex:            2,
            padding:         '14px',
            border:          'none',
            borderRadius:    '10px',
            backgroundColor: '#1A56DB',
            color:           'white',
            fontSize:        '15px',
            fontWeight:      700,
            cursor:          'pointer',
          }}
        >
          Continue to Payment →
        </button>
      </div>
    </div>
  );
}

// ─── Processing Screen ────────────────────────────────────────────────────────

function ProcessingScreen() {
  return (
    <div style={{
      display:        'flex',
      flexDirection:  'column',
      alignItems:     'center',
      justifyContent: 'center',
      padding:        '48px 16px',
      gap:            '20px',
    }}>
      <div style={{
        width:        '56px', height: '56px',
        border:       '4px solid #E0E7FF',
        borderTop:    '4px solid #1A56DB',
        borderRadius: '50%',
        animation:    'spin 0.9s linear infinite',
      }} />
      <p style={{ margin: 0, fontSize: '16px', color: '#374151', fontWeight: 500 }}>
        Processing your payment…
      </p>
      <p style={{ margin: 0, fontSize: '13px', color: '#9CA3AF' }}>
        Please do not close this window
      </p>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

// ─── Failed Screen ────────────────────────────────────────────────────────────

function FailedScreen({ error, onRetry, onClose }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px', padding: '24px 0' }}>
      <div style={{ fontSize: '48px' }}>❌</div>
      <h2 style={{ margin: 0, color: '#DC2626', fontSize: '20px' }}>Payment Failed</h2>
      {error && (
        <p style={{ margin: 0, color: '#6B7280', fontSize: '14px', textAlign: 'center' }}>{error}</p>
      )}
      <div style={{ display: 'flex', gap: '10px', width: '100%' }}>
        <button
          type="button"
          onClick={onClose}
          style={{
            flex: 1, padding: '13px', border: '2px solid #E5E7EB',
            borderRadius: '10px', backgroundColor: 'white', color: '#6B7280',
            fontSize: '15px', cursor: 'pointer',
          }}
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={onRetry}
          style={{
            flex: 2, padding: '13px', border: 'none',
            borderRadius: '10px', backgroundColor: '#1A56DB', color: 'white',
            fontSize: '15px', fontWeight: 700, cursor: 'pointer',
          }}
        >
          Try Again
        </button>
      </div>
    </div>
  );
}

// ─── PaymentFlow ──────────────────────────────────────────────────────────────

export default function PaymentFlow({ billId, dept, onClose }) {
  const navigate = useNavigate();
  const {
    step,
    activeBill,
    selectedGateway,
    selectedMethod,
    upiId,
    cardData,
    setStep,
    setActiveBill,
    setLoading,
    setError,
    setReceipt,
    setOffline,
    setQueuedCount,
    clearCardData,
    error,
    reset,
  } = usePaymentStore();

  // Load bill on mount
  useEffect(() => {
    async function loadBill() {
      try {
        const bills = await paymentService.getPendingBills('current-user', dept);
        const bill = bills.find((b) => b.id === billId) ?? bills[0];
        if (bill) {
          setActiveBill(bill);
          setStep(PAYMENT_STEPS.BILL_SUMMARY);
        }
      } catch (err) {
        setError('Could not load bill details. Please try again.');
      }
    }
    loadBill();

    // Monitor offline status
    setOffline(!isNetworkAvailable());
    const handleOnline  = () => setOffline(false);
    const handleOffline = () => setOffline(true);
    window.addEventListener('online',  handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online',  handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [billId, dept]);

  async function handlePay() {
    if (!activeBill) return;
    setStep(PAYMENT_STEPS.PROCESSING);
    setLoading(true);

    try {
      // Determine current user ID (replace with auth store lookup)
      const userId = 'current-user';

      // Step 1: Initiate payment (creates order)
      const { orderId, paymentId, mode, mockDelay } = await paymentService.initiatePayment({
        userId,
        billId:  activeBill.id,
        amount:  activeBill.amountDue,
        dept,
        method:  selectedMethod,
        gateway: selectedGateway,
      });

      // Step 2: Open gateway UI (real) OR wait for mock delay
      let gatewayPaymentId = null;

      if (mode === 'real') {
        const profile = await paymentService.getOrCreateCustomerProfile(userId);
        const prefill  = { name: profile.name, contact: profile.contact, email: profile.email };

        if (selectedGateway === GATEWAYS.PORTONE) {
          const result = await portoneAdapter.openPayment({
            orderId,
            customerId: profile.portoneCustomerId,
            amount:     activeBill.amountDue,
            currency:   'INR',
            method:     selectedMethod,
            prefill,
          });
          gatewayPaymentId = result.paymentId;
        } else {
          const result = await razorpayAdapter.openPayment({
            orderId,
            amount:  activeBill.amountDue,
            currency:'INR',
            prefill,
          });
          gatewayPaymentId = result.razorpay_payment_id;
        }
      }

      // IMPORTANT: Clear card data from memory immediately after SDK call
      clearCardData();

      // Step 3: Complete / verify
      const receipt = await paymentService.completePayment({
        paymentId,
        orderId,
        gateway:         selectedGateway,
        gatewayPaymentId,
        dept,
        method:          selectedMethod,
        mockDelay,
      });

      setReceipt(receipt);
      navigate(`/receipt/${paymentId}`);

    } catch (err) {
      clearCardData(); // always clear card data

      const { queued } = await paymentService.handleFailure({
        error:       err,
        paymentData: { billId: activeBill?.id, dept, method: selectedMethod },
      });

      if (queued) {
        const count = await import('../../modules/payment/offlineQueue.js')
          .then((m) => m.default.getPendingCount());
        setQueuedCount(count);
        setStep(PAYMENT_STEPS.OFFLINE_QUEUED);
      } else {
        setError(err.message ?? 'Payment failed. Please try again.');
        setStep(PAYMENT_STEPS.FAILED);
      }
    }
  }

  function handleClose() {
    if (step === PAYMENT_STEPS.PROCESSING) return; // don't allow close mid-payment
    if (
      step !== PAYMENT_STEPS.BILL_SUMMARY &&
      step !== PAYMENT_STEPS.IDLE &&
      !window.confirm('Are you sure you want to cancel this payment?')
    ) {
      return;
    }
    reset();
    onClose?.();
  }

  // ─── Render ─────────────────────────────────────────────────────────────────

  return (
    <div
      style={{
        maxWidth:        '480px',
        margin:          '0 auto',
        padding:         '24px 20px',
        backgroundColor: 'white',
        borderRadius:    '16px',
        boxShadow:       '0 4px 24px rgba(0,0,0,0.10)',
        minHeight:       '360px',
      }}
    >
      <OfflineBanner />

      {step !== PAYMENT_STEPS.PROCESSING &&
       step !== PAYMENT_STEPS.SUCCESS &&
       step !== PAYMENT_STEPS.IDLE && (
        <StepDots current={step} />
      )}

      {(step === PAYMENT_STEPS.IDLE || !activeBill) && (
        <div style={{ textAlign: 'center', padding: '40px', color: '#9CA3AF' }}>
          Loading bill…
        </div>
      )}

      {step === PAYMENT_STEPS.BILL_SUMMARY && activeBill && (
        <BillSummary
          bill={activeBill}
          dept={dept}
          onContinue={() => setStep(PAYMENT_STEPS.METHOD_SELECT)}
          onClose={handleClose}
        />
      )}

      {(step === PAYMENT_STEPS.METHOD_SELECT || step === PAYMENT_STEPS.INPUT) && (
        <PaymentMethodSelector onPay={handlePay} />
      )}

      {step === PAYMENT_STEPS.PROCESSING && <ProcessingScreen />}

      {step === PAYMENT_STEPS.FAILED && (
        <FailedScreen
          error={error}
          onRetry={() => setStep(PAYMENT_STEPS.METHOD_SELECT)}
          onClose={handleClose}
        />
      )}

      {step === PAYMENT_STEPS.OFFLINE_QUEUED && (
        <div style={{ textAlign: 'center', padding: '32px 16px' }}>
          <div style={{ fontSize: '40px', marginBottom: '12px' }}>📡</div>
          <h2 style={{ color: '#92400E', margin: '0 0 8px' }}>Payment Queued</h2>
          <p style={{ color: '#6B7280', fontSize: '14px', margin: '0 0 20px' }}>
            No internet connection. Your payment has been saved and will be processed automatically when connection is restored.
          </p>
          <button
            type="button"
            onClick={handleClose}
            style={{
              padding: '13px 28px', border: 'none',
              borderRadius: '10px', backgroundColor: '#1A56DB',
              color: 'white', fontWeight: 700, fontSize: '15px', cursor: 'pointer',
            }}
          >
            Back to Dashboard
          </button>
        </div>
      )}
    </div>
  );
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatBillMonth(ym) {
  if (!ym) return '—';
  const [year, month] = ym.split('-');
  const date = new Date(parseInt(year), parseInt(month) - 1, 1);
  return date.toLocaleString('en-IN', { month: 'long', year: 'numeric' });
}

function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}
