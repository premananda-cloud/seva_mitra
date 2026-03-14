/**
 * ReceiptScreen.jsx
 * Success screen shown after payment is confirmed.
 * Supports browser print with @media print CSS that hides navigation.
 *
 * FIX (Critical): All inline styles replaced with KOISK Tailwind design-system classes.
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import usePaymentStore from '../../modules/payment/paymentStore.js';
import { formatINR } from '../../modules/payment/paymentUtils.js';
import {
  DEPT_ICONS,
  DEPT_DISPLAY_NAMES,
  PAYMENT_METHODS,
} from '../../modules/payment/constants.js';

const METHOD_LABELS = {
  [PAYMENT_METHODS.UPI]:         'UPI',
  [PAYMENT_METHODS.CARD]:        'Card',
  [PAYMENT_METHODS.NET_BANKING]: 'Net Banking',
};

function formatDateTime(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-IN', {
    day:    '2-digit',
    month:  'short',
    year:   'numeric',
    hour:   '2-digit',
    minute: '2-digit',
    hour12: true,
  });
}

export default function ReceiptScreen() {
  const navigate = useNavigate();
  const { receipt, reset } = usePaymentStore();

  if (!receipt) {
    navigate('/');
    return null;
  }

  const deptIcon    = DEPT_ICONS[receipt.dept]         ?? '🏠';
  const deptName    = DEPT_DISPLAY_NAMES[receipt.dept] ?? receipt.dept;
  const methodLabel = METHOD_LABELS[receipt.method]    ?? receipt.method;

  function handleBackToDashboard() {
    reset();
    navigate('/dashboard');
  }

  return (
    <>
      <style>{`
        @media print {
          body * { visibility: hidden; }
          #koisk-receipt, #koisk-receipt * { visibility: visible; }
          #koisk-receipt {
            position: fixed;
            left: 0; top: 0;
            width: 100%;
            padding: 32px;
          }
          .receipt-actions { display: none !important; }
        }
      `}</style>

      <div className="screen bg-emerald-50 items-center justify-center">
        <div
          id="koisk-receipt"
          className="card max-w-md w-full mx-auto my-8 p-8 text-center animate-bounce-in"
        >
          {/* Success header */}
          <div className="mb-6">
            <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4 text-3xl">
              ✅
            </div>
            <h1 className="heading-display text-2xl text-koisk-success">
              Payment Successful
            </h1>
            <p className="text-koisk-muted font-body text-sm mt-1">
              KOISK — Utility Services
            </p>
          </div>

          {/* Reference number */}
          <div className="bg-emerald-50 border border-dashed border-emerald-300 rounded-2xl px-5 py-4 mb-6">
            <p className="text-koisk-muted font-body text-xs uppercase tracking-wider mb-1">
              Reference Number
            </p>
            <p className="font-mono font-bold text-xl text-koisk-success">
              {receipt.referenceNo}
            </p>
          </div>

          {/* Details table */}
          <div className="border border-koisk-blue/10 rounded-2xl overflow-hidden mb-6 text-left">
            {[
              ['Department',      `${deptIcon} ${deptName}`],
              ['Amount Paid',     formatINR(receipt.amount)],
              ['Payment Method',  methodLabel],
              ['Consumer No.',    receipt.consumerNo ?? '—'],
              ['Date & Time',     formatDateTime(receipt.paidAt)],
            ].map(([label, value], i) => (
              <div
                key={label}
                className={`flex justify-between items-center px-4 py-3 text-sm ${
                  i % 2 === 0 ? 'bg-white' : 'bg-koisk-surface'
                } ${i < 4 ? 'border-b border-koisk-blue/10' : ''}`}
              >
                <span className="text-koisk-muted font-body">{label}</span>
                <span className={`font-display font-semibold text-koisk-navy ${
                  label === 'Amount Paid' ? 'text-koisk-success text-lg' : ''
                }`}>
                  {value}
                </span>
              </div>
            ))}
          </div>

          {/* Actions */}
          <div className="receipt-actions flex flex-col gap-3">
            <button
              onClick={() => window.print()}
              className="btn-secondary w-full flex items-center justify-center gap-2"
            >
              🖨️ Print Receipt
            </button>
            <button
              onClick={handleBackToDashboard}
              className="btn-primary w-full"
            >
              ← Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
