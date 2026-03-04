/**
 * CardInput.jsx
 * Card details — tokenised, raw numbers never stored after SDK call.
 * Features: auto-formatting, card network detection, visual preview.
 *
 * SECURITY: cardData is in-memory only during input step.
 * paymentStore.clearCardData() MUST be called immediately after SDK call.
 */

import React from 'react';
import usePaymentStore from '../../modules/payment/paymentStore.js';
import {
  validateCardNumber,
  validateExpiry,
  validateCVV,
  maskCardNumber,
  formatCardNumber,
  formatExpiry,
} from '../../modules/payment/paymentUtils.js';
import { CARD_NETWORKS } from '../../modules/payment/constants.js';

const NETWORK_LABELS = {
  [CARD_NETWORKS.VISA]:       { label: 'Visa',       color: '#1A1F71', icon: '💙' },
  [CARD_NETWORKS.MASTERCARD]: { label: 'Mastercard', color: '#EB001B', icon: '🔴' },
  [CARD_NETWORKS.RUPAY]:      { label: 'RuPay',      color: '#007CC2', icon: '🟦' },
  [CARD_NETWORKS.AMEX]:       { label: 'Amex',       color: '#007BC1', icon: '🔷' },
};

function inputStyle(valid, touched) {
  return {
    width:           '100%',
    boxSizing:       'border-box',
    padding:         '12px 14px',
    fontSize:        '15px',
    border:          `2px solid ${touched && !valid ? '#EF4444' : touched && valid ? '#10B981' : '#D1D5DB'}`,
    borderRadius:    '10px',
    outline:         'none',
    transition:      'border-color 0.15s',
    backgroundColor: '#FAFAFA',
  };
}

function FieldLabel({ children, htmlFor }) {
  return (
    <label
      htmlFor={htmlFor}
      style={{ fontWeight: 600, fontSize: '13px', color: '#374151', display: 'block', marginBottom: '4px' }}
    >
      {children}
    </label>
  );
}

