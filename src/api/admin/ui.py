"""
src/api/admin/ui.py
===================
Localhost-only admin panel — served at /admin as a single HTML page.
Mount this in main.py AFTER all other routers.

Usage in main.py:
    from src.api.admin.ui import mount_admin_ui
    mount_admin_ui(app)
"""

import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


# ─── Localhost Guard Middleware ───────────────────────────────────────────────

class LocalhostOnlyMiddleware(BaseHTTPMiddleware):
    """Block any request to /admin* that isn't from 127.0.0.1 / ::1."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/admin"):
            client_host = request.client.host if request.client else ""
            if client_host not in ("127.0.0.1", "::1", "localhost"):
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Admin panel is only accessible from localhost."},
                )
        return await call_next(request)


# ─── HTML ─────────────────────────────────────────────────────────────────────

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>KOISK Admin</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:       #0a0c0f;
    --surface:  #111418;
    --border:   #1e2329;
    --border2:  #2a3040;
    --accent:   #00d4aa;
    --accent2:  #0096ff;
    --warn:     #f59e0b;
    --danger:   #ef4444;
    --success:  #22c55e;
    --text:     #e2e8f0;
    --muted:    #64748b;
    --mono:     'IBM Plex Mono', monospace;
    --sans:     'IBM Plex Sans', sans-serif;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--sans);
    font-size: 14px;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  /* ── Header ── */
  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 28px;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
    z-index: 100;
  }

  .logo {
    font-family: var(--mono);
    font-size: 15px;
    font-weight: 600;
    letter-spacing: .06em;
    color: var(--accent);
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .logo-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.4;transform:scale(.8)} }

  .header-right { display: flex; align-items: center; gap: 14px; }

  .badge {
    font-family: var(--mono);
    font-size: 11px;
    padding: 3px 9px;
    border-radius: 3px;
    background: rgba(0,212,170,.12);
    color: var(--accent);
    border: 1px solid rgba(0,212,170,.25);
    letter-spacing: .04em;
  }

  .badge.warn { background: rgba(245,158,11,.12); color: var(--warn); border-color: rgba(245,158,11,.25); }

  #logout-btn {
    font-family: var(--mono);
    font-size: 11px;
    padding: 5px 14px;
    border: 1px solid var(--border2);
    border-radius: 4px;
    background: transparent;
    color: var(--muted);
    cursor: pointer;
    transition: all .2s;
  }
  #logout-btn:hover { border-color: var(--danger); color: var(--danger); }

  /* ── Layout ── */
  .shell { display: flex; flex: 1; }

  /* ── Sidebar ── */
  aside {
    width: 200px;
    background: var(--surface);
    border-right: 1px solid var(--border);
    padding: 20px 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
    flex-shrink: 0;
  }

  .nav-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 9px 20px;
    font-size: 13px;
    color: var(--muted);
    cursor: pointer;
    border-left: 2px solid transparent;
    transition: all .15s;
    font-family: var(--sans);
    font-weight: 400;
    user-select: none;
  }

  .nav-item:hover { color: var(--text); background: rgba(255,255,255,.03); }

  .nav-item.active {
    color: var(--accent);
    border-left-color: var(--accent);
    background: rgba(0,212,170,.06);
    font-weight: 500;
  }

  .nav-icon { font-size: 15px; width: 18px; text-align: center; }

  .nav-divider {
    height: 1px;
    background: var(--border);
    margin: 10px 16px;
  }

  /* ── Main ── */
  main {
    flex: 1;
    overflow-y: auto;
    padding: 28px;
  }

  /* ── Login screen ── */
  #login-screen {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    background: var(--bg);
  }

  .login-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 40px;
    width: 360px;
  }

  .login-title {
    font-family: var(--mono);
    font-size: 20px;
    color: var(--accent);
    margin-bottom: 6px;
    font-weight: 600;
  }

  .login-sub {
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 28px;
    font-family: var(--mono);
  }

  .field { margin-bottom: 16px; }

  .field label {
    display: block;
    font-size: 11px;
    font-family: var(--mono);
    color: var(--muted);
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: .06em;
  }

  .field input, .field select, .field textarea {
    width: 100%;
    padding: 9px 12px;
    background: var(--bg);
    border: 1px solid var(--border2);
    border-radius: 4px;
    color: var(--text);
    font-family: var(--mono);
    font-size: 13px;
    outline: none;
    transition: border-color .2s;
  }

  .field input:focus, .field select:focus, .field textarea:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 2px rgba(0,212,170,.08);
  }

  .field textarea { resize: vertical; min-height: 70px; }
  .field select option { background: var(--surface); }

  .btn {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 9px 18px;
    border-radius: 4px;
    font-family: var(--mono);
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    border: 1px solid transparent;
    transition: all .18s;
    letter-spacing: .03em;
  }

  .btn-primary {
    background: var(--accent);
    color: #0a0c0f;
    border-color: var(--accent);
  }
  .btn-primary:hover { background: #00bfa0; }

  .btn-ghost {
    background: transparent;
    color: var(--text);
    border-color: var(--border2);
  }
  .btn-ghost:hover { border-color: var(--accent); color: var(--accent); }

  .btn-danger {
    background: transparent;
    color: var(--danger);
    border-color: rgba(239,68,68,.4);
  }
  .btn-danger:hover { background: rgba(239,68,68,.1); }

  .btn:disabled { opacity: .4; cursor: not-allowed; }

  .error-msg {
    font-family: var(--mono);
    font-size: 12px;
    color: var(--danger);
    margin-top: 12px;
    padding: 8px 12px;
    background: rgba(239,68,68,.08);
    border: 1px solid rgba(239,68,68,.2);
    border-radius: 4px;
    display: none;
  }

  /* ── Page header ── */
  .page-header {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border);
  }

  .page-title {
    font-family: var(--mono);
    font-size: 18px;
    font-weight: 600;
    color: var(--text);
  }

  .page-sub { font-size: 12px; color: var(--muted); margin-top: 4px; font-family: var(--mono); }

  /* ── Health cards ── */
  .stat-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 14px; margin-bottom: 24px; }

  .stat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 16px 18px;
  }

  .stat-label { font-size: 11px; color: var(--muted); font-family: var(--mono); text-transform: uppercase; letter-spacing: .06em; margin-bottom: 8px; }

  .stat-value { font-family: var(--mono); font-size: 20px; font-weight: 600; color: var(--accent); }

  .stat-value.ok  { color: var(--success); }
  .stat-value.err { color: var(--danger);  }
  .stat-value.sm  { font-size: 13px; }

  /* ── Table ── */
  .table-wrap { overflow-x: auto; border: 1px solid var(--border); border-radius: 6px; }

  table { width: 100%; border-collapse: collapse; }

  th {
    background: var(--surface);
    padding: 10px 14px;
    text-align: left;
    font-size: 11px;
    font-family: var(--mono);
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: .06em;
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
  }

  td {
    padding: 10px 14px;
    border-bottom: 1px solid var(--border);
    font-size: 12px;
    font-family: var(--mono);
    vertical-align: top;
  }

  tr:last-child td { border-bottom: none; }
  tr:hover td { background: rgba(255,255,255,.02); }

  .pill {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 10px;
    font-family: var(--mono);
    font-weight: 500;
    letter-spacing: .04em;
  }

  .pill-get    { background: rgba(34,197,94,.12);  color: #22c55e; }
  .pill-post   { background: rgba(0,150,255,.12);  color: #60a5fa; }
  .pill-patch  { background: rgba(245,158,11,.12); color: var(--warn); }
  .pill-delete { background: rgba(239,68,68,.12);  color: var(--danger); }
  .pill-ok     { background: rgba(34,197,94,.12);  color: #22c55e; }
  .pill-fail   { background: rgba(239,68,68,.12);  color: var(--danger); }
  .pill-pend   { background: rgba(245,158,11,.12); color: var(--warn); }

  /* ── Logs ── */
  .log-box {
    background: #05070a;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 16px;
    font-family: var(--mono);
    font-size: 11.5px;
    line-height: 1.7;
    height: 500px;
    overflow-y: auto;
    color: #94a3b8;
    white-space: pre-wrap;
    word-break: break-all;
  }

  .log-box .log-err  { color: var(--danger); }
  .log-box .log-warn { color: var(--warn); }
  .log-box .log-ok   { color: var(--success); }
  .log-box .log-info { color: var(--accent2); }

  /* ── Config form ── */
  .section {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 22px;
    margin-bottom: 20px;
  }

  .section-title {
    font-family: var(--mono);
    font-size: 13px;
    font-weight: 600;
    color: var(--accent);
    margin-bottom: 18px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
  }

  .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

  .toast {
    position: fixed;
    bottom: 24px;
    right: 24px;
    padding: 12px 18px;
    border-radius: 5px;
    font-family: var(--mono);
    font-size: 12px;
    z-index: 999;
    opacity: 0;
    transform: translateY(10px);
    transition: all .3s;
    pointer-events: none;
  }

  .toast.show { opacity: 1; transform: translateY(0); }
  .toast.ok   { background: rgba(34,197,94,.15); border: 1px solid rgba(34,197,94,.3); color: var(--success); }
  .toast.err  { background: rgba(239,68,68,.15); border: 1px solid rgba(239,68,68,.3); color: var(--danger); }

  .spin {
    display: inline-block;
    width: 14px; height: 14px;
    border: 2px solid rgba(0,212,170,.2);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin .6s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .filters { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; align-items: flex-end; }
  .filters .field { margin-bottom: 0; }
  .filters .field input, .filters .field select { width: auto; min-width: 130px; }

  .empty { text-align: center; color: var(--muted); padding: 40px; font-family: var(--mono); font-size: 13px; }

  .tab { display: none; }
  .tab.active { display: block; }

  #app-shell { display: none; flex: 1; flex-direction: column; }
  #app-shell.visible { display: flex; }
</style>
</head>
<body>

<!-- ── Login ── -->
<div id="login-screen">
  <div class="login-card">
    <div class="login-title">KOISK/ADMIN</div>
    <div class="login-sub">// localhost access only</div>
    <div class="field">
      <label>Username</label>
      <input id="l-user" type="text" placeholder="admin" autocomplete="username" />
    </div>
    <div class="field">
      <label>Password</label>
      <input id="l-pass" type="password" placeholder="••••••••" autocomplete="current-password"
             onkeydown="if(event.key==='Enter')doLogin()" />
    </div>
    <button class="btn btn-primary" onclick="doLogin()" id="login-btn" style="width:100%">
      Sign in
    </button>
    <div id="login-err" class="error-msg"></div>
  </div>
</div>

<!-- ── App Shell ── -->
<div id="app-shell">
  <header>
    <div class="logo">
      <div class="logo-dot"></div>
      KOISK ADMIN
    </div>
    <div class="header-right">
      <span class="badge warn" id="h-role">—</span>
      <span class="badge" id="h-dept">—</span>
      <button id="logout-btn" onclick="doLogout()">logout</button>
    </div>
  </header>

  <div class="shell">
    <aside>
      <div class="nav-item active" onclick="nav('health')"  data-tab="health">
        <span class="nav-icon">◈</span> Health
      </div>
      <div class="nav-item" onclick="nav('routes')"  data-tab="routes">
        <span class="nav-icon">⊞</span> Routes
      </div>
      <div class="nav-divider"></div>
      <div class="nav-item" onclick="nav('requests')" data-tab="requests">
        <span class="nav-icon">⊡</span> Requests
      </div>
      <div class="nav-item" onclick="nav('payments')" data-tab="payments">
        <span class="nav-icon">⊟</span> Payments
      </div>
      <div class="nav-divider"></div>
      <div class="nav-item" onclick="nav('config')" data-tab="config">
        <span class="nav-icon">⊛</span> Config
      </div>
      <div class="nav-item" onclick="nav('logs')" data-tab="logs">
        <span class="nav-icon">⊜</span> Logs
      </div>
    </aside>

    <main>

      <!-- Health -->
      <div class="tab active" id="tab-health">
        <div class="page-header">
          <div>
            <div class="page-title">Health</div>
            <div class="page-sub">Live API status</div>
          </div>
          <button class="btn btn-ghost" onclick="loadHealth()">↺ Refresh</button>
        </div>
        <div class="stat-grid" id="health-grid">
          <div class="stat-card"><div class="stat-label">Status</div><div class="stat-value" id="hs-status">—</div></div>
          <div class="stat-card"><div class="stat-label">Timestamp</div><div class="stat-value sm" id="hs-ts">—</div></div>
          <div class="stat-card"><div class="stat-label">Mock Payment</div><div class="stat-value" id="hs-mock">—</div></div>
        </div>
        <div class="section">
          <div class="section-title">Active Departments</div>
          <div id="hs-depts" style="display:flex;gap:10px;flex-wrap:wrap;"></div>
        </div>
      </div>

      <!-- Routes -->
      <div class="tab" id="tab-routes">
        <div class="page-header">
          <div>
            <div class="page-title">Routes</div>
            <div class="page-sub">All registered API endpoints</div>
          </div>
          <input id="route-filter" placeholder="filter…" style="background:var(--surface);border:1px solid var(--border2);color:var(--text);padding:7px 12px;border-radius:4px;font-family:var(--mono);font-size:12px;outline:none;width:200px" oninput="filterRoutes()" />
        </div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Method</th><th>Path</th><th>Tags</th></tr></thead>
            <tbody id="routes-body"></tbody>
          </table>
        </div>
      </div>

      <!-- Requests -->
      <div class="tab" id="tab-requests">
        <div class="page-header">
          <div>
            <div class="page-title">Service Requests</div>
            <div class="page-sub">View and manage service requests</div>
          </div>
          <button class="btn btn-ghost" onclick="loadRequests()">↺ Refresh</button>
        </div>
        <div class="filters">
          <div class="field">
            <label>Department</label>
            <select id="req-dept" onchange="loadRequests()">
              <option value="">All</option>
              <option>electricity</option><option>water</option>
              <option>gas</option><option>municipal</option>
            </select>
          </div>
          <div class="field">
            <label>Status</label>
            <select id="req-status" onchange="loadRequests()">
              <option value="">All</option>
              <option>PENDING</option><option>IN_PROGRESS</option>
              <option>DELIVERED</option><option>FAILED</option><option>CANCELLED</option>
            </select>
          </div>
          <div class="field">
            <label>Limit</label>
            <input id="req-limit" type="number" value="25" min="1" max="200" style="width:80px" onchange="loadRequests()" />
          </div>
        </div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>ID</th><th>Dept</th><th>Status</th><th>Created</th><th>Action</th></tr></thead>
            <tbody id="requests-body"></tbody>
          </table>
        </div>
        <div id="req-total" style="font-family:var(--mono);font-size:11px;color:var(--muted);margin-top:10px;"></div>
      </div>

      <!-- Payments -->
      <div class="tab" id="tab-payments">
        <div class="page-header">
          <div>
            <div class="page-title">Payments</div>
            <div class="page-sub">Payment records scoped to your role</div>
          </div>
          <button class="btn btn-ghost" onclick="loadPayments()">↺ Refresh</button>
        </div>
        <div class="filters">
          <div class="field">
            <label>Department</label>
            <select id="pay-dept" onchange="loadPayments()">
              <option value="">All</option>
              <option>electricity</option><option>water</option>
              <option>gas</option><option>municipal</option>
            </select>
          </div>
          <div class="field">
            <label>Status</label>
            <select id="pay-status" onchange="loadPayments()">
              <option value="">All</option>
              <option>captured</option><option>pending</option>
              <option>failed</option><option>refunded</option>
            </select>
          </div>
          <div class="field">
            <label>Limit</label>
            <input id="pay-limit" type="number" value="25" min="1" max="200" style="width:80px" onchange="loadPayments()" />
          </div>
        </div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>ID</th><th>Dept</th><th>Amount</th><th>Gateway</th><th>Method</th><th>Status</th><th>Paid At</th></tr></thead>
            <tbody id="payments-body"></tbody>
          </table>
        </div>
        <div id="pay-total" style="font-family:var(--mono);font-size:11px;color:var(--muted);margin-top:10px;"></div>
      </div>

      <!-- Config -->
      <div class="tab" id="tab-config">
        <div class="page-header">
          <div>
            <div class="page-title">Config</div>
            <div class="page-sub">Merchant &amp; Kiosk payment credentials</div>
          </div>
        </div>

        <!-- Merchant Setup -->
        <div class="section">
          <div class="section-title">Merchant / Gateway Setup</div>
          <div class="form-row">
            <div class="field">
              <label>Gateway</label>
              <select id="cfg-gateway">
                <option value="razorpay">Razorpay</option>
                <option value="portone">PortOne</option>
                <option value="mock">Mock (testing)</option>
              </select>
            </div>
            <div class="field">
              <label>Merchant ID</label>
              <input id="cfg-mid" placeholder="rzp_live_…" />
            </div>
          </div>
          <div class="form-row">
            <div class="field">
              <label>Channel Key</label>
              <input id="cfg-chkey" placeholder="optional" />
            </div>
            <div class="field">
              <label>API Key / Secret</label>
              <input id="cfg-apikey" type="password" placeholder="stored obfuscated" />
            </div>
          </div>
          <div class="field">
            <label>Notes</label>
            <textarea id="cfg-notes" placeholder="optional notes…"></textarea>
          </div>
          <button class="btn btn-primary" onclick="saveMerchant()">Save Merchant Config</button>
        </div>

        <!-- Kiosk Razorpay Keys -->
        <div class="section">
          <div class="section-title">Kiosk Razorpay Keys <span style="color:var(--muted);font-size:11px">(super_admin only)</span></div>
          <div class="form-row">
            <div class="field">
              <label>Department</label>
              <select id="ksk-dept">
                <option value="global">global</option>
                <option value="electricity">electricity</option>
                <option value="water">water</option>
                <option value="municipal">municipal</option>
              </select>
            </div>
            <div class="field">
              <label>Mode</label>
              <select id="ksk-mode">
                <option value="test">test</option>
                <option value="live">live</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="field">
              <label>Razorpay Key ID</label>
              <input id="ksk-keyid" placeholder="rzp_test_…" />
            </div>
            <div class="field">
              <label>Razorpay Key Secret</label>
              <input id="ksk-secret" type="password" placeholder="stored encrypted" />
            </div>
          </div>
          <div style="display:flex;gap:10px;align-items:center;margin-top:4px">
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-family:var(--mono);font-size:12px;color:var(--muted)">
              <input id="ksk-active" type="checkbox" checked style="accent-color:var(--accent)" />
              Active
            </label>
          </div>
          <div style="margin-top:16px;display:flex;gap:10px">
            <button class="btn btn-primary" onclick="saveKioskConfig()">Save Kiosk Keys</button>
            <button class="btn btn-ghost" onclick="loadKioskConfigs()">Load Current</button>
          </div>
          <div id="kiosk-cfg-list" style="margin-top:16px"></div>
        </div>
      </div>

      <!-- Logs -->
      <div class="tab" id="tab-logs">
        <div class="page-header">
          <div>
            <div class="page-title">Logs</div>
            <div class="page-sub">Recent application log tail</div>
          </div>
          <div style="display:flex;gap:10px">
            <input id="log-lines" type="number" value="200" min="20" max="2000" style="background:var(--surface);border:1px solid var(--border2);color:var(--text);padding:7px 10px;border-radius:4px;font-family:var(--mono);font-size:12px;width:90px" />
            <button class="btn btn-ghost" onclick="loadLogs()">↺ Load</button>
          </div>
        </div>
        <div class="log-box" id="log-box">// click Load to fetch logs</div>
      </div>

    </main>
  </div>
</div>

<!-- Status-change modal (simple prompt replacement) -->
<div id="status-modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:200;align-items:center;justify-content:center">
  <div style="background:var(--surface);border:1px solid var(--border2);border-radius:8px;padding:28px;width:360px">
    <div style="font-family:var(--mono);font-size:14px;font-weight:600;margin-bottom:16px;color:var(--accent)">Update Request Status</div>
    <div class="field">
      <label>Request ID</label>
      <input id="sm-id" readonly style="opacity:.6" />
    </div>
    <div class="field">
      <label>New Status</label>
      <select id="sm-status">
        <option>PENDING</option><option>IN_PROGRESS</option>
        <option>DELIVERED</option><option>FAILED</option><option>CANCELLED</option>
      </select>
    </div>
    <div class="field">
      <label>Note (optional)</label>
      <input id="sm-note" placeholder="admin note…" />
    </div>
    <div style="display:flex;gap:10px;margin-top:4px">
      <button class="btn btn-primary" onclick="submitStatus()">Update</button>
      <button class="btn btn-ghost"   onclick="closeModal()">Cancel</button>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
let TOKEN = null;
let ADMIN_INFO = {};
let ALL_ROUTES = [];

// ── Auth ──────────────────────────────────────────────────────────────────────

async function doLogin() {
  const user = document.getElementById('l-user').value.trim();
  const pass = document.getElementById('l-pass').value;
  const btn  = document.getElementById('login-btn');
  const err  = document.getElementById('login-err');
  if (!user || !pass) { showErr(err, 'Enter username and password'); return; }
  err.style.display = 'none';
  btn.innerHTML = '<span class="spin"></span> Signing in…';
  btn.disabled = true;

  const fd = new FormData();
  fd.append('username', user);
  fd.append('password', pass);

  try {
    const r = await fetch('/admin/login', { method: 'POST', body: fd });
    const d = await r.json();
    if (!r.ok) { showErr(err, d.detail || 'Login failed'); btn.innerHTML = 'Sign in'; btn.disabled = false; return; }
    TOKEN = d.access_token;
    ADMIN_INFO = d;
    document.getElementById('h-role').textContent = d.role;
    document.getElementById('h-dept').textContent = d.department || 'all';
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('app-shell').classList.add('visible');
    loadHealth();
    buildRoutes();
  } catch(e) {
    showErr(err, 'Network error');
    btn.innerHTML = 'Sign in';
    btn.disabled = false;
  }
}

function doLogout() {
  TOKEN = null; ADMIN_INFO = {};
  document.getElementById('login-screen').style.display = 'flex';
  document.getElementById('app-shell').classList.remove('visible');
  document.getElementById('l-pass').value = '';
}

function showErr(el, msg) { el.textContent = msg; el.style.display = 'block'; }

// ── Navigation ────────────────────────────────────────────────────────────────

function nav(tab) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('tab-' + tab).classList.add('active');
  document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
  if (tab === 'requests') loadRequests();
  if (tab === 'payments') loadPayments();
  if (tab === 'logs')     {} // manual
}

// ── Auth fetch ────────────────────────────────────────────────────────────────

async function apiFetch(url, opts = {}) {
  const headers = { 'Authorization': 'Bearer ' + TOKEN, ...(opts.headers || {}) };
  const r = await fetch(url, { ...opts, headers });
  if (r.status === 401) { doLogout(); return null; }
  return r;
}

// ── Health ────────────────────────────────────────────────────────────────────

async function loadHealth() {
  try {
    const r = await fetch('/health');
    const d = await r.json();
    const sv = (id, val) => document.getElementById(id).textContent = val;
    const el = document.getElementById('hs-status');
    el.textContent = d.status;
    el.className = 'stat-value ' + (d.status === 'healthy' ? 'ok' : 'err');
    sv('hs-ts', d.timestamp ? d.timestamp.replace('T',' ').split('.')[0] : '—');
    const mock = document.getElementById('hs-mock');
    mock.textContent = d.mock_payment;
    mock.className = 'stat-value ' + (d.mock_payment === 'true' ? '' : 'ok');
    const dd = document.getElementById('hs-depts');
    dd.innerHTML = (d.departments || []).map(dep =>
      `<span class="pill pill-ok">${dep}</span>`
    ).join('');
  } catch(e) {
    document.getElementById('hs-status').textContent = 'unreachable';
    document.getElementById('hs-status').className = 'stat-value err';
  }
}

// ── Routes ────────────────────────────────────────────────────────────────────

async function buildRoutes() {
  try {
    const r = await fetch('/openapi.json');
    const d = await r.json();
    ALL_ROUTES = [];
    for (const [path, methods] of Object.entries(d.paths || {})) {
      for (const [method, info] of Object.entries(methods)) {
        ALL_ROUTES.push({ method: method.toUpperCase(), path, tags: (info.tags || []).join(', ') });
      }
    }
    renderRoutes(ALL_ROUTES);
  } catch(e) { console.warn('Could not load openapi.json', e); }
}

function renderRoutes(routes) {
  const body = document.getElementById('routes-body');
  if (!routes.length) { body.innerHTML = `<tr><td colspan="3" class="empty">no routes</td></tr>`; return; }
  body.innerHTML = routes.map(r => `
    <tr>
      <td><span class="pill pill-${r.method.toLowerCase()}">${r.method}</span></td>
      <td>${r.path}</td>
      <td style="color:var(--muted)">${r.tags}</td>
    </tr>`).join('');
}

function filterRoutes() {
  const q = document.getElementById('route-filter').value.toLowerCase();
  renderRoutes(ALL_ROUTES.filter(r => r.path.toLowerCase().includes(q) || r.method.toLowerCase().includes(q) || r.tags.toLowerCase().includes(q)));
}

// ── Requests ──────────────────────────────────────────────────────────────────

async function loadRequests() {
  const dept   = document.getElementById('req-dept').value;
  const status = document.getElementById('req-status').value;
  const limit  = document.getElementById('req-limit').value || 25;
  let url = `/admin/requests?limit=${limit}`;
  if (dept)   url += `&department=${dept}`;
  if (status) url += `&status=${status}`;

  const r = await apiFetch(url);
  if (!r) return;
  const d = await r.json();
  document.getElementById('req-total').textContent = `Showing ${(d.requests||[]).length} of ${d.total} total`;
  const body = document.getElementById('requests-body');
  if (!d.requests?.length) { body.innerHTML = `<tr><td colspan="5" class="empty">no requests</td></tr>`; return; }
  body.innerHTML = d.requests.map(req => `
    <tr>
      <td style="color:var(--muted)">${req.service_request_id || req.id || '—'}</td>
      <td>${req.department || '—'}</td>
      <td><span class="pill ${statusPill(req.status)}">${req.status || '—'}</span></td>
      <td>${fmtDate(req.created_at)}</td>
      <td><button class="btn btn-ghost" style="padding:4px 10px;font-size:11px"
          onclick="openModal('${req.service_request_id || req.id}','${req.status||''}')">Update</button></td>
    </tr>`).join('');
}

function statusPill(s) {
  if (!s) return '';
  const m = { PENDING:'pill-pend', IN_PROGRESS:'pill-pend', DELIVERED:'pill-ok', FAILED:'pill-fail', CANCELLED:'pill-fail' };
  return m[s] || '';
}

// ── Payments ──────────────────────────────────────────────────────────────────

async function loadPayments() {
  const dept   = document.getElementById('pay-dept').value;
  const status = document.getElementById('pay-status').value;
  const limit  = document.getElementById('pay-limit').value || 25;
  let url = `/admin/payments?limit=${limit}`;
  if (dept)   url += `&department=${dept}`;
  if (status) url += `&status=${status}`;

  const r = await apiFetch(url);
  if (!r) return;
  const d = await r.json();
  document.getElementById('pay-total').textContent = `Showing ${(d.payments||[]).length} of ${d.total} total`;
  const body = document.getElementById('payments-body');
  if (!d.payments?.length) { body.innerHTML = `<tr><td colspan="7" class="empty">no payments</td></tr>`; return; }
  body.innerHTML = d.payments.map(p => `
    <tr>
      <td style="color:var(--muted)">${p.id}</td>
      <td>${p.dept || '—'}</td>
      <td style="color:var(--accent)">₹${Number(p.amount).toFixed(2)}</td>
      <td>${p.gateway || '—'}</td>
      <td>${p.method || '—'}</td>
      <td><span class="pill ${payPill(p.status)}">${p.status || '—'}</span></td>
      <td style="color:var(--muted)">${fmtDate(p.paidAt || p.createdAt)}</td>
    </tr>`).join('');
}

function payPill(s) {
  if (!s) return '';
  const m = { captured:'pill-ok', success:'pill-ok', pending:'pill-pend', failed:'pill-fail', refunded:'pill-pend' };
  return m[s.toLowerCase()] || '';
}

// ── Status Modal ──────────────────────────────────────────────────────────────

function openModal(id, status) {
  document.getElementById('sm-id').value     = id;
  document.getElementById('sm-status').value = status;
  document.getElementById('sm-note').value   = '';
  document.getElementById('status-modal').style.display = 'flex';
}

function closeModal() { document.getElementById('status-modal').style.display = 'none'; }

async function submitStatus() {
  const id     = document.getElementById('sm-id').value;
  const status = document.getElementById('sm-status').value;
  const note   = document.getElementById('sm-note').value;
  const r = await apiFetch(`/admin/requests/${id}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status, note }),
  });
  closeModal();
  if (r && r.ok) { toast('Status updated', 'ok'); loadRequests(); }
  else           { toast('Update failed', 'err'); }
}

// ── Config ────────────────────────────────────────────────────────────────────

async function saveMerchant() {
  const body = {
    gateway:     document.getElementById('cfg-gateway').value,
    merchant_id: document.getElementById('cfg-mid').value.trim(),
    channel_key: document.getElementById('cfg-chkey').value.trim() || undefined,
    api_key:     document.getElementById('cfg-apikey').value || undefined,
    notes:       document.getElementById('cfg-notes').value.trim() || undefined,
  };
  if (!body.merchant_id) { toast('Merchant ID is required', 'err'); return; }
  const r = await apiFetch('/admin/merchant/setup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (r && r.ok) toast('Merchant config saved ✓', 'ok');
  else           toast('Save failed', 'err');
}

async function saveKioskConfig() {
  const body = {
    department:          document.getElementById('ksk-dept').value,
    razorpay_mode:       document.getElementById('ksk-mode').value,
    razorpay_key_id:     document.getElementById('ksk-keyid').value.trim() || undefined,
    razorpay_key_secret: document.getElementById('ksk-secret').value || undefined,
    is_active:           document.getElementById('ksk-active').checked,
  };
  const r = await apiFetch('/admin/kiosk-config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (r && r.ok) { toast('Kiosk config saved ✓', 'ok'); loadKioskConfigs(); }
  else           { const d = r ? await r.json() : {}; toast(d.detail || 'Save failed', 'err'); }
}

async function loadKioskConfigs() {
  const r = await apiFetch('/admin/kiosk-config');
  if (!r || !r.ok) { toast('Could not load (super_admin required)', 'err'); return; }
  const d = await r.json();
  const el = document.getElementById('kiosk-cfg-list');
  if (!d.configs?.length) { el.innerHTML = '<div style="color:var(--muted);font-family:var(--mono);font-size:12px">No configs yet.</div>'; return; }
  el.innerHTML = `<div class="table-wrap"><table>
    <thead><tr><th>Dept</th><th>Key Hint</th><th>Mode</th><th>Active</th><th>Updated</th></tr></thead>
    <tbody>${d.configs.map(c => `
      <tr>
        <td>${c.department}</td>
        <td style="color:var(--muted)">${c.razorpay_key_id_hint || '—'}</td>
        <td><span class="pill ${c.razorpay_mode==='live'?'pill-ok':'pill-pend'}">${c.razorpay_mode||'—'}</span></td>
        <td><span class="pill ${c.is_active?'pill-ok':'pill-fail'}">${c.is_active?'yes':'no'}</span></td>
        <td style="color:var(--muted)">${fmtDate(c.configured_at)}</td>
      </tr>`).join('')}
    </tbody></table></div>`;
}

// ── Logs ──────────────────────────────────────────────────────────────────────

async function loadLogs() {
  const lines = parseInt(document.getElementById('log-lines').value) || 200;
  const box   = document.getElementById('log-box');
  box.textContent = '// loading…';
  const r = await apiFetch(`/admin/logs?lines=${lines}`);
  if (!r) return;
  if (!r.ok) { box.textContent = '// log endpoint not available (404) — check server log path'; return; }
  const d = await r.json();
  const raw = (d.lines || []).join('\\n');
  box.innerHTML = (d.lines || []).map(line => {
    const l = line.replace(/</g,'&lt;');
    if (/error|exception|traceback/i.test(l)) return `<span class="log-err">${l}</span>`;
    if (/warning|warn/i.test(l))              return `<span class="log-warn">${l}</span>`;
    if (/info/i.test(l))                      return `<span class="log-info">${l}</span>`;
    if (/started|healthy|ok|success/i.test(l))return `<span class="log-ok">${l}</span>`;
    return l;
  }).join('\\n');
  box.scrollTop = box.scrollHeight;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmtDate(s) {
  if (!s) return '—';
  try { return new Date(s).toLocaleString('en-IN', { dateStyle:'short', timeStyle:'short' }); }
  catch { return s; }
}

function toast(msg, type='ok') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `toast ${type} show`;
  setTimeout(() => el.classList.remove('show'), 3000);
}

// Close modal on backdrop click
document.getElementById('status-modal').addEventListener('click', function(e) {
  if (e.target === this) closeModal();
});
</script>
</body>
</html>"""


# ─── Log tail endpoint ────────────────────────────────────────────────────────

_LOG_PATH = os.getenv("LOG_FILE", "logs/koisk_api.log")


def _get_log_router():
    from fastapi import APIRouter
    from fastapi.responses import JSONResponse

    r = APIRouter()

    @r.get("/admin/logs", include_in_schema=False)
    async def admin_logs(lines: int = 200):
        try:
            with open(_LOG_PATH, "r", errors="replace") as f:
                all_lines = f.readlines()
            tail = [l.rstrip() for l in all_lines[-lines:]]
            return {"lines": tail, "total": len(all_lines), "path": _LOG_PATH}
        except FileNotFoundError:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"Log file not found: {_LOG_PATH}")

    return r


# ─── Mount function ───────────────────────────────────────────────────────────

def mount_admin_ui(app: FastAPI) -> None:
    """
    Call this at the bottom of main.py after all routers are included:

        from src.api.admin.ui import mount_admin_ui
        mount_admin_ui(app)
    """
    app.add_middleware(LocalhostOnlyMiddleware)

    @app.get("/admin", response_class=HTMLResponse, include_in_schema=False)
    async def admin_ui():
        return HTMLResponse(content=_HTML)

    app.include_router(_get_log_router())
