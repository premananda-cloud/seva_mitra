/**
 * PaymentFlow.jsx — refactored to use KOISK design system (no inline style props)
 */

import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { clsx } from 'clsx';
import { useAuthStore } from '../../modules/auth/authStore.js';
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
  const idx   = { BILL_SUMMARY: 0, METHOD_SELECT: 1, INPUT: 1, PROCESSING: 2, SUCCESS: 2, FAILED: 2 };
  const active = idx[current] ?? 0;

  return (
    <div className="flex items-center justify-center gap-2 mb-6" role="progressbar" aria-valuenow={active + 1} aria-valuemax={3}>
      {steps.map((label, i) => (
        <React.Fragment key={label}>
          <div className="flex flex-col items-center gap-1">
            <div className={clsx(
              'w-7 h-7 rounded-full flex items-center justify-center text-xs font-display font-bold transition-colors duration-200',
              i <= active ? 'bg-koisk-teal text-white' : 'bg-koisk-surface text-koisk-muted border border-koisk-blue/20'
            )}>
              {i < active ? '✓' : i + 1}
            </div>
            <span className={clsx('text-xs font-body', i <= active ? 'text-koisk-teal font-semibold' : 'text-koisk-muted')}>
              {label}
            </span>
          </div>
          {i < steps.length - 1 && (
            <div className={clsx(
              'flex-1 h-0.5 mb-4 transition-colors duration-200',
              i < active ? 'bg-koisk-teal' : 'bg-koisk-blue/15'
            )} />
          )}
        </React.Fragment>
      ))}
    </div>
  );
}

// ─── Bill Summary (Step 1) ────────────────────────────────────────────────────

function BillSummary({ bill, dept, onContinue, onClose }) {
  return (
    <div className="flex flex-col gap-5">
      <div className="bg-blue-50 border border-blue-200 rounded-2xl p-5 flex flex-col gap-3">
        <div className="flex items-center gap-3">
          <span className="text-3xl" aria-hidden="true">{DEPT_ICONS[dept] ?? '🏠'}</span>
          <div>
            <h2 className="font-display font-bold text-koisk-navy text-lg m-0">
              {DEPT_DISPLAY_NAMES[dept] ?? dept} Bill
            </h2>
            <p className="text-blue-600 font-body text-sm mt-0.5">Consumer: {bill.consumerNo}</p>
          </div>
        </div>

        {[
          ['Billing Period', formatBillMonth(bill.billMonth)],
          ['Due Date',       formatDate(bill.dueDate)],
        ].map(([label, value]) => (
          <div key={label} className="flex justify-between text-sm">
            <span className="text-koisk-muted font-body">{label}</span>
            <span className="text-koisk-navy font-semibold font-body">{value}</span>
          </div>
        ))}

        <hr className="border-blue-200 my-1" />

        <div className="flex justify-between items-center">
          <span className="font-display font-bold text-koisk-navy text-base">Amount Due</span>
          <span className="font-display font-bold text-koisk-teal text-2xl">{formatINR(bill.amountDue)}</span>
        </div>
      </div>

      <div className="flex gap-3">
        <button type="button" onClick={onClose} className="btn-secondary flex-1">
          Cancel
        </button>
        <button type="button" onClick={onContinue} className="btn-primary flex-[2]">
          Continue to Payment →
        </button>
      </div>
    </div>
  );
}

// ─── Processing Screen ────────────────────────────────────────────────────────

function ProcessingScreen() {
  return (
    <div className="flex flex-col items-center justify-center py-12 gap-5" role="status" aria-live="polite">
      <div className="w-14 h-14 border-4 border-koisk-blue/20 border-t-koisk-teal rounded-full animate-spin" />
      <p className="font-display font-semibold text-koisk-navy text-lg m-0">Processing your payment…</p>
      <p className="text-koisk-muted font-body text-sm m-0">Please do not close this window</p>
    </div>
  );
}

// ─── Failed Screen ────────────────────────────────────────────────────────────

function FailedScreen({ error, onRetry, onClose }) {
  return (
    <div className="flex flex-col items-center gap-4 py-6" role="alert">
      <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center text-4xl" aria-hidden="true">❌</div>
      <h2 className="font-display font-bold text-koisk-danger text-xl m-0">Payment Failed</h2>
      {error && <p className="text-koisk-muted font-body text-sm text-center m-0">{error}</p>}
      <div className="flex gap-3 w-full">
        <button type="button" onClick={onClose}  className="btn-secondary flex-1">Cancel</button>
        <button type="button" onClick={onRetry}  className="btn-primary flex-[2]">Try Again</button>
      </div>
    </div>
  );
}

// ─── PaymentFlow ──────────────────────────────────────────────────────────────

