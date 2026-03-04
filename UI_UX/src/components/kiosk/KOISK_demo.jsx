import { useState, useEffect, useRef } from "react";

// ── Fonts via Google ──────────────────────────────────────────────────────────
const FontLink = () => (
  <style>{`
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Sora:wght@300;400;600;700;800&display=swap');

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --navy:   #0A1628;
      --blue:   #1A3A6B;
      --teal:   #0EA5A0;
      --accent: #F0C93A;
      --surf:   #F4F6FB;
      --muted:  #7A8AA0;
      --white:  #FFFFFF;
      --danger: #E53E3E;
      --green:  #10B981;
    }

    body { font-family: 'Space Grotesk', sans-serif; background: var(--surf); }

    .screen { min-height: 100vh; display: flex; flex-direction: column; background: var(--surf); }

    /* Animations */
    @keyframes fadeUp   { from { opacity:0; transform:translateY(18px); } to { opacity:1; transform:translateY(0); } }
    @keyframes slideIn  { from { opacity:0; transform:translateX(-16px);} to { opacity:1; transform:translateX(0);  } }
    @keyframes pulse    { 0%,100%{transform:scale(1);}50%{transform:scale(1.04);} }
    @keyframes spin     { to { transform: rotate(360deg); } }
    @keyframes ripple   { 0%{transform:scale(0);opacity:.5;}100%{transform:scale(3);opacity:0;} }
    @keyframes shimmer  { 0%{background-position:-200% 0;}100%{background-position:200% 0;} }
    @keyframes checkIn  { 0%{transform:scale(0) rotate(-20deg);opacity:0;}80%{transform:scale(1.1);}100%{transform:scale(1);opacity:1;} }

    .fade-up  { animation: fadeUp  .45s cubic-bezier(.25,.8,.25,1) both; }
    .slide-in { animation: slideIn .35s cubic-bezier(.25,.8,.25,1) both; }

    .d1 { animation-delay: .05s; } .d2 { animation-delay: .12s; }
    .d3 { animation-delay: .20s; } .d4 { animation-delay: .28s; }
    .d5 { animation-delay: .36s; } .d6 { animation-delay: .44s; }

    /* Nav */
    .top-nav {
      background: var(--navy);
      padding: 14px 24px;
      display: flex; align-items: center; justify-content: space-between;
    }
    .top-nav .brand { font-family: 'Sora', sans-serif; font-weight: 800; font-size: 22px; color: var(--white); letter-spacing: -.5px; }
    .top-nav .greeting { font-size: 12px; color: rgba(255,255,255,.5); margin-bottom: 2px; }
    .top-nav .username { font-weight: 700; color: var(--white); font-size: 16px; }
    .nav-btn {
      background: rgba(255,255,255,.10); border: 1px solid rgba(255,255,255,.15);
      color: rgba(255,255,255,.75); font-size: 13px; font-family: inherit;
      padding: 8px 14px; border-radius: 10px; cursor: pointer; transition: all .2s;
    }
    .nav-btn:hover { background: rgba(255,255,255,.18); color: #fff; }

    /* Cards */
    .card {
      background: var(--white); border-radius: 20px;
      border: 1px solid rgba(26,58,107,.08); box-shadow: 0 2px 12px rgba(10,22,40,.06);
    }
    .card-hover {
      cursor: pointer; transition: transform .18s, box-shadow .18s, border-color .18s;
    }
    .card-hover:hover { transform: translateY(-3px); box-shadow: 0 8px 28px rgba(10,22,40,.12); border-color: rgba(14,165,160,.25); }
    .card-hover:active { transform: scale(.97); }

    /* Buttons */
    .btn-primary {
      background: var(--teal); color: #fff; border: none;
      font-family: 'Sora', sans-serif; font-weight: 700; font-size: 16px;
      padding: 16px 32px; border-radius: 14px; cursor: pointer;
      transition: all .2s; min-height: 56px; display: inline-flex; align-items: center; justify-content: center; gap: 8px;
    }
    .btn-primary:hover:not(:disabled) { background: var(--navy); box-shadow: 0 4px 18px rgba(14,165,160,.35); }
    .btn-primary:active:not(:disabled) { transform: scale(.97); }
    .btn-primary:disabled { opacity: .4; cursor: not-allowed; }

    .btn-secondary {
      background: white; color: var(--navy); border: 2px solid rgba(26,58,107,.15);
      font-family: 'Sora', sans-serif; font-weight: 600; font-size: 15px;
      padding: 14px 28px; border-radius: 14px; cursor: pointer;
      transition: all .2s; min-height: 52px; display: inline-flex; align-items: center; justify-content: center;
    }
    .btn-secondary:hover { border-color: var(--teal); color: var(--teal); }

    /* Inputs */
    .input-wrap { margin-bottom: 18px; }
    .input-label { display: block; font-size: 11px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: .8px; margin-bottom: 8px; }
    .input-field {
      width: 100%; background: var(--white); border: 2px solid rgba(26,58,107,.12);
      border-radius: 14px; padding: 16px 18px; font-size: 17px; color: var(--navy);
      font-family: inherit; outline: none; transition: all .2s; min-height: 58px;
    }
    .input-field:focus { border-color: var(--teal); box-shadow: 0 0 0 4px rgba(14,165,160,.10); }
    .input-field::placeholder { color: rgba(122,138,160,.55); }

    /* Badge */
    .badge { display: inline-flex; align-items: center; gap: 5px; padding: 4px 12px; border-radius: 100px; font-size: 11px; font-weight: 700; letter-spacing: .3px; }
    .badge-success { background: #ECFDF5; color: #047857; border: 1px solid #A7F3D0; }
    .badge-warn    { background: #FFFBEB; color: #B45309; border: 1px solid #FDE68A; }
    .badge-info    { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
    .badge-muted   { background: #F9FAFB; color: #6B7280; border: 1px solid #E5E7EB; }

    /* Language screen */
    .lang-screen {
      min-height: 100vh;
      background: linear-gradient(145deg, var(--navy) 0%, var(--blue) 55%, var(--teal) 100%);
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      padding: 40px 20px;
      position: relative; overflow: hidden;
    }
    .lang-screen::before {
      content: '';
      position: absolute; inset: 0;
      background-image: radial-gradient(circle at 2px 2px, rgba(255,255,255,.06) 1px, transparent 0);
      background-size: 36px 36px;
    }
    .lang-btn {
      position: relative; display: flex; flex-direction: column; align-items: center; gap: 6px;
      min-height: 100px; border-radius: 18px; padding: 16px 12px;
      font-family: 'Sora', sans-serif; font-weight: 600; font-size: 16px;
      transition: all .2s; border: 2px solid rgba(255,255,255,.2);
      background: rgba(255,255,255,.10); color: white; cursor: pointer;
    }
    .lang-btn:hover  { background: rgba(255,255,255,.18); border-color: rgba(255,255,255,.4); transform: translateY(-2px); }
    .lang-btn.active { background: var(--accent); color: var(--navy); border-color: var(--accent); transform: scale(1.04); box-shadow: 0 8px 24px rgba(240,201,58,.4); }
    .lang-btn:active { transform: scale(.96); }

    /* Service tiles */
    .service-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .svc-tile { padding: 20px 18px; border-radius: 20px; text-align: left; border: 1px solid rgba(26,58,107,.08); }
    .svc-icon-wrap { width: 48px; height: 48px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 22px; margin-bottom: 12px; box-shadow: inset 0 -3px 0 rgba(0,0,0,.12); }
    .svc-name  { font-family: 'Sora', sans-serif; font-weight: 700; color: var(--navy); font-size: 15px; }
    .svc-sub   { font-size: 12px; color: var(--muted); margin-top: 3px; }

    /* Steps */
    .steps-wrap { display: flex; align-items: center; gap: 6px; margin-bottom: 22px; justify-content: center; }
    .step-dot { width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 13px; transition: all .25s; }
    .step-line { flex: 1; height: 2px; max-width: 40px; transition: all .25s; }

    /* Receipt */
    .receipt-stamp {
      background: linear-gradient(135deg, #ECFDF5, #D1FAE5);
      border: 2px dashed #34D399; border-radius: 20px; padding: 28px 24px; text-align: center;
    }
    .check-circle {
      width: 64px; height: 64px; background: var(--green); border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 28px; margin: 0 auto 14px;
      animation: checkIn .5s cubic-bezier(.34,1.56,.64,1) both;
    }

    /* Shimmer loading */
    .shimmer {
      background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
      background-size: 200% 100%;
      animation: shimmer 1.4s infinite; border-radius: 8px;
    }

    /* Offline banner */
    .offline-banner { background: #FEF3C7; border: 1px solid #FCD34D; border-radius: 12px; padding: 10px 16px; display: flex; align-items: center; gap: 10px; font-size: 13px; color: #92400E; margin-bottom: 16px; }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-thumb { background: rgba(122,138,160,.3); border-radius: 99px; }

    .spinner { width: 40px; height: 40px; border: 4px solid rgba(14,165,160,.2); border-top-color: var(--teal); border-radius: 50%; animation: spin .8s linear infinite; }

    /* PIN dots */
    .pin-wrap { display: flex; justify-content: center; gap: 12px; margin: 8px 0 18px; }
    .pin-dot  { width: 16px; height: 16px; border-radius: 50%; border: 2px solid var(--teal); background: transparent; transition: background .15s; }
    .pin-dot.filled { background: var(--teal); }
    .numpad { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; max-width: 260px; margin: 0 auto; }
    .num-btn { aspect-ratio:1; border-radius: 14px; background: white; border: 1.5px solid rgba(26,58,107,.1); font-size: 20px; font-weight: 700; color: var(--navy); cursor: pointer; transition: all .15s; display: flex; align-items: center; justify-content: center; }
    .num-btn:hover  { background: var(--surf); border-color: var(--teal); }
    .num-btn:active { transform: scale(.92); background: rgba(14,165,160,.08); }
    .num-btn.del    { font-size: 18px; color: var(--muted); }
  `}</style>
);

