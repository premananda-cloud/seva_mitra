/**
 * PaymentMethodSelector.jsx
 * Step 2 of the payment wizard.
 * Gateway toggle + method tabs + UPIInput or CardInput sub-component.
 * "Pay ₹X,XXX →" button is disabled until input is valid.
 */

import React, { useState } from 'react';
import usePaymentStore from '../../modules/payment/paymentStore.js';
import { formatINR } from '../../modules/payment/paymentUtils.js';
import { GATEWAYS, PAYMENT_METHODS } from '../../modules/payment/constants.js';
import UPIInput from './UPIInput.jsx';
import CardInput from './CardInput.jsx';

const GATEWAY_OPTIONS = [
  { value: GATEWAYS.PORTONE,  label: 'PortOne',  recommended: true },
  { value: GATEWAYS.RAZORPAY, label: 'Razorpay', recommended: false },
];

const METHOD_TABS = [
  { value: PAYMENT_METHODS.UPI,         label: 'UPI',          icon: '📱' },
  { value: PAYMENT_METHODS.CARD,        label: 'Credit Card',  icon: '💳' },
  { value: PAYMENT_METHODS.CARD,        label: 'Debit Card',   icon: '🏦', subtype: 'debit' },
  { value: PAYMENT_METHODS.NET_BANKING, label: 'Net Banking',  icon: '🌐' },
];