export default function CardInput({ onValidChange }) {
  const { cardData, setCardData } = usePaymentStore();
  const [touched, setTouch] = React.useState({ number: false, expiry: false, cvv: false, name: false });

  const rawDigits = cardData.number.replace(/\s/g, '');
  const { valid: numValid, network } = validateCardNumber(rawDigits);

  const [expiryMM, expiryYY] = (cardData.expiry || '').split('/');
  const { valid: expiryValid, error: expiryError } = expiryMM && expiryYY
    ? validateExpiry(expiryMM, expiryYY)
    : { valid: false, error: null };

  const { valid: cvvValid } = validateCVV(cardData.cvv, network);
  const nameValid = cardData.name.trim().length >= 2;

  const allValid = numValid && expiryValid && cvvValid && nameValid;

  React.useEffect(() => {
    onValidChange?.(allValid);
  }, [allValid]);

  function touch(field) {
    setTouch((t) => ({ ...t, [field]: true }));
  }

  function handleNumberChange(e) {
    const formatted = formatCardNumber(e.target.value);
    setCardData({ number: formatted });
  }

  function handleExpiryChange(e) {
    const formatted = formatExpiry(e.target.value);
    setCardData({ expiry: formatted });
  }

  function handleCvvChange(e) {
    const digits = e.target.value.replace(/\D/g, '').slice(0, network === CARD_NETWORKS.AMEX ? 4 : 3);
    setCardData({ cvv: digits });
  }

  function handleNameChange(e) {
    setCardData({ name: e.target.value });
  }

  const networkInfo = network ? NETWORK_LABELS[network] : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

      {/* Visual Card Preview */}
      <div
        style={{
          background:    'linear-gradient(135deg, #1A56DB, #0E3A8C)',
          borderRadius:  '14px',
          padding:       '20px 22px',
          color:         'white',
          minHeight:     '100px',
          display:       'flex',
          flexDirection: 'column',
          justifyContent:'space-between',
          fontFamily:    'monospace',
          boxShadow:     '0 4px 16px rgba(26,86,219,0.25)',
          position:      'relative',
          overflow:      'hidden',
        }}
      >
        {/* Background pattern */}
        <div style={{
          position:   'absolute', top: '-30px', right: '-30px',
          width:      '120px',   height: '120px',
          borderRadius:'50%',   background: 'rgba(255,255,255,0.08)',
        }} />
        <div style={{
          position:   'absolute', bottom: '-20px', left: '40px',
          width:      '80px',    height: '80px',
          borderRadius:'50%',   background: 'rgba(255,255,255,0.05)',
        }} />

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '12px', opacity: 0.7 }}>KOISK Card</span>
          {networkInfo && (
            <span style={{ fontSize: '13px', fontWeight: 700, fontFamily: 'sans-serif' }}>
              {networkInfo.icon} {networkInfo.label}
            </span>
          )}
        </div>

        <div style={{ fontSize: '18px', letterSpacing: '3px', marginTop: '12px' }}>
          {cardData.number ? maskCardNumber(rawDigits) : '•••• •••• •••• ••••'}
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '10px', fontSize: '13px' }}>
          <span style={{ opacity: 0.8 }}>
            {cardData.name.toUpperCase() || 'CARDHOLDER NAME'}
          </span>
          <span style={{ opacity: 0.8 }}>
            {cardData.expiry || 'MM/YY'}
          </span>
        </div>
      </div>

      {/* Card Number */}
      <div>
        <FieldLabel htmlFor="card-number">Card Number</FieldLabel>
        <div style={{ position: 'relative' }}>
          <input
            id="card-number"
            type="text"
            inputMode="numeric"
            autoComplete="cc-number"
            placeholder="1234 5678 9012 3456"
            maxLength={19}
            value={cardData.number}
            onChange={handleNumberChange}
            onBlur={() => touch('number')}
            style={{ ...inputStyle(numValid, touched.number), fontFamily: 'monospace', fontSize: '17px' }}
          />
        </div>
        {touched.number && !numValid && cardData.number.length > 0 && (
          <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#EF4444' }}>
            Invalid card number
          </p>
        )}
      </div>

      {/* Expiry + CVV row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <div>
          <FieldLabel htmlFor="card-expiry">Expiry</FieldLabel>
          <input
            id="card-expiry"
            type="text"
            inputMode="numeric"
            autoComplete="cc-exp"
            placeholder="MM/YY"
            maxLength={5}
            value={cardData.expiry}
            onChange={handleExpiryChange}
            onBlur={() => touch('expiry')}
            style={inputStyle(expiryValid, touched.expiry)}
          />
          {touched.expiry && !expiryValid && expiryError && (
            <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#EF4444' }}>{expiryError}</p>
          )}
        </div>

        <div>
          <FieldLabel htmlFor="card-cvv">CVV</FieldLabel>
          <input
            id="card-cvv"
            type="password"
            inputMode="numeric"
            autoComplete="cc-csc"
            placeholder={network === CARD_NETWORKS.AMEX ? '4 digits' : '3 digits'}
            maxLength={network === CARD_NETWORKS.AMEX ? 4 : 3}
            value={cardData.cvv}
            onChange={handleCvvChange}
            onBlur={() => touch('cvv')}
            style={inputStyle(cvvValid, touched.cvv)}
          />
          <p style={{ margin: '3px 0 0', fontSize: '11px', color: '#9CA3AF' }}>
            Never stored
          </p>
        </div>
      </div>

      {/* Name on card */}
      <div>
        <FieldLabel htmlFor="card-name">Name on Card</FieldLabel>
        <input
          id="card-name"
          type="text"
          autoComplete="cc-name"
          placeholder="As it appears on your card"
          value={cardData.name}
          onChange={handleNameChange}
          onBlur={() => touch('name')}
          style={inputStyle(nameValid, touched.name)}
        />
      </div>
    </div>
  );
}
