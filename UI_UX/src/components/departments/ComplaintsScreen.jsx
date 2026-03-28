/**
 * ComplaintsScreen.jsx
 * Cross-department complaint & grievance hub.
 * Covers: Electricity · Water · Gas · Municipal · General Civic
 *
 * Two modes:
 *   - "submit"  — fill & submit a new complaint
 *   - "track"   — look up a complaint by reference ID
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { clsx } from 'clsx';
import { useAuthStore } from '@/modules/auth/authStore';

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8877';

// ─── Department + Category Config ────────────────────────────────────────────

const DEPARTMENTS = [
  { value: 'electricity', label: 'Electricity',  icon: '⚡', color: 'from-amber-400 to-yellow-500' },
  { value: 'water',       label: 'Water Supply', icon: '💧', color: 'from-blue-400 to-cyan-500'   },
  { value: 'gas',         label: 'Gas',          icon: '🔥', color: 'from-orange-400 to-red-500'  },
  { value: 'municipal',   label: 'Municipal',    icon: '🏛️', color: 'from-emerald-400 to-green-500' },
  { value: 'general',     label: 'General Civic',icon: '🏙️', color: 'from-purple-400 to-violet-500' },
];

const CATEGORIES = {
  electricity: [
    { value: 'No Power Supply',         label: '🔴 No Power Supply'            },
    { value: 'Voltage Fluctuation',     label: '🟡 Voltage Fluctuation'        },
    { value: 'Billing Issue',           label: '🟡 Billing / Overcharge'       },
    { value: 'Meter Fault',             label: '🟢 Faulty Meter'               },
    { value: 'Street Light Issue',      label: '🟢 Street Light Not Working'   },
    { value: 'Wire Sparking',           label: '🔴 Exposed / Sparking Wire'    },
    { value: 'Other',                   label: '— Other'                       },
  ],
  water: [
    { value: 'No Water Supply',         label: '🔴 No Water Supply'            },
    { value: 'Water Leakage',           label: '🔴 Water Leakage / Burst Pipe' },
    { value: 'Dirty / Contaminated',    label: '🔴 Dirty or Contaminated Water' },
    { value: 'Low Pressure',            label: '🟡 Low Water Pressure'         },
    { value: 'Billing Issue',           label: '🟡 Billing / Overcharge'       },
    { value: 'Meter Fault',             label: '🟢 Faulty Meter'               },
    { value: 'Other',                   label: '— Other'                       },
  ],
  gas: [
    { value: 'Gas Leak',                label: '🔴 Gas Leak — Immediate Danger' },
    { value: 'Unusual Smell',           label: '🔴 Unusual Smell / Possible Leak' },
    { value: 'No Gas Supply',           label: '🟡 No Gas Supply'              },
    { value: 'Low Pressure',            label: '🟡 Low Gas Pressure'           },
    { value: 'Billing Issue',           label: '🟡 Billing / Overcharge'       },
    { value: 'Meter Fault',             label: '🟢 Faulty Meter'               },
    { value: 'Other',                   label: '— Other'                       },
  ],
  municipal: [
    { value: 'Garbage Not Collected',   label: '🟡 Garbage Not Collected'      },
    { value: 'Road Damaged',            label: '🟡 Damaged Road / Pothole'     },
    { value: 'Drainage Blocked',        label: '🔴 Blocked Drain / Flooding'   },
    { value: 'Stray Animal Menace',     label: '🟡 Stray Animal Issue'         },
    { value: 'Illegal Construction',    label: '🟡 Illegal Construction'       },
    { value: 'Property Tax Issue',      label: '🟢 Property Tax / Certificate' },
    { value: 'Other',                   label: '— Other'                       },
  ],
  general: [
    { value: 'Public Nuisance',         label: '🟡 Public Nuisance'            },
    { value: 'Encroachment',            label: '🟡 Encroachment'               },
    { value: 'Noise Pollution',         label: '🟡 Noise Pollution'            },
    { value: 'Corruption / Misconduct', label: '🔴 Corruption / Misconduct'    },
    { value: 'Service Delay',           label: '🟡 Delayed Government Service' },
    { value: 'Other',                   label: '— Other'                       },
  ],
};

const SEVERITIES = [
  { value: 'Critical', label: '🔴 Critical',  sub: 'Life / safety risk — 2 hr response'    },
  { value: 'High',     label: '🟠 High',      sub: 'Major disruption — 24 hr response'     },
  { value: 'Medium',   label: '🟡 Medium',    sub: 'Moderate issue — 3 day response'       },
  { value: 'Low',      label: '🟢 Low',       sub: 'Minor issue — 7 day response'          },
];

const STATUS_BADGE = {
  SUBMITTED:   { cls: 'badge-info',    label: 'Submitted'   },
  IN_PROGRESS: { cls: 'badge-warning', label: 'In Progress' },
  APPROVED:    { cls: 'badge-info',    label: 'Approved'    },
  DELIVERED:   { cls: 'badge-success', label: 'Resolved'    },
  DENIED:      { cls: 'badge-muted',   label: 'Closed'      },
  CANCELLED:   { cls: 'badge-muted',   label: 'Cancelled'   },
};

// ─── Sub-components ───────────────────────────────────────────────────────────

/** Step 1 – pick a department tile */
function DeptPicker({ selected, onSelect }) {
  return (
    <div>
      <p className="input-label mb-3">Which department?</p>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {DEPARTMENTS.map((d, i) => (
          <button
            key={d.value}
            onClick={() => onSelect(d.value)}
            className={clsx(
              'rounded-2xl p-4 text-left border-2 transition-all duration-200 active:scale-95',
              selected === d.value
                ? 'border-koisk-teal bg-koisk-teal/5 shadow-md'
                : 'border-koisk-blue/15 bg-white hover:border-koisk-teal/50',
            )}
            style={{ animationDelay: `${i * 60}ms` }}
          >
            <div className={clsx(
              'w-10 h-10 rounded-xl bg-gradient-to-br flex items-center justify-center text-xl mb-2 shadow-sm',
              d.color,
            )}>
              {d.icon}
            </div>
            <p className="font-display font-semibold text-koisk-navy text-sm leading-tight">{d.label}</p>
          </button>
        ))}
      </div>
    </div>
  );
}