// ── Data ──────────────────────────────────────────────────────────────────────
const LANGUAGES = [
  { code: "en", name: "English",    native: "English",    flag: "🇬🇧" },
  { code: "hi", name: "Hindi",      native: "हिन्दी",      flag: "🇮🇳" },
  { code: "kn", name: "Kannada",    native: "ಕನ್ನಡ",      flag: "🇮🇳" },
  { code: "ta", name: "Tamil",      native: "தமிழ்",        flag: "🇮🇳" },
  { code: "te", name: "Telugu",     native: "తెలుగు",      flag: "🇮🇳" },
  { code: "mr", name: "Marathi",    native: "मराठी",       flag: "🇮🇳" },
  { code: "od", name: "Odia",       native: "ଓଡ଼ିଆ",        flag: "🇮🇳" },
];

const DEMO_USER = {
  name: "Arjun Sharma",
  phone: "9876543210",
  consumerId: "KA-ELEC-204817",
  isDemo: true,
};

const DEMO_REQUESTS = [
  { id: 1, type: "ELECTRICITY_BILL",  reference: "TXN-2024-8821", createdAt: "2025-01-15", status: "COMPLETED",   amount: 1342 },
  { id: 2, type: "WATER_COMPLAINT",   reference: "CMP-2025-0042", createdAt: "2025-02-01", status: "IN_PROGRESS", amount: null },
  { id: 3, type: "GAS_CONNECTION",    reference: "CON-2024-9901", createdAt: "2024-12-10", status: "APPROVED",    amount: 500  },
  { id: 4, type: "MUNICIPAL_TAX",     reference: "TXN-2024-7710", createdAt: "2024-11-05", status: "COMPLETED",   amount: 4500 },
];

