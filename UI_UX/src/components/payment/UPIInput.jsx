/**
 * UPIInput.jsx
 * UPI ID entry with live format validation.
 * Touch-friendly input with green tick on valid, red error on invalid.
 */

import React, { useState } from 'react';
import usePaymentStore from '../../modules/payment/paymentStore.js';
import { validateUPIId } from '../../modules/payment/paymentUtils.js';

const UPI_APP_SHORTCUTS = [
  { label: 'GPay',    suffix: '@okicici', icon: '🟢' },
  { label: 'PhonePe', suffix: '@ybl',     icon: '🟣' },
  { label: 'Paytm',   suffix: '@paytm',   icon: '🔵' },
  { label: 'BHIM',    suffix: '@upi',     icon: '🟠' },
];

export default function UPIInput({ onValidChange }) {
  const { upiId, setUpiId } = usePaymentStore();
  const [touched, setTouched] = useState(false);

  const validation = validateUPIId(upiId);
  const showError  = touched && upiId.length > 0 && !validation.valid;
  const showTick   = upiId.length > 0 && validation.valid;

  function handleChange(e) {
    const val = e.target.value.trim();
    setUpiId(val);
    if (!touched && val.length > 0) setTouched(true);
    onValidChange?.(validateUPIId(val).valid);
  }

  function handleBlur() {
    setTouched(true);
    onValidChange?.(validation.valid);
  }

  function applyShortcut(suffix) {
    // If user has typed a username part, append the handle
    const currentBase = upiId.split('@')[0] || '';
    const newId = currentBase ? `${currentBase}${suffix}` : suffix.replace('@', '');
    setUpiId(newId);
    setTouched(true);
    onValidChange?.(validateUPIId(newId).valid);
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      <label
        htmlFor="upi-input"
        style={{ fontWeight: 600, fontSize: '14px', color: '#374151' }}
      >
        UPI ID
      </label>

      <div style={{ position: 'relative' }}>
        <input
          id="upi-input"
          type="text"
          inputMode="email"
          autoComplete="off"
          autoCorrect="off"
          autoCapitalize="none"
          spellCheck={false}
          placeholder="yourname@bankname"
          value={upiId}
          onChange={handleChange}
          onBlur={handleBlur}
          style={{
            width:           '100%',
            boxSizing:       'border-box',
            padding:         '14px 44px 14px 14px',
            fontSize:        '16px',
            border:          `2px solid ${showError ? '#EF4444' : showTick ? '#10B981' : '#D1D5DB'}`,
            borderRadius:    '10px',
            outline:         'none',
            transition:      'border-color 0.15s',
            backgroundColor: '#FAFAFA',
            fontFamily:      'monospace',
          }}
          aria-invalid={showError}
          aria-describedby={showError ? 'upi-error' : undefined}
        />

        {/* Status icon */}
        <span
          style={{
            position:   'absolute',
            right:      '14px',
            top:        '50%',
            transform:  'translateY(-50%)',
            fontSize:   '18px',
            lineHeight: 1,
          }}
          aria-hidden="true"
        >
          {showTick && '✅'}
          {showError && '❌'}
        </span>
      </div>

      {/* Error message */}
      {showError && (
        <p
          id="upi-error"
          role="alert"
          style={{ margin: 0, fontSize: '13px', color: '#EF4444' }}
        >
          {validation.error}
        </p>
      )}

      {/* Hint text */}
      {!showError && !showTick && (
        <p style={{ margin: 0, fontSize: '12px', color: '#9CA3AF' }}>
          Format: username@bankname (e.g. ramesh@okicici)
        </p>
      )}

      {/* UPI App shortcuts */}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '4px' }}>
        {UPI_APP_SHORTCUTS.map((app) => (
          <button
            key={app.label}
            type="button"
            onClick={() => applyShortcut(app.suffix)}
            style={{
              display:         'flex',
              alignItems:      'center',
              gap:             '4px',
              padding:         '4px 10px',
              border:          '1px solid #E5E7EB',
              borderRadius:    '20px',
              fontSize:        '12px',
              cursor:          'pointer',
              backgroundColor: '#F9FAFB',
              color:           '#374151',
              transition:      'background 0.15s',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#EEF2FF')}
            onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#F9FAFB')}
          >
            <span>{app.icon}</span>
            {app.label}
          </button>
        ))}
      </div>
    </div>
  );
}
