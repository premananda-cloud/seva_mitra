/**
 * PaymentFlow.jsx
 * Top-level payment wizard — 3-step flow.
 * State machine: IDLE → BILL_SUMMARY → METHOD_SELECT → PROCESSING → SUCCESS/FAILED
 *
 * FIX (Critical): All inline styles replaced with KOISK Tailwind design-system classes.
 * FIX (Critical): window.confirm() replaced with inline CONFIRM_CANCEL step.
 *
 * Props:
 *   billId  {string}    — which bill to pay
 *   dept    {string}    — 'electricity'|'gas'|'water'
 *   onClose {function}  — called when citizen exits without paying
 */

import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
  const idx = { BILL_SUMMARY: 0, METHOD_SELECT: 1, INPUT: 1, PROCESSING: 2, SUCCESS: 2, FAILED: 2 };
  const active = idx[current] ?? 0;

  return (
    <div className="flex items-center justify-center gap-2 mb-6">
      {steps.map((label, i) => (
        <React.Fragment key={label}>
          <div className="flex flex-col items-center gap-1">
            <div className={[
              'w-7 h-7 rounded-full flex items-center justify-center font-display font-bold text-sm transition-colors duration-200',
              i <= active ? 'bg-koisk-teal text-white' : 'bg-koisk-blue/10 text-koisk-muted',
            ].join(' ')}>
              {i < active ? '✓' : i + 1}
            </div>
            <span className={`text-xs font-body ${i <= active ? 'text-koisk-teal' : 'text-koisk-muted'}`}>
              {label}
            </span>
          </div>
          {i < steps.length - 1 && (
            <div className={`flex-1 h-0.5 mb-4 transition-colors duration-200 ${i < active ? 'bg-koisk-teal' : 'bg-koisk-blue/10'}`} />
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
      <div className="rounded-2xl bg-blue-50 border border-blue-100 p-5">
        <div className="flex items-center gap-3 mb-4">
          <span className="text-3xl">{DEPT_ICONS[dept] ?? '🏠'}</span>
          <div>
            <h2 className="heading-display text-lg leading-tight">
              {DEPT_DISPLAY_NAMES[dept] ?? dept} Bill
            </h2>
            <p className="text-koisk-muted font-body text-sm mt-0.5">
              Consumer: {bill.consumerNo}
            </p>
          </div>
        </div>

        {[
          ['Billing Period', formatBillMonth(bill.billMonth)],
          ['Due Date', formatDate(bill.dueDate)],
        ].map(([label, value]) => (
          <div key={label} className="flex justify-between text-sm py-1">
            <span className="text-koisk-muted font-body">{label}</span>
            <span className="font-body text-koisk-navy font-medium">{value}</span>
          </div>
        ))}

        <hr className="border-blue-200 my-3" />

        <div className="flex justify-between items-center">
          <span className="heading-display text-base">Amount Due</span>
          <span className="heading-display text-2xl text-koisk-teal">{formatINR(bill.amountDue)}</span>
        </div>
      </div>

      <div className="flex gap-3">
        <button type="button" onClick={onClose} className="btn-secondary flex-1 text-base py-3">
          Cancel
        </button>
        <button type="button" onClick={onContinue} className="btn-primary flex-[2] text-base py-3">
          Continue →
        </button>
      </div>
    </div>
  );
}

// ─── Cancel Confirmation (replaces window.confirm) ────────────────────────────

function CancelConfirm({ onConfirm, onResume }) {
  return (
    <div className="flex flex-col items-center gap-5 py-8 px-2 text-center animate-fade-up">
      <div className="w-16 h-16 rounded-3xl bg-amber-50 flex items-center justify-center text-3xl">
        ⚠️
      </div>
      <div>
        <h2 className="heading-display text-xl mb-2">Cancel Payment?</h2>
        <p className="text-koisk-muted font-body text-sm leading-relaxed">
          Your progress will be lost and the payment will not be processed.
        </p>
      </div>
      <div className="flex gap-3 w-full">
        <button type="button" onClick={onResume} className="btn-secondary flex-1">
          Keep Going
        </button>
        <button type="button" onClick={onConfirm} className="btn-danger flex-1">
          Yes, Cancel
        </button>
      </div>
    </div>
  );
}

// ─── Processing Screen ────────────────────────────────────────────────────────

function ProcessingScreen() {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-5">
      <div className="w-14 h-14 border-4 border-koisk-blue/20 border-t-koisk-teal rounded-full animate-spin" />
      <p className="font-display font-semibold text-koisk-navy text-base">
        Processing your payment…
      </p>
      <p className="text-koisk-muted font-body text-sm">
        Please do not close this window
      </p>
    </div>
  );
}

// ─── Failed Screen ────────────────────────────────────────────────────────────

function FailedScreen({ error, onRetry, onClose }) {
  return (
    <div className="flex flex-col items-center gap-4 py-6 animate-fade-up">
      <div className="w-16 h-16 rounded-3xl bg-red-50 flex items-center justify-center font-display font-bold text-2xl text-koisk-danger">
        ✕
      </div>
      <h2 className="heading-display text-xl text-koisk-danger">Payment Failed</h2>
      {error && (
        <p className="text-koisk-muted font-body text-sm text-center leading-relaxed">{error}</p>
      )}
      <div className="flex gap-3 w-full mt-2">
        <button type="button" onClick={onClose} className="btn-secondary flex-1">
          Cancel
        </button>
        <button type="button" onClick={onRetry} className="btn-primary flex-[2]">
          Try Again
        </button>
      </div>
    </div>
  );
}

// ─── Offline Queued Screen ────────────────────────────────────────────────────

function OfflineQueuedScreen({ onClose }) {
  return (
    <div className="flex flex-col items-center gap-4 py-8 text-center animate-fade-up">
      <div className="w-16 h-16 rounded-3xl bg-amber-50 flex items-center justify-center text-3xl">
        📡
      </div>
      <h2 className="heading-display text-xl text-amber-700">Payment Queued</h2>
      <p className="text-koisk-muted font-body text-sm leading-relaxed max-w-xs">
        No internet connection. Your payment has been saved and will be processed automatically when connection is restored.
      </p>
      <button type="button" onClick={onClose} className="btn-primary w-full mt-2">
        Back to Dashboard
      </button>
    </div>
  );
}

// ─── PaymentFlow ──────────────────────────────────────────────────────────────

export default function PaymentFlow({ billId, dept, onClose }) {
  const navigate = useNavigate();
  const authUser = useAuthStore(s => s.user);

  const {
    step,
    activeBill,
    selectedGateway,
    selectedMethod,
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

  const [confirmingCancel, setConfirmingCancel] = React.useState(false);

  useEffect(() => {
    async function loadBill() {
      try {
        const bills = await paymentService.getPendingBills(authUser?.id ?? 'demo-user', dept);
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
      const userId = authUser?.id ?? 'demo-user';

      const { orderId, paymentId, mode, mockDelay } = await paymentService.initiatePayment({
        userId,
        billId:  activeBill.id,
        amount:  activeBill.amountDue,
        dept,
        method:  selectedMethod,
        gateway: selectedGateway,
      });

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
            amount:   activeBill.amountDue,
            currency: 'INR',
            prefill,
          });
          gatewayPaymentId = result.razorpay_payment_id;
        }
      }

      clearCardData();

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
      clearCardData();

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
    if (step === PAYMENT_STEPS.PROCESSING) return;

    if (step === PAYMENT_STEPS.BILL_SUMMARY || step === PAYMENT_STEPS.IDLE) {
      reset();
      onClose?.();
      return;
    }

    // Show inline cancel confirmation — no window.confirm()
    setConfirmingCancel(true);
  }

  function handleConfirmCancel() {
    setConfirmingCancel(false);
    reset();
    onClose?.();
  }

  function handleResumePayment() {
    setConfirmingCancel(false);
  }

  // ─── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="card max-w-lg mx-auto p-6 min-h-[360px] max-h-[90vh] overflow-y-auto w-full">
      <OfflineBanner />

      {confirmingCancel ? (
        <CancelConfirm onConfirm={handleConfirmCancel} onResume={handleResumePayment} />
      ) : (
        <>
          {step !== PAYMENT_STEPS.PROCESSING &&
           step !== PAYMENT_STEPS.SUCCESS &&
           step !== PAYMENT_STEPS.IDLE && (
            <StepDots current={step} />
          )}

          {(step === PAYMENT_STEPS.IDLE || !activeBill) && (
            <div className="flex items-center justify-center py-12 text-koisk-muted font-body">
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
            <PaymentMethodSelector onPay={handlePay} onCancel={handleClose} />
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
            <OfflineQueuedScreen onClose={() => { reset(); onClose?.(); }} />
          )}
        </>
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