export default function PaymentMethodSelector({ onPay }) {
  const {
    activeBill,
    selectedGateway,
    selectedMethod,
    setGateway,
    setMethod,
    loading,
  } = usePaymentStore();

  const [inputValid, setInputValid] = useState(false);
  const [selectedTab, setSelectedTab] = useState(null);

  function handleTabSelect(tab) {
    setSelectedTab(tab);
    setMethod(tab.value);
    setInputValid(false);
  }

  function handleGatewaySelect(gateway) {
    setGateway(gateway);
  }

  const amount = activeBill?.amountDue ?? 0;
  const payDisabled = !selectedMethod || !inputValid || loading;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

      {/* Gateway Toggle */}
      <div>
        <p style={{ margin: '0 0 10px', fontWeight: 600, fontSize: '14px', color: '#374151' }}>
          Pay via
        </p>
        <div style={{ display: 'flex', gap: '10px' }}>
          {GATEWAY_OPTIONS.map((gw) => {
            const active = selectedGateway === gw.value;
            return (
              <button
                key={gw.value}
                type="button"
                onClick={() => handleGatewaySelect(gw.value)}
                style={{
                  flex:            1,
                  padding:         '10px 14px',
                  border:          `2px solid ${active ? '#1A56DB' : '#E5E7EB'}`,
                  borderRadius:    '10px',
                  backgroundColor: active ? '#EFF6FF' : 'white',
                  color:           active ? '#1A56DB' : '#374151',
                  cursor:          'pointer',
                  fontWeight:      active ? 600 : 400,
                  fontSize:        '14px',
                  display:         'flex',
                  alignItems:      'center',
                  justifyContent:  'center',
                  gap:             '6px',
                  transition:      'all 0.15s',
                }}
              >
                <span style={{
                  width:           '16px', height: '16px',
                  borderRadius:    '50%',
                  border:          `2px solid ${active ? '#1A56DB' : '#9CA3AF'}`,
                  backgroundColor: active ? '#1A56DB' : 'transparent',
                  display:         'inline-block',
                  flexShrink:      0,
                }} />
                {gw.label}
                {gw.recommended && (
                  <span style={{
                    fontSize:        '10px',
                    backgroundColor: '#DCFCE7',
                    color:           '#166534',
                    padding:         '1px 6px',
                    borderRadius:    '10px',
                    fontWeight:      600,
                  }}>
                    ✓ Recommended
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Method Tabs */}
      <div>
        <p style={{ margin: '0 0 10px', fontWeight: 600, fontSize: '14px', color: '#374151' }}>
          Payment Method
        </p>
        <div style={{
          display:             'grid',
          gridTemplateColumns: '1fr 1fr',
          gap:                 '8px',
        }}>
          {METHOD_TABS.map((tab) => {
            const active = selectedTab?.label === tab.label;
            return (
              <button
                key={tab.label}
                type="button"
                onClick={() => handleTabSelect(tab)}
                style={{
                  padding:         '10px 12px',
                  border:          `2px solid ${active ? '#1A56DB' : '#E5E7EB'}`,
                  borderRadius:    '10px',
                  backgroundColor: active ? '#EFF6FF' : 'white',
                  color:           active ? '#1A56DB' : '#374151',
                  cursor:          'pointer',
                  fontWeight:      active ? 600 : 400,
                  fontSize:        '14px',
                  display:         'flex',
                  alignItems:      'center',
                  gap:             '6px',
                  transition:      'all 0.15s',
                }}
              >
                <span>{tab.icon}</span>
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Input component for selected method */}
      {selectedTab?.value === PAYMENT_METHODS.UPI && (
        <UPIInput onValidChange={setInputValid} />
      )}

      {selectedTab?.value === PAYMENT_METHODS.CARD && (
        <CardInput onValidChange={setInputValid} />
      )}

      {selectedTab?.value === PAYMENT_METHODS.NET_BANKING && (
        <NetBankingSelector onValidChange={setInputValid} />
      )}

      {/* Pay button */}
      <button
        type="button"
        onClick={onPay}
        disabled={payDisabled}
        style={{
          width:           '100%',
          padding:         '16px',
          border:          'none',
          borderRadius:    '12px',
          backgroundColor: payDisabled ? '#E5E7EB' : '#1A56DB',
          color:           payDisabled ? '#9CA3AF' : 'white',
          fontSize:        '16px',
          fontWeight:      700,
          cursor:          payDisabled ? 'not-allowed' : 'pointer',
          transition:      'background-color 0.2s',
          display:         'flex',
          alignItems:      'center',
          justifyContent:  'center',
          gap:             '8px',
        }}
      >
        {loading ? (
          <>
            <span style={{
              width:        '18px', height: '18px',
              border:       '2px solid rgba(255,255,255,0.3)',
              borderTop:    '2px solid white',
              borderRadius: '50%',
              animation:    'spin 0.8s linear infinite',
              display:      'inline-block',
            }} />
            Processing…
          </>
        ) : (
          <>Pay {formatINR(amount)} →</>
        )}
      </button>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}

// ─── Net Banking Bank List ────────────────────────────────────────────────────

const POPULAR_BANKS = [
  { code: 'SBI',    label: 'State Bank of India' },
  { code: 'HDFC',   label: 'HDFC Bank' },
  { code: 'ICICI',  label: 'ICICI Bank' },
  { code: 'AXIS',   label: 'Axis Bank' },
  { code: 'KOTAK',  label: 'Kotak Mahindra Bank' },
  { code: 'PNB',    label: 'Punjab National Bank' },
  { code: 'BOB',    label: 'Bank of Baroda' },
  { code: 'YES',    label: 'Yes Bank' },
];

function NetBankingSelector({ onValidChange }) {
  const [selected, setSelected] = React.useState(null);

  function handleSelect(code) {
    setSelected(code);
    onValidChange?.(true);
  }

  return (
    <div>
      <p style={{ margin: '0 0 10px', fontWeight: 600, fontSize: '14px', color: '#374151' }}>
        Select Your Bank
      </p>
      <div style={{
        display:             'grid',
        gridTemplateColumns: '1fr 1fr',
        gap:                 '8px',
        maxHeight:           '240px',
        overflowY:           'auto',
      }}>
        {POPULAR_BANKS.map((bank) => {
          const active = selected === bank.code;
          return (
            <button
              key={bank.code}
              type="button"
              onClick={() => handleSelect(bank.code)}
              style={{
                padding:         '10px 12px',
                border:          `2px solid ${active ? '#1A56DB' : '#E5E7EB'}`,
                borderRadius:    '8px',
                backgroundColor: active ? '#EFF6FF' : 'white',
                color:           active ? '#1A56DB' : '#374151',
                cursor:          'pointer',
                fontSize:        '13px',
                fontWeight:      active ? 600 : 400,
                textAlign:       'left',
                transition:      'all 0.15s',
              }}
            >
              🏦 {bank.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
