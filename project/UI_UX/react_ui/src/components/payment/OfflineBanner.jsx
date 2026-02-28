/**
 * OfflineBanner.jsx
 * Shown at the top of PaymentFlow when there is no network connection.
 * Auto-hides when the network is restored.
 */

import React, { useEffect, useState } from 'react';
import usePaymentStore from '../../modules/payment/paymentStore.js';
import { isNetworkAvailable } from '../../modules/payment/paymentUtils.js';

export default function OfflineBanner() {
  const { isOffline, queuedCount, setOffline } = usePaymentStore();
  const [visible, setVisible] = useState(!isNetworkAvailable());

  useEffect(() => {
    function handleOnline() {
      setVisible(false);
      setOffline(false);
    }
    function handleOffline() {
      setVisible(true);
      setOffline(true);
    }

    window.addEventListener('online',  handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online',  handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [setOffline]);

  if (!visible && !isOffline) return null;

  return (
    <div
      role="alert"
      style={{
        display:         'flex',
        alignItems:      'center',
        justifyContent:  'space-between',
        backgroundColor: '#FEF3C7',
        border:          '1px solid #F59E0B',
        borderRadius:    '8px',
        padding:         '12px 16px',
        marginBottom:    '16px',
        fontSize:        '14px',
        color:           '#92400E',
        gap:             '12px',
        flexWrap:        'wrap',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '18px' }}>📡</span>
        <div>
          <strong>No internet connection</strong>
          <div style={{ marginTop: '2px', fontWeight: 'normal' }}>
            Your payment will be queued and processed when the connection is restored.
          </div>
        </div>
      </div>

      {queuedCount > 0 && (
        <span
          style={{
            backgroundColor: '#F59E0B',
            color:           'white',
            borderRadius:    '12px',
            padding:         '2px 10px',
            fontWeight:      600,
            fontSize:        '13px',
            whiteSpace:      'nowrap',
          }}
        >
          {queuedCount} queued {queuedCount === 1 ? 'payment' : 'payments'}
        </span>
      )}
    </div>
  );
}
