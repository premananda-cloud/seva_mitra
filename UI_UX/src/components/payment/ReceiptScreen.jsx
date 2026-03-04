/**
 * ReceiptScreen.jsx
 * Success screen shown after payment is confirmed.
 * Supports browser print with @media print CSS that hides navigation.
 * Data source: paymentStore.receipt (set by paymentService.completePayment)
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import usePaymentStore from '../../modules/payment/paymentStore.js';
import { formatINR } from '../../modules/payment/paymentUtils.js';
import { DEPT_ICONS, DEPT_DISPLAY_NAMES, GATEWAY_DISPLAY_NAMES, PAYMENT_METHODS } from '../../modules/payment/constants.js';

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
    // Shouldn't happen if routing is correct — redirect to dashboard
    navigate('/');
    return null;
  }

  const deptIcon  = DEPT_ICONS[receipt.dept]          ?? '🏠';
  const deptName  = DEPT_DISPLAY_NAMES[receipt.dept]  ?? receipt.dept;
  const methodLabel = METHOD_LABELS[receipt.method]   ?? receipt.method;

  function handleBackToDashboard() {
    reset();
    navigate('/');
  }

  function handlePrint() {
    window.print();
  }

  return (
    <>
      {/* Print-only CSS injected via a <style> tag */}
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

      <div
        style={{
          minHeight:       '100vh',
          backgroundColor: '#F0FDF4',
          display:         'flex',
          alignItems:      'center',
          justifyContent:  'center',
          padding:         '24px 16px',
        }}
      >
        <div
          id="koisk-receipt"
          style={{
            backgroundColor: 'white',
            borderRadius:    '16px',
            padding:         '36px 32px',
            maxWidth:        '460px',
            width:           '100%',
            boxShadow:       '0 4px 24px rgba(0,0,0,0.10)',
            textAlign:       'center',
          }}
        >
          {/* Header */}
          <div style={{ marginBottom: '24px' }}>
            <div style={{
              width:           '64px', height: '64px',
              backgroundColor: '#DCFCE7', borderRadius: '50%',
              display:         'flex', alignItems: 'center', justifyContent: 'center',
              margin:          '0 auto 12px',
              fontSize:        '32px',
            }}>
              ✅
            </div>
            <h1 style={{ margin: 0, fontSize: '22px', color: '#166534', fontWeight: 700 }}>
              Payment Successful
            </h1>
            <p style={{ margin: '6px 0 0', color: '#6B7280', fontSize: '14px' }}>
              KOISK — Utility Services
            </p>
          </div>

          {/* Reference Number */}
          <div style={{
            backgroundColor: '#F0FDF4',
            border:          '1px dashed #86EFAC',
            borderRadius:    '10px',
            padding:         '14px 20px',
            marginBottom:    '24px',
          }}>
            <p style={{ margin: 0, fontSize: '12px', color: '#6B7280', textTransform: 'uppercase', letterSpacing: '1px' }}>
              Reference Number
            </p>
            <p style={{ margin: '4px 0 0', fontSize: '20px', fontWeight: 700, color: '#166534', fontFamily: 'monospace' }}>
              {receipt.referenceNo}
            </p>
          </div>

          {/* Details table */}
          <div style={{
            border:       '1px solid #F3F4F6',
            borderRadius: '10px',
            overflow:     'hidden',
            marginBottom: '28px',
            textAlign:    'left',
          }}>
            {[
              { label: 'Department', value: `${deptIcon} ${deptName}` },
              { label: 'Amount Paid', value: <strong style={{ color: '#059669', fontSize: '18px' }}>{formatINR(receipt.amount)}</strong> },
              { label: 'Payment Method', value: methodLabel },
              { label: 'Consumer No.', value: receipt.consumerNo ?? '—' },
              { label: 'Date & Time', value: formatDateTime(receipt.paidAt) },
            ].map((row, i) => (
              <div
                key={row.label}
                style={{
                  display:         'flex',
                  justifyContent:  'space-between',
                  alignItems:      'center',
                  padding:         '12px 16px',
                  backgroundColor: i % 2 === 0 ? 'white' : '#F9FAFB',
                  borderBottom:    i < 4 ? '1px solid #F3F4F6' : 'none',
                  fontSize:        '14px',
                }}
              >
                <span style={{ color: '#9CA3AF' }}>{row.label}</span>
                <span style={{ color: '#111827', fontWeight: 500 }}>{row.value}</span>
              </div>
            ))}
          </div>

          {/* Actions */}
          <div className="receipt-actions" style={{ display: 'flex', gap: '12px', flexDirection: 'column' }}>
            <button
              onClick={handlePrint}
              style={{
                width:           '100%',
                padding:         '14px',
                border:          '2px solid #1A56DB',
                borderRadius:    '10px',
                backgroundColor: 'white',
                color:           '#1A56DB',
                fontSize:        '15px',
                fontWeight:      600,
                cursor:          'pointer',
                display:         'flex',
                alignItems:      'center',
                justifyContent:  'center',
                gap:             '8px',
              }}
            >
              🖨️ Print Receipt
            </button>

            <button
              onClick={handleBackToDashboard}
              style={{
                width:           '100%',
                padding:         '14px',
                border:          'none',
                borderRadius:    '10px',
                backgroundColor: '#1A56DB',
                color:           'white',
                fontSize:        '15px',
                fontWeight:      600,
                cursor:          'pointer',
              }}
            >
              ← Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
