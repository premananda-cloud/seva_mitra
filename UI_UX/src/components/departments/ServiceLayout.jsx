/**
 * ServiceLayout.jsx
 * Shared chrome for all department service screens.
 * Renders the top nav, back button, and a slot for service action tiles + modals.
 */
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { clsx } from 'clsx';
import PaymentFlow from '@/components/payment/PaymentFlow';

export default function ServiceLayout({ dept, icon, gradient, title, tiles, formModals }) {
  const navigate = useNavigate();
  const [activeAction, setActiveAction] = useState(null); // key of which form/modal is open
  const [payBillOpen, setPayBillOpen]   = useState(false);

  function handleTileClick(tile) {
    if (tile.action === 'pay_bill') {
      setPayBillOpen(true);
    } else {
      setActiveAction(tile.action);
    }
  }

  const ActiveForm = activeAction ? formModals[activeAction] : null;

  return (
    <div className="screen bg-koisk-surface">

      {/* ── Nav ──────────────────────────────────────────────────── */}
      <div className="bg-koisk-navy px-6 py-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <button
            onClick={() => navigate('/dashboard')}
            className="text-white/70 hover:text-white font-body text-sm flex items-center gap-2 transition-colors min-h-[44px] px-2 rounded-xl focus-visible:outline focus-visible:outline-2 focus-visible:outline-koisk-accent"
            aria-label="Back to dashboard"
          >
            <span aria-hidden="true">←</span> Back
          </button>
          <span className="font-display font-bold text-white text-lg">KOISK</span>
          <div className="w-16" /> {/* spacer */}
        </div>
      </div>

      {/* ── Department Hero ───────────────────────────────────────── */}
      <div className={clsx('px-6 py-8', gradient)}>
        <div className="max-w-3xl mx-auto">
          <div className="flex items-center gap-4 animate-fade-up">
            <div className="w-16 h-16 rounded-3xl bg-white/20 flex items-center justify-center text-4xl shadow-lg">
              {icon}
            </div>
            <div>
              <h1 className="font-display font-bold text-white text-2xl">{title}</h1>
              <p className="text-white/70 font-body text-sm mt-0.5">Select a service below</p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Service Tiles ─────────────────────────────────────────── */}
      <div className="max-w-3xl mx-auto w-full px-4 py-6">
        <div className="grid grid-cols-2 gap-3">
          {tiles.map((tile, i) => (
            <button
              key={tile.action}
              onClick={() => handleTileClick(tile)}
              className="card-hover p-5 text-left animate-fade-up"
              style={{ animationDelay: `${i * 70}ms`, animationFillMode: 'forwards' }}
            >
              <div className="w-11 h-11 rounded-2xl bg-koisk-surface flex items-center justify-center text-2xl mb-3 shadow-sm">
                {tile.icon}
              </div>
              <p className="font-display font-semibold text-koisk-navy text-sm">{tile.label}</p>
              <p className="text-koisk-muted text-xs font-body mt-0.5">{tile.sub}</p>
            </button>
          ))}
        </div>
      </div>

      {/* ── Pay Bill Modal (PaymentFlow) ──────────────────────────── */}
      {payBillOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-koisk-navy/60 backdrop-blur-sm p-4">
          <PaymentFlow
            dept={dept}
            billId={null}
            onClose={() => setPayBillOpen(false)}
          />
        </div>
      )}

      {/* ── Service Form Modals ───────────────────────────────────── */}
      {ActiveForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-koisk-navy/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-3xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            <ActiveForm onClose={() => setActiveAction(null)} dept={dept} />
          </div>
        </div>
      )}
    </div>
  );
}