/** Spinner used while loading */
function Spinner() {
  return (
    <span className="inline-flex items-center gap-2">
      <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
      </svg>
      Please wait…
    </span>
  );
}

// ─── Main SubmitView ──────────────────────────────────────────────────────────

function SubmitView() {
  const user = useAuthStore(s => s.user);

  const [step,        setStep]        = useState(1);   // 1=dept 2=details 3=confirm
  const [dept,        setDept]        = useState('');
  const [category,    setCategory]    = useState('');
  const [severity,    setSeverity]    = useState('Medium');
  const [form,        setForm]        = useState({
    citizen_name: user?.name ?? '',
    phone:        user?.phone ?? '',
    subject:      '',
    description:  '',
    location:     '',
    ward_number:  '',
    consumer_no:  '',
  });
  const [loading,   setLoading]   = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [refData,   setRefData]   = useState(null);
  const [error,     setError]     = useState('');

  function setField(k, v) { setForm(f => ({ ...f, [k]: v })); }

  const deptObj     = DEPARTMENTS.find(d => d.value === dept);
  const categoryOpts = dept ? CATEGORIES[dept] : [];

  function canProceed() {
    if (step === 1) return !!dept;
    if (step === 2) return (
      !!category &&
      form.citizen_name.trim() &&
      form.phone.trim() &&
      form.subject.trim() &&
      form.description.trim()
    );
    return true;
  }

  async function handleSubmit() {
    setLoading(true);
    setError('');
    try {
      const payload = {
        citizen_name: form.citizen_name,
        phone:        form.phone,
        department:   dept,
        category,
        subject:      form.subject,
        description:  form.description,
        location:     form.location   || undefined,
        ward_number:  form.ward_number|| undefined,
        consumer_no:  form.consumer_no|| undefined,
        severity,
      };
      const res = await fetch(`${API}/api/v1/complaints/submit`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const data = await res.json();
      setRefData(data);
      setSubmitted(true);
    } catch (err) {
      setError(err.message || 'Submission failed. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  // ── Success ──
  if (submitted && refData) {
    const slaMsg = refData.data?.sla_message || 'Your complaint has been received.';
    return (
      <div className="p-6 text-center animate-bounce-in">
        <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4 text-3xl">✅</div>
        <h2 className="font-display font-bold text-koisk-navy text-xl mb-2">Complaint Registered!</h2>
        <p className="text-koisk-muted font-body text-sm mb-5">{slaMsg}</p>

        <div className="bg-koisk-surface rounded-2xl p-4 mb-4 text-left space-y-2">
          <p className="text-xs text-koisk-muted font-body uppercase tracking-wider mb-1">Reference Number</p>
          <p className="font-mono font-bold text-koisk-navy text-base break-all">
            {refData.data?.reference_id || refData.service_request_id}
          </p>
        </div>

        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 mb-6 text-left">
          <p className="text-amber-800 font-body text-xs">
            📌 Save your reference number to track your complaint status at any kiosk.
          </p>
        </div>

        <div className="bg-koisk-surface rounded-2xl p-4 mb-6 text-left space-y-1">
          <p className="text-xs text-koisk-muted font-body uppercase tracking-wider">Summary</p>
          <p className="font-display font-semibold text-koisk-navy text-sm">{deptObj?.icon} {deptObj?.label} — {category}</p>
          <p className="text-koisk-muted text-xs">{form.subject}</p>
          <span className={clsx('badge mt-1', severity === 'Critical' ? 'badge-warning' : severity === 'High' ? 'badge-warning' : 'badge-info')}>
            {severity}
          </span>
        </div>
      </div>
    );
  }

  // ── Step 1: Department ──
  if (step === 1) {
    return (
      <div className="p-6 space-y-6 animate-fade-up">
        <DeptPicker selected={dept} onSelect={d => { setDept(d); setCategory(''); }} />
        {error && <p className="text-red-600 font-body text-sm">{error}</p>}
        <button
          onClick={() => setStep(2)}
          disabled={!canProceed()}
          className="btn-primary w-full"
        >
          Next →
        </button>
      </div>
    );
  }

  // ── Step 2: Details ──
  if (step === 2) {
    return (
      <div className="p-6 space-y-4 animate-fade-up">

        {/* Dept chip */}
        <div className="flex items-center gap-2 p-3 bg-koisk-surface rounded-2xl">
          <span className="text-xl">{deptObj?.icon}</span>
          <span className="font-display font-semibold text-koisk-navy text-sm">{deptObj?.label}</span>
          <button onClick={() => setStep(1)} className="ml-auto text-koisk-muted hover:text-koisk-navy text-xs font-body underline">Change</button>
        </div>

        {/* Category */}
        <div>
          <label className="input-label">Issue Category <span className="text-red-500">*</span></label>
          <select value={category} onChange={e => setCategory(e.target.value)} className="input-field">
            <option value="">— Select issue type —</option>
            {categoryOpts.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
        </div>

        {/* Severity */}
        <div>
          <label className="input-label">Severity</label>
          <div className="grid grid-cols-2 gap-2">
            {SEVERITIES.map(s => (
              <button
                key={s.value}
                onClick={() => setSeverity(s.value)}
                className={clsx(
                  'rounded-2xl p-3 text-left border-2 transition-all duration-150',
                  severity === s.value
                    ? 'border-koisk-teal bg-koisk-teal/5'
                    : 'border-koisk-blue/15 bg-white hover:border-koisk-teal/40',
                )}
              >
                <p className="font-display font-semibold text-koisk-navy text-sm">{s.label}</p>
                <p className="text-koisk-muted text-xs font-body mt-0.5">{s.sub}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Contact */}
        <div>
          <label className="input-label">Your Name <span className="text-red-500">*</span></label>
          <input type="text" value={form.citizen_name} onChange={e => setField('citizen_name', e.target.value)}
            placeholder="Full name" className="input-field" />
        </div>
        <div>
          <label className="input-label">Mobile Number <span className="text-red-500">*</span></label>
          <input type="tel" value={form.phone} onChange={e => setField('phone', e.target.value)}
            placeholder="10-digit number" className="input-field" />
        </div>

        {/* Subject + Description */}
        <div>
          <label className="input-label">Subject <span className="text-red-500">*</span></label>
          <input type="text" value={form.subject} onChange={e => setField('subject', e.target.value)}
            placeholder="Brief title of your complaint" className="input-field" />
        </div>
        <div>
          <label className="input-label">Description <span className="text-red-500">*</span></label>
          <textarea value={form.description} onChange={e => setField('description', e.target.value)}
            placeholder="Describe the issue in detail" rows={3} className="input-field resize-none" />
        </div>

        {/* Optional */}
        <div>
          <label className="input-label">Location / Landmark</label>
          <input type="text" value={form.location} onChange={e => setField('location', e.target.value)}
            placeholder="Where is the issue? (optional)" className="input-field" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="input-label">Ward No.</label>
            <input type="text" value={form.ward_number} onChange={e => setField('ward_number', e.target.value)}
              placeholder="e.g. 12" className="input-field" />
          </div>
          <div>
            <label className="input-label">Consumer No.</label>
            <input type="text" value={form.consumer_no} onChange={e => setField('consumer_no', e.target.value)}
              placeholder="If applicable" className="input-field" />
          </div>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-2xl text-red-700 font-body text-sm">{error}</div>
        )}

        <div className="flex gap-3 pt-2">
          <button onClick={() => setStep(1)} className="btn-secondary flex-1">← Back</button>
          <button
            onClick={handleSubmit}
            disabled={loading || !canProceed()}
            className="btn-primary flex-1"
          >
            {loading ? <Spinner /> : 'Submit Complaint'}
          </button>
        </div>
      </div>
    );
  }

  return null;
}

// ─── Track View ───────────────────────────────────────────────────────────────

function TrackView() {
  const [refId,   setRefId]   = useState('');
  const [loading, setLoading] = useState(false);
  const [result,  setResult]  = useState(null);
  const [error,   setError]   = useState('');

  async function handleTrack() {
    if (!refId.trim()) return;
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await fetch(`${API}/api/v1/complaints/${encodeURIComponent(refId.trim())}`);
      if (res.status === 404) throw new Error('Complaint not found. Please check your reference number.');
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message || 'Could not fetch status. Try again.');
    } finally {
      setLoading(false);
    }
  }

  const badge = result ? (STATUS_BADGE[result.status] || STATUS_BADGE['SUBMITTED']) : null;
  const deptObj = result ? DEPARTMENTS.find(d => d.value === result.department) : null;

  return (
    <div className="p-6 space-y-5 animate-fade-up">
      <div>
        <label className="input-label">Reference Number <span className="text-red-500">*</span></label>
        <input
          type="text"
          value={refId}
          onChange={e => setRefId(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleTrack()}
          placeholder="e.g. a1b2c3d4-..."
          className="input-field font-mono"
        />
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-2xl text-red-700 font-body text-sm">{error}</div>
      )}

      <button
        onClick={handleTrack}
        disabled={loading || !refId.trim()}
        className="btn-primary w-full"
      >
        {loading ? <Spinner /> : '🔍 Track Complaint'}
      </button>

      {result && (
        <div className="bg-koisk-surface rounded-3xl p-5 space-y-4 animate-fade-up border border-koisk-blue/10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xl">{deptObj?.icon ?? '📋'}</span>
              <span className="font-display font-semibold text-koisk-navy">{deptObj?.label ?? result.department}</span>
            </div>
            <span className={clsx('badge', badge.cls)}>{badge.label}</span>
          </div>

          <div className="border-t border-koisk-blue/10 pt-4 space-y-3">
            <div>
              <p className="text-xs text-koisk-muted font-body uppercase tracking-wider">Category</p>
              <p className="font-body text-koisk-navy text-sm mt-0.5">{result.category}</p>
            </div>
            <div>
              <p className="text-xs text-koisk-muted font-body uppercase tracking-wider">Subject</p>
              <p className="font-body text-koisk-navy text-sm mt-0.5">{result.subject}</p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-koisk-muted font-body uppercase tracking-wider">Severity</p>
                <p className="font-body text-koisk-navy text-sm mt-0.5">{result.severity}</p>
              </div>
              <div>
                <p className="text-xs text-koisk-muted font-body uppercase tracking-wider">Filed On</p>
                <p className="font-body text-koisk-navy text-sm mt-0.5">
                  {new Date(result.created_at).toLocaleDateString('en-IN')}
                </p>
              </div>
            </div>
            <div className="bg-white rounded-2xl p-3 border border-koisk-blue/10">
              <p className="text-koisk-muted font-body text-sm">💬 {result.message}</p>
            </div>
          </div>

          <div>
            <p className="text-xs text-koisk-muted font-body uppercase tracking-wider mb-1">Reference ID</p>
            <p className="font-mono text-xs text-koisk-navy break-all">{result.reference_id}</p>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Main Export ─────────────────────────────────────────────────────────────

export default function ComplaintsScreen() {
  const navigate  = useNavigate();
  const [mode, setMode] = useState('submit'); // 'submit' | 'track'

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
          <span className="font-display font-bold text-white text-lg">Seva Mitra</span>
          <div className="w-16" />
        </div>
      </div>

      {/* ── Hero ─────────────────────────────────────────────────── */}
      <div className="bg-gradient-to-r from-violet-500 to-purple-600 px-6 py-8">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-center gap-4 animate-fade-up">
            <div className="w-16 h-16 rounded-3xl bg-white/20 flex items-center justify-center text-4xl shadow-lg">
              📣
            </div>
            <div>
              <h1 className="font-display font-bold text-white text-2xl">Complaints &amp; Grievances</h1>
              <p className="text-white/70 font-body text-sm mt-0.5">
                All departments · Electricity · Water · Gas · Municipal
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Mode Toggle ──────────────────────────────────────────── */}
      <div className="max-w-3xl mx-auto w-full px-4 pt-5">
        <div className="flex bg-white rounded-2xl p-1 shadow-sm border border-koisk-blue/10">
          {[
            { key: 'submit', label: '📝 New Complaint' },
            { key: 'track',  label: '🔍 Track Status'  },
          ].map(m => (
            <button
              key={m.key}
              onClick={() => setMode(m.key)}
              className={clsx(
                'flex-1 py-3 rounded-xl font-display font-semibold text-sm transition-all duration-200',
                mode === m.key
                  ? 'bg-koisk-teal text-white shadow-md'
                  : 'text-koisk-muted hover:text-koisk-navy',
              )}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Content ──────────────────────────────────────────────── */}
      <div className="max-w-3xl mx-auto w-full px-4 pb-10 mt-2">
        <div className="card">
          {mode === 'submit' ? <SubmitView /> : <TrackView />}
        </div>
      </div>
    </div>
  );
}