export default function PaymentFlow({ billId, dept, onClose }) {
  const navigate = useNavigate();
  const authUser = useAuthStore(s => s.user);
  const {
    step, activeBill, selectedGateway, selectedMethod, upiId, cardData,
    setStep, setActiveBill, setLoading, setError, setReceipt,
    setOffline, setQueuedCount, clearCardData, error, reset,
  } = usePaymentStore();

  useEffect(() => {
    async function loadBill() {
      try {
        const bills = await paymentService.getPendingBills(authUser?.id ?? 'demo-user', dept);
        const bill  = bills.find(b => b.id === billId) ?? bills[0];
        if (bill) { setActiveBill(bill); setStep(PAYMENT_STEPS.BILL_SUMMARY); }
      } catch { setError('Could not load bill details. Please try again.'); }
    }
    loadBill();

    setOffline(!isNetworkAvailable());
    const onOnline  = () => setOffline(false);
    const onOffline = () => setOffline(true);
    window.addEventListener('online',  onOnline);
    window.addEventListener('offline', onOffline);
    return () => { window.removeEventListener('online', onOnline); window.removeEventListener('offline', onOffline); };
  }, [billId, dept]);

  async function handlePay() {
    if (!activeBill) return;
    setStep(PAYMENT_STEPS.PROCESSING);
    setLoading(true);
    try {
      const userId = authUser?.id ?? 'demo-user';
      const { orderId, paymentId, mode, mockDelay } = await paymentService.initiatePayment({
        userId, billId: activeBill.id, amount: activeBill.amountDue,
        dept, method: selectedMethod, gateway: selectedGateway,
      });

      let gatewayPaymentId = null;
      if (mode === 'real') {
        const profile = await paymentService.getOrCreateCustomerProfile(userId);
        const prefill  = { name: profile.name, contact: profile.contact, email: profile.email };
        if (selectedGateway === GATEWAYS.PORTONE) {
          const r = await portoneAdapter.openPayment({ orderId, customerId: profile.portoneCustomerId, amount: activeBill.amountDue, currency: 'INR', method: selectedMethod, prefill });
          gatewayPaymentId = r.paymentId;
        } else {
          const r = await razorpayAdapter.openPayment({ orderId, amount: activeBill.amountDue, currency: 'INR', prefill });
          gatewayPaymentId = r.razorpay_payment_id;
        }
      }
      clearCardData();
      const receipt = await paymentService.completePayment({ paymentId, orderId, gateway: selectedGateway, gatewayPaymentId, dept, method: selectedMethod, mockDelay });
      setReceipt(receipt);
      navigate(`/receipt/${paymentId}`);
    } catch (err) {
      clearCardData();
      const { queued } = await paymentService.handleFailure({ error: err, paymentData: { billId: activeBill?.id, dept, method: selectedMethod } });
      if (queued) {
        const count = await import('../../modules/payment/offlineQueue.js').then(m => m.default.getPendingCount());
        setQueuedCount(count);
        setStep(PAYMENT_STEPS.OFFLINE_QUEUED);
      } else {
        setError(err.message ?? 'Payment failed. Please try again.');
        setStep(PAYMENT_STEPS.FAILED);
      }
    }
  }

  function handleClose() {
    if (step === PAYMENT_STEPS.PROCESSING) return;
    if (step !== PAYMENT_STEPS.BILL_SUMMARY && step !== PAYMENT_STEPS.IDLE &&
        !window.confirm('Are you sure you want to cancel this payment?')) return;
    reset();
    onClose?.();
  }

  return (
    <div className="p-6">
      <OfflineBanner />

      {step !== PAYMENT_STEPS.PROCESSING && step !== PAYMENT_STEPS.SUCCESS && step !== PAYMENT_STEPS.IDLE && (
        <StepDots current={step} />
      )}

      {(step === PAYMENT_STEPS.IDLE || !activeBill) && (
        <div className="text-center py-10 text-koisk-muted font-body">Loading bill…</div>
      )}

      {step === PAYMENT_STEPS.BILL_SUMMARY && activeBill && (
        <BillSummary bill={activeBill} dept={dept} onContinue={() => setStep(PAYMENT_STEPS.METHOD_SELECT)} onClose={handleClose} />
      )}

      {(step === PAYMENT_STEPS.METHOD_SELECT || step === PAYMENT_STEPS.INPUT) && (
        <PaymentMethodSelector onPay={handlePay} />
      )}

      {step === PAYMENT_STEPS.PROCESSING && <ProcessingScreen />}

      {step === PAYMENT_STEPS.FAILED && (
        <FailedScreen error={error} onRetry={() => setStep(PAYMENT_STEPS.METHOD_SELECT)} onClose={handleClose} />
      )}

      {step === PAYMENT_STEPS.OFFLINE_QUEUED && (
        <div className="text-center py-8 px-4" role="status">
          <div className="text-4xl mb-3" aria-hidden="true">📡</div>
          <h2 className="font-display font-bold text-amber-800 text-xl m-0 mb-2">Payment Queued</h2>
          <p className="text-koisk-muted font-body text-sm mb-6">
            No internet connection. Your payment has been saved and will be processed automatically when connection is restored.
          </p>
          <button type="button" onClick={handleClose} className="btn-primary w-full">
            Back to Dashboard
          </button>
        </div>
      )}
    </div>
  );
}

function formatBillMonth(ym) {
  if (!ym) return '—';
  const [year, month] = ym.split('-');
  return new Date(parseInt(year), parseInt(month) - 1, 1).toLocaleString('en-IN', { month: 'long', year: 'numeric' });
}
function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}