const SERVICES = [
  { key: "electricity", icon: "⚡", grad: "linear-gradient(135deg,#F59E0B,#EF4444)", label: "Electricity", sub: "Pay Bill · Complaint" },
  { key: "gas",         icon: "🔥", grad: "linear-gradient(135deg,#F97316,#DC2626)", label: "Gas",         sub: "Pay Bill · Connection" },
  { key: "water",       icon: "💧", grad: "linear-gradient(135deg,#3B82F6,#06B6D4)", label: "Water",       sub: "Pay Bill · Complaint" },
  { key: "municipal",   icon: "🏛️", grad: "linear-gradient(135deg,#10B981,#059669)", label: "Municipal",   sub: "Tax · Licence" },
];

const STATUS_CFG = {
  COMPLETED:   { cls: "badge-success", label: "Completed"   },
  IN_PROGRESS: { cls: "badge-warn",    label: "Processing"  },
  APPROVED:    { cls: "badge-info",    label: "Approved"    },
  PENDING:     { cls: "badge-muted",   label: "Pending"     },
};

const BILL = { consumerNo: "KA-ELEC-204817", billMonth: "2025-02", dueDate: "2025-03-10", amountDue: 1342 };

// ── Helpers ───────────────────────────────────────────────────────────────────
const greet = () => {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
};
const fmtINR  = n => "₹" + n.toLocaleString("en-IN");
const fmtDate = s => new Date(s).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });

