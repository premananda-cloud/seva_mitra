/**
 * PaymentMethodSelector.jsx
 * Step 2 of the payment wizard.
 * Gateway toggle + method tabs + UPIInput or CardInput sub-component.
 *
 * FIX (Critical): All inline styles replaced with KOISK Tailwind design-system classes.
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
  { value: PAYMENT_METHODS.UPI,         label: 'UPI',         icon: '📱' },
  { value: PAYMENT_METHODS.CARD,        label: 'Credit Card', icon: '💳' },
  { value: PAYMENT_METHODS.CARD,        label: 'Debit Card',  icon: '🏦', subtype: 'debit' },
  { value: PAYMENT_METHODS.NET_BANKING, label: 'Net Banking', icon: '🌐' },
];

export default function PaymentMethodSelector({ onPay, onCancel }) {
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

  const amount = activeBill?.amountDue ?? 0;
  const payDisabled = !selectedMethod || !inputValid || loading;

  return (
    <div className="flex flex-col gap-5">

      {/* Gateway Toggle */}
      <div>
        <p className="input-label mb-2">Pay via</p>
        <div className="flex gap-3">
          {GATEWAY_OPTIONS.map((gw) => {
            const active = selectedGateway === gw.value;
            return (
              <button
                key={gw.value}
                type="button"
                onClick={() => setGateway(gw.value)}
                aria-pressed={active}
                className={[
                  'flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-2xl border-2',
                  'font-display font-semibold text-sm transition-all duration-150 active:scale-[0.98]',
                  active
                    ? 'border-koisk-teal bg-koisk-teal/5 text-koisk-teal'
                    : 'border-koisk-blue/15 bg-white text-koisk-navy hover:border-koisk-teal/40',
                ].join(' ')}
              >
                <span className={[
                  'w-4 h-4 rounded-full border-2 flex-shrink-0 transition-colors',
                  active ? 'border-koisk-teal bg-koisk-teal' : 'border-koisk-muted',
                ].join(' ')} />
                {gw.label}
                {gw.recommended && (
                  <span className="badge badge-success text-xs px-2 py-0.5">✓ Best</span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Method Tabs */}
      <div>
        <p className="input-label mb-2">Payment Method</p>
        <div className="grid grid-cols-2 gap-2">
          {METHOD_TABS.map((tab) => {
            const active = selectedTab?.label === tab.label;
            return (
              <button
                key={tab.label}
                type="button"
                onClick={() => handleTabSelect(tab)}
                aria-pressed={active}
                className={[
                  'flex items-center gap-2 px-4 py-3 rounded-2xl border-2',
                  'font-display font-semibold text-sm transition-all duration-150 active:scale-[0.98]',
                  active
                    ? 'border-koisk-teal bg-koisk-teal/5 text-koisk-teal'
                    : 'border-koisk-blue/15 bg-white text-koisk-navy hover:border-koisk-teal/40',
                ].join(' ')}
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

      {/* Action buttons */}
      <div className="flex gap-3 pt-1">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="btn-secondary flex-none px-6"
          >
            ← Back
          </button>
        )}
        <button
          type="button"
          onClick={onPay}
          disabled={payDisabled}
          className="btn-primary flex-1"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <Spinner />
              Processing…
            </span>
          ) : (
            <>Pay {formatINR(amount)} →</>
          )}
        </button>
      </div>
    </div>
  );
}

// ─── Spinner ──────────────────────────────────────────────────────────────────

function Spinner() {
  return (
    <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}

// ─── Net Banking Bank List ────────────────────────────────────────────────────

const POPULAR_BANKS = [
  { code: 'SBI',   label: 'State Bank of India' },
  { code: 'HDFC',  label: 'HDFC Bank' },
  { code: 'ICICI', label: 'ICICI Bank' },
  { code: 'AXIS',  label: 'Axis Bank' },
  { code: 'KOTAK', label: 'Kotak Mahindra' },
  { code: 'PNB',   label: 'Punjab National' },
  { code: 'BOB',   label: 'Bank of Baroda' },
  { code: 'YES',   label: 'Yes Bank' },
];

function NetBankingSelector({ onValidChange }) {
  const [selected, setSelected] = React.useState(null);

  function handleSelect(code) {
    setSelected(code);
    onValidChange?.(true);
  }

  return (
    <div>
      <p className="input-label mb-2">Select Your Bank</p>
      <div className="grid grid-cols-2 gap-2 max-h-60 overflow-y-auto">
        {POPULAR_BANKS.map((bank) => {
          const active = selected === bank.code;
          return (
            <button
              key={bank.code}
              type="button"
              onClick={() => handleSelect(bank.code)}
              aria-pressed={active}
              className={[
                'flex items-center gap-2 px-4 py-3 rounded-2xl border-2 text-left',
                'font-body text-sm transition-all duration-150 active:scale-[0.98]',
                active
                  ? 'border-koisk-teal bg-koisk-teal/5 text-koisk-teal font-semibold'
                  : 'border-koisk-blue/15 bg-white text-koisk-navy hover:border-koisk-teal/40',
              ].join(' ')}
            >
              🏦 {bank.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
