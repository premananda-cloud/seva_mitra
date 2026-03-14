/**
 * ServiceRequestForm.jsx
 * Generic form modal for submitting service requests to the backend.
 * POST /api/v1/{dept}/{endpoint}
 */
import { useState } from 'react';
import { clsx } from 'clsx';
import { useAuthStore } from '@/modules/auth/authStore';

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8877';

export default function ServiceRequestForm({ title, icon, dept, endpoint, fields, onClose }) {
  const user = useAuthStore(s => s.user);
  const [values,    setValues]    = useState(() => Object.fromEntries(fields.map(f => [f.name, ''])));
  const [loading,   setLoading]   = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [refNo,     setRefNo]     = useState('');
  const [error,     setError]     = useState('');

  function setValue(name, val) {
    setValues(v => ({ ...v, [name]: val }));
  }

  async function handleSubmit() {
    setLoading(true);
    setError('');
    try {
      const payload = {
        user_id: user?.id ?? 'demo-user',
        ...values,
      };
      const res = await fetch(`${API}/api/v1/${dept}/${endpoint}`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const data = await res.json();
      setRefNo(data.request_id ?? data.reference ?? 'REQ-' + Date.now());
      setSubmitted(true);
    } catch (err) {
      setError(err.message || 'Failed to submit. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  const isValid = fields.every(f => !f.required || values[f.name]?.trim());

  /* ── Success state ────────────────────────────────────────────── */
  if (submitted) {
    return (
      <div className="p-8 text-center animate-bounce-in">
        <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4 text-3xl">
          ✅
        </div>
        <h2 className="font-display font-bold text-koisk-navy text-xl mb-2">Request Submitted!</h2>
        <p className="text-koisk-muted font-body text-sm mb-4">
          Your request has been received and is being processed.
        </p>
        <div className="bg-koisk-surface rounded-2xl p-4 mb-6">
          <p className="text-xs text-koisk-muted font-body uppercase tracking-wider mb-1">Reference Number</p>
          <p className="font-mono font-bold text-koisk-navy text-base">{refNo}</p>
        </div>
        <button onClick={onClose} className="btn-primary w-full">
          Back to Services
        </button>
      </div>
    );
  }

  /* ── Form state ───────────────────────────────────────────────── */
  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-12 h-12 rounded-2xl bg-koisk-surface flex items-center justify-center text-2xl">
          {icon}
        </div>
        <div>
          <h2 className="font-display font-bold text-koisk-navy text-lg">{title}</h2>
          <p className="text-koisk-muted font-body text-xs">Fill in the details below</p>
        </div>
        <button
          onClick={onClose}
          className="ml-auto min-h-[44px] min-w-[44px] flex items-center justify-center text-koisk-muted hover:text-koisk-navy text-xl leading-none rounded-xl hover:bg-koisk-surface transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-koisk-teal"
          aria-label="Close form"
        >
          ✕
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-2xl text-red-700 font-body text-sm">
          {error}
        </div>
      )}

      {/* Fields */}
      <div className="space-y-4">
        {fields.map(f => (
          <div key={f.name}>
            <label className="input-label">
              {f.label}{f.required && <span className="text-red-500 ml-1">*</span>}
            </label>

            {f.type === 'select' ? (
              <select
                value={values[f.name]}
                onChange={e => setValue(f.name, e.target.value)}
                className="input-field"
              >
                <option value="">— Select —</option>
                {f.options.map(o => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            ) : f.type === 'textarea' ? (
              <textarea
                value={values[f.name]}
                onChange={e => setValue(f.name, e.target.value)}
                placeholder={f.placeholder}
                rows={3}
                className="input-field resize-none"
              />
            ) : (
              <input
                type={f.type ?? 'text'}
                value={values[f.name]}
                onChange={e => setValue(f.name, e.target.value)}
                placeholder={f.placeholder}
                className="input-field"
              />
            )}
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="flex gap-3 mt-6">
        <button onClick={onClose} className="btn-secondary flex-1">
          Cancel
        </button>
        <button
          onClick={handleSubmit}
          disabled={loading || !isValid}
          className="btn-primary flex-2 flex-1"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
              Submitting…
            </span>
          ) : 'Submit Request'}
        </button>
      </div>
    </div>
  );
}