// ── 1. Language Screen ────────────────────────────────────────────────────────
function LanguageScreen({ onContinue }) {
  const [selected, setSelected] = useState("en");
  return (
    <div className="lang-screen">
      <FontLink />
      {/* Logo */}
      <div className="fade-up" style={{ textAlign: "center", marginBottom: 32, position: "relative" }}>
        <div style={{ display: "inline-flex", alignItems: "center", gap: 14, marginBottom: 8 }}>
          <div style={{ width: 52, height: 52, borderRadius: 16, background: "rgba(240,201,58,.2)", border: "1.5px solid rgba(240,201,58,.4)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 24 }}>🏛️</div>
          <span style={{ fontFamily: "'Sora',sans-serif", fontWeight: 800, fontSize: 44, color: "white", letterSpacing: -2 }}>KOISK</span>
        </div>
        <p style={{ color: "rgba(240,201,58,.85)", fontWeight: 500, fontSize: 17 }}>Smart Civic Utility Kiosk</p>
      </div>

      {/* Title */}
      <div className="fade-up d1" style={{ textAlign: "center", marginBottom: 32 }}>
        <h1 style={{ fontFamily: "'Sora',sans-serif", fontWeight: 800, color: "white", fontSize: 28, marginBottom: 6 }}>Welcome to KOISK</h1>
        <p style={{ color: "rgba(255,255,255,.55)", fontSize: 16 }}>Choose your preferred language to continue</p>
      </div>

      {/* Grid */}
      <div className="fade-up d2" style={{ width: "100%", maxWidth: 560, display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10, marginBottom: 32 }}>
        {LANGUAGES.map((l, i) => (
          <button key={l.code} className={`lang-btn ${selected === l.code ? "active" : ""}`} onClick={() => setSelected(l.code)} style={{ animationDelay: `${i * 60}ms` }}>
            {selected === l.code && <span style={{ position: "absolute", top: 7, right: 9, fontSize: 10, background: "rgba(10,22,40,.2)", width: 18, height: 18, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center" }}>✓</span>}
            <span style={{ fontSize: 26 }}>{l.flag}</span>
            <span style={{ fontSize: 14 }}>{l.native}</span>
            {l.native !== l.name && <span style={{ fontSize: 11, opacity: .65 }}>{l.name}</span>}
          </button>
        ))}
      </div>

      {/* Current + Continue */}
      <div className="fade-up d3" style={{ textAlign: "center" }}>
        <p style={{ color: "rgba(255,255,255,.45)", fontSize: 13, marginBottom: 16 }}>
          Current: <strong style={{ color: "white" }}>{LANGUAGES.find(l => l.code === selected)?.native}</strong>
        </p>
        <button className="btn-primary" style={{ background: "var(--accent)", color: "var(--navy)", fontSize: 18, minWidth: 220, boxShadow: "0 6px 24px rgba(240,201,58,.4)" }} onClick={onContinue}>
          Continue →
        </button>
      </div>
      <p style={{ marginTop: 20, color: "rgba(255,255,255,.25)", fontSize: 12 }}>7 languages supported</p>
    </div>
  );
}

// ── 2. Login Screen ───────────────────────────────────────────────────────────
function LoginScreen({ onLogin, onBack }) {
  const [phone, setPhone] = useState("");
  const [pin,   setPin]   = useState("");
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState("");

  const handleDemo = async () => {
    setLoading(true); setError("");
    await new Promise(r => setTimeout(r, 900));
    setLoading(false);
    onLogin(DEMO_USER);
  };

  const handleSubmit = async () => {
    if (phone.length < 10 || pin.length < 4) return;
    setLoading(true); setError("");
    await new Promise(r => setTimeout(r, 1000));
    setLoading(false);
    if (phone === "9876543210" && pin === "1234") {
      onLogin({ ...DEMO_USER, isDemo: false });
    } else {
      setError("Phone number or PIN is incorrect.");
    }
  };

  const addPin = (d) => { if (pin.length < 4) setPin(p => p + d); };
  const delPin = () => setPin(p => p.slice(0, -1));

  return (
    <div className="screen">
      {/* Nav */}
      <div className="top-nav">
        <button className="nav-btn" onClick={onBack}>← Back</button>
        <span className="brand">KOISK</span>
        <button className="nav-btn" onClick={onBack}>Change Language</button>
      </div>

      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: "32px 20px" }}>
        <div className="fade-up" style={{ width: "100%", maxWidth: 400 }}>
          {/* Header */}
          <div style={{ textAlign: "center", marginBottom: 28 }}>
            <div style={{ width: 60, height: 60, background: "rgba(14,165,160,.1)", borderRadius: 18, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 28, margin: "0 auto 14px" }}>🔐</div>
            <h1 style={{ fontFamily: "'Sora',sans-serif", fontWeight: 800, fontSize: 28, color: "var(--navy)", marginBottom: 4 }}>Sign In</h1>
            <p style={{ color: "var(--muted)", fontSize: 15 }}>Enter your registered phone number and PIN</p>
          </div>

          {error && (
            <div style={{ background: "#FEF2F2", border: "1px solid #FECACA", borderRadius: 12, padding: "12px 16px", marginBottom: 18, color: "#B91C1C", fontSize: 14, textAlign: "center" }}>{error}</div>
          )}

          {/* Phone */}
          <div className="input-wrap">
            <label className="input-label">Phone Number</label>
            <input type="tel" className="input-field" value={phone} onChange={e => setPhone(e.target.value.replace(/\D/g,"").slice(0,10))} placeholder="Enter 10-digit mobile number" />
          </div>

          {/* PIN dots */}
          <label className="input-label" style={{ display: "block", marginBottom: 10 }}>PIN</label>
          <div className="pin-wrap">
            {[0,1,2,3].map(i => <div key={i} className={`pin-dot ${i < pin.length ? "filled" : ""}`} />)}
          </div>
          <div className="numpad" style={{ marginBottom: 22 }}>
            {["1","2","3","4","5","6","7","8","9","","0","⌫"].map((k, i) => (
              k === "" ? <div key={i} /> :
              <button key={i} className={`num-btn ${k === "⌫" ? "del" : ""}`}
                onClick={() => k === "⌫" ? delPin() : addPin(k)}>
                {k}
              </button>
            ))}
          </div>

          <button className="btn-primary" style={{ width: "100%", marginBottom: 12 }}
            disabled={loading || phone.length < 10 || pin.length < 4}
            onClick={handleSubmit}>
            {loading ? <span className="spinner" style={{ width: 22, height: 22, borderWidth: 3 }} /> : "Sign In"}
          </button>

          {/* Divider */}
          <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "18px 0" }}>
            <div style={{ flex: 1, height: 1, background: "rgba(26,58,107,.1)" }} />
            <span style={{ color: "var(--muted)", fontSize: 13 }}>OR</span>
            <div style={{ flex: 1, height: 1, background: "rgba(26,58,107,.1)" }} />
          </div>

          <button onClick={handleDemo} disabled={loading}
            style={{ width: "100%", padding: "16px", border: "2px dashed rgba(14,165,160,.4)", background: "transparent", borderRadius: 14, cursor: "pointer", transition: "all .2s", color: "var(--teal)", fontFamily: "'Sora',sans-serif", fontWeight: 700, fontSize: 15 }}>
            <div>Use Demo Account</div>
            <div style={{ fontSize: 12, fontWeight: 400, color: "var(--muted)", marginTop: 3 }}>Pre-loaded with sample data</div>
          </button>

          <p style={{ textAlign: "center", marginTop: 20, fontSize: 13, color: "var(--muted)" }}>
            <span style={{ fontStyle: "italic", opacity: .7 }}>Demo: phone 9876543210 · PIN 1234</span>
          </p>
        </div>
      </div>
    </div>
  );
}

// ── 3. Dashboard ──────────────────────────────────────────────────────────────
function Dashboard({ user, onLogout, onService }) {
  const [loading, setLoading] = useState(true);
  const [requests, setRequests] = useState([]);

  useEffect(() => {
    setTimeout(() => { setRequests(DEMO_REQUESTS); setLoading(false); }, 800);
  }, []);

  return (
    <div className="screen">
      {/* Nav */}
      <div className="top-nav">
        <div>
          <p className="greeting">{greet()},</p>
          <p className="username">{user.name.split(" ")[0]}</p>
        </div>
        <span className="brand">KOISK</span>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {user.isDemo && <span className="badge badge-warn" style={{ fontSize: 10 }}>DEMO</span>}
          <button className="nav-btn" onClick={onLogout}>↩ Logout</button>
        </div>
      </div>

      <div style={{ flex: 1, maxWidth: 640, margin: "0 auto", width: "100%", padding: "24px 16px", display: "flex", flexDirection: "column", gap: 28 }}>

        {/* Services */}
        <section className="fade-up">
          <h2 style={{ fontFamily: "'Sora',sans-serif", fontWeight: 700, color: "var(--navy)", fontSize: 17, marginBottom: 14, display: "flex", alignItems: "center", gap: 8 }}>
            🏢 Services
          </h2>
          <div className="service-grid">
            {SERVICES.map((s, i) => (
              <button key={s.key} className="card card-hover svc-tile fade-up"
                style={{ animationDelay: `${i * 70}ms`, background: "white", textAlign: "left", border: "none", width: "100%", fontFamily: "inherit", cursor: "pointer" }}
                onClick={() => onService(s.key)}>
                <div className="svc-icon-wrap" style={{ background: s.grad }}>{s.icon}</div>
                <p className="svc-name">{s.label}</p>
                <p className="svc-sub">{s.sub}</p>
              </button>
            ))}
          </div>
        </section>

        {/* Recent Activity */}
        <section className="fade-up d2">
          <h2 style={{ fontFamily: "'Sora',sans-serif", fontWeight: 700, color: "var(--navy)", fontSize: 17, marginBottom: 14, display: "flex", alignItems: "center", gap: 8 }}>
            📋 Recent Activity
          </h2>

          {loading ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {[1,2,3].map(i => <div key={i} className="shimmer" style={{ height: 72, borderRadius: 16 }} />)}
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {requests.map((r, i) => {
                const sc = STATUS_CFG[r.status] || STATUS_CFG.PENDING;
                return (
                  <div key={r.id} className="card slide-in"
                    style={{ padding: "14px 18px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, animationDelay: `${i * 70 + 200}ms` }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p style={{ fontWeight: 700, color: "var(--navy)", fontSize: 14, marginBottom: 3 }}>{r.type.replace(/_/g," ")}</p>
                      <p style={{ fontSize: 12, color: "var(--muted)" }}>{r.reference} · {fmtDate(r.createdAt)}</p>
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 5, flexShrink: 0 }}>
                      <span className={`badge ${sc.cls}`}>{sc.label}</span>
                      {r.amount && <span style={{ fontWeight: 800, color: "var(--navy)", fontSize: 15 }}>{fmtINR(r.amount)}</span>}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        {/* Consumer ID */}
        {user.consumerId && (
          <div className="card fade-up d4" style={{ padding: "16px 20px", display: "flex", alignItems: "center", gap: 14 }}>
            <span style={{ fontSize: 28 }}>🪪</span>
            <div>
              <p style={{ fontSize: 10, color: "var(--muted)", textTransform: "uppercase", letterSpacing: ".8px", marginBottom: 3 }}>Consumer ID</p>
              <p style={{ fontFamily: "monospace", fontWeight: 600, color: "var(--navy)", fontSize: 15 }}>{user.consumerId}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── 4. Payment Flow ───────────────────────────────────────────────────────────
function PaymentFlow({ dept, onClose, onSuccess }) {
  const [step,   setStep]   = useState("summary"); // summary | method | processing | done | failed
  const [method, setMethod] = useState("upi");
  const [upiId,  setUpiId]  = useState("");
  const [offline] = useState(false);

  const deptInfo = SERVICES.find(s => s.key === dept) || SERVICES[0];

  const handlePay = async () => {
    setStep("processing");
    await new Promise(r => setTimeout(r, 2200));
    setStep("done");
  };

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(10,22,40,.6)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 999, padding: 16, backdropFilter: "blur(4px)" }}>
      <div className="fade-up card" style={{ maxWidth: 480, width: "100%", padding: "28px 24px", maxHeight: "90vh", overflowY: "auto" }}>

        {offline && (
          <div className="offline-banner">⚠️ No internet — payment will be queued offline.</div>
        )}

        {/* Steps indicator */}
        {!["processing","done"].includes(step) && (
          <div className="steps-wrap">
            {["Summary","Method","Done"].map((label, i) => {
              const stepIdx = { summary: 0, method: 1, done: 2 }[step] ?? 0;
              const active  = i <= stepIdx;
              return (
                <div key={label} style={{ display: "flex", alignItems: "center", gap: 6, flex: i < 2 ? 1 : undefined }}>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
                    <div className="step-dot" style={{ background: active ? "var(--teal)" : "#E5E7EB", color: active ? "white" : "#9CA3AF" }}>
                      {i < stepIdx ? "✓" : i + 1}
                    </div>
                    <span style={{ fontSize: 10, color: active ? "var(--teal)" : "#9CA3AF" }}>{label}</span>
                  </div>
                  {i < 2 && <div className="step-line" style={{ background: i < stepIdx ? "var(--teal)" : "#E5E7EB", flex: 1, marginBottom: 14 }} />}
                </div>
              );
            })}
          </div>
        )}

        {/* Step: Summary */}
        {step === "summary" && (
          <div className="fade-up">
            <div style={{ background: "#F0F9FF", border: "1px solid #BAE6FD", borderRadius: 14, padding: 20, marginBottom: 20 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 14 }}>
                <div style={{ width: 44, height: 44, borderRadius: 12, background: deptInfo.grad, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22 }}>{deptInfo.icon}</div>
                <div>
                  <h2 style={{ fontSize: 17, color: "#0C4A6E", fontFamily: "'Sora',sans-serif", fontWeight: 700 }}>{deptInfo.label} Bill</h2>
                  <p style={{ fontSize: 12, color: "#0369A1", marginTop: 2 }}>Consumer: {BILL.consumerNo}</p>
                </div>
              </div>
              {[["Billing Period","February 2025"],["Due Date",fmtDate(BILL.dueDate)]].map(([k,v]) => (
                <div key={k} style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 8 }}>
                  <span style={{ color: "#6B7280" }}>{k}</span>
                  <span style={{ fontWeight: 600, color: "#111827" }}>{v}</span>
                </div>
              ))}
              <hr style={{ border: "none", borderTop: "1px solid #BAE6FD", margin: "10px 0" }} />
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontWeight: 700, color: "#0C4A6E", fontSize: 15 }}>Amount Due</span>
                <span style={{ fontWeight: 800, color: "#0369A1", fontSize: 26, fontFamily: "'Sora',sans-serif" }}>{fmtINR(BILL.amountDue)}</span>
              </div>
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              <button className="btn-secondary" style={{ flex: 1 }} onClick={onClose}>Cancel</button>
              <button className="btn-primary"   style={{ flex: 2 }} onClick={() => setStep("method")}>Continue to Payment →</button>
            </div>
          </div>
        )}

        {/* Step: Method */}
        {step === "method" && (
          <div className="fade-up">
            <h2 style={{ fontFamily: "'Sora',sans-serif", fontWeight: 700, color: "var(--navy)", fontSize: 19, marginBottom: 16, textAlign: "center" }}>Choose Payment Method</h2>

            {/* Method cards */}
            {[
              { id: "upi",  icon: "📲", label: "UPI",         sub: "PhonePe, GPay, Paytm"    },
              { id: "card", icon: "💳", label: "Card",        sub: "Debit / Credit card"      },
              { id: "netb", icon: "🏦", label: "Net Banking",  sub: "All major banks"          },
            ].map(m => (
              <div key={m.id} onClick={() => setMethod(m.id)}
                style={{
                  display: "flex", alignItems: "center", gap: 14, padding: "14px 16px",
                  borderRadius: 14, border: `2px solid ${method === m.id ? "var(--teal)" : "rgba(26,58,107,.1)"}`,
                  background: method === m.id ? "rgba(14,165,160,.05)" : "white",
                  cursor: "pointer", marginBottom: 10, transition: "all .15s",
                }}>
                <span style={{ fontSize: 26 }}>{m.icon}</span>
                <div style={{ flex: 1 }}>
                  <p style={{ fontWeight: 700, color: "var(--navy)", fontSize: 15 }}>{m.label}</p>
                  <p style={{ fontSize: 12, color: "var(--muted)" }}>{m.sub}</p>
                </div>
                <div style={{ width: 20, height: 20, borderRadius: "50%", border: `2px solid ${method === m.id ? "var(--teal)" : "#D1D5DB"}`, background: method === m.id ? "var(--teal)" : "white", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  {method === m.id && <div style={{ width: 8, height: 8, borderRadius: "50%", background: "white" }} />}
                </div>
              </div>
            ))}

            {/* UPI input */}
            {method === "upi" && (
              <div className="input-wrap fade-up" style={{ marginTop: 8 }}>
                <label className="input-label">UPI ID</label>
                <input type="text" className="input-field" value={upiId} onChange={e => setUpiId(e.target.value)} placeholder="e.g. user@upi" />
              </div>
            )}

            {method === "card" && (
              <div className="fade-up" style={{ marginTop: 8 }}>
                <div className="input-wrap">
                  <label className="input-label">Card Number</label>
                  <input className="input-field" placeholder="•••• •••• •••• ••••" maxLength={19} />
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <div className="input-wrap"><label className="input-label">Expiry</label><input className="input-field" placeholder="MM/YY" /></div>
                  <div className="input-wrap"><label className="input-label">CVV</label><input className="input-field" placeholder="•••" type="password" maxLength={3} /></div>
                </div>
              </div>
            )}

            <div style={{ display: "flex", gap: 10, marginTop: 6 }}>
              <button className="btn-secondary" style={{ flex: 1 }} onClick={() => setStep("summary")}>← Back</button>
              <button className="btn-primary"   style={{ flex: 2 }} onClick={handlePay}>Pay {fmtINR(BILL.amountDue)}</button>
            </div>
          </div>
        )}

        {/* Step: Processing */}
        {step === "processing" && (
          <div style={{ textAlign: "center", padding: "48px 16px" }}>
            <div className="spinner" style={{ margin: "0 auto 20px" }} />
            <p style={{ fontWeight: 600, color: "var(--navy)", fontSize: 17 }}>Processing your payment…</p>
            <p style={{ color: "var(--muted)", fontSize: 13, marginTop: 6 }}>Please do not close this window</p>
          </div>
        )}

        {/* Step: Done */}
        {step === "done" && (
          <div className="fade-up" style={{ textAlign: "center" }}>
            <div className="receipt-stamp">
              <div className="check-circle">✓</div>
              <h2 style={{ fontFamily: "'Sora',sans-serif", fontWeight: 800, color: "#065F46", fontSize: 22, marginBottom: 6 }}>Payment Successful!</h2>
              <p style={{ color: "#047857", fontSize: 14, marginBottom: 16 }}>Your {deptInfo.label} bill has been paid.</p>
              {[["Amount Paid", fmtINR(BILL.amountDue)],["Reference","TXN-2025-" + Math.floor(Math.random()*9000+1000)],["Date", fmtDate(new Date().toISOString())]].map(([k,v]) => (
                <div key={k} style={{ display: "flex", justifyContent: "space-between", fontSize: 13, borderTop: "1px solid rgba(52,211,153,.3)", padding: "8px 0" }}>
                  <span style={{ color: "#065F46" }}>{k}</span>
                  <span style={{ fontWeight: 700, color: "#065F46" }}>{v}</span>
                </div>
              ))}
            </div>
            <button className="btn-primary" style={{ marginTop: 20, width: "100%" }} onClick={() => { onSuccess?.(); onClose(); }}>Back to Dashboard</button>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Root App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [screen,      setScreen]      = useState("language"); // language | login | dashboard
  const [user,        setUser]        = useState(null);
  const [activeDept,  setActiveDept]  = useState(null);
  const [paidDepts,   setPaidDepts]   = useState([]);

  const handleLogin  = (u)    => { setUser(u); setScreen("dashboard"); };
  const handleLogout = ()     => { setUser(null); setScreen("language"); };
  const handleService= (dept) => setActiveDept(dept);
  const handlePaid   = ()     => { if (activeDept) setPaidDepts(p => [...p, activeDept]); };

  return (
    <>
      <FontLink />
      {screen === "language"  && <LanguageScreen onContinue={() => setScreen("login")} />}
      {screen === "login"     && <LoginScreen    onLogin={handleLogin} onBack={() => setScreen("language")} />}
      {screen === "dashboard" && user && (
        <Dashboard user={user} onLogout={handleLogout} onService={handleService} />
      )}
      {activeDept && (
        <PaymentFlow dept={activeDept} onClose={() => setActiveDept(null)} onSuccess={handlePaid} />
      )}
    </>
  );
}
