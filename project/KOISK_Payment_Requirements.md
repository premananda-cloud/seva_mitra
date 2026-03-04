# KOISK Payment Module — Requirements & Build Specification
**Version:** 1.0  
**Date:** February 2026  
**Scope:** react_ui payment module only — API and database teams use this as the contract  
**Status:** Requirements confirmed — ready to build

---

## 0. How to Read This Document

This document is split into three independent sections so frontend, backend, and database teams can work in parallel without blocking each other.

- **Section 1** — React UI team builds this against mock/stub interfaces
- **Section 2** — Backend team builds this; their endpoints must match the contracts here exactly
- **Section 3** — Database team builds this; schema must match what Section 2 reads/writes

The **contract boundary** is the API endpoint list in Section 2.1. Frontend calls these URLs. Backend serves them. Neither team needs to know how the other side is implemented.

---

## 1. React UI — Payment Module

### 1.1 New Files to Create

All files live inside `react_ui/src/`

```
modules/payment/
  paymentService.js       ← talks to orchestrator (never to HTTP directly)
  gatewayAdapters.js      ← PortOne SDK + Razorpay SDK wrappers
  offlineQueue.js         ← manages offline payment queue in IndexedDB
  paymentStore.js         ← Zustand store for all payment UI state
  paymentUtils.js         ← validation, formatting, INR helpers
  constants.js            ← payment method codes, status strings, gateway names

components/payment/
  PaymentFlow.jsx         ← top-level orchestrator component (3-step wizard)
  PaymentMethodSelector.jsx ← choose gateway + method (UPI / Card / NetBanking)
  UPIInput.jsx            ← UPI ID entry with live format validation
  CardInput.jsx           ← card details — tokenised, raw numbers never stored
  ReceiptScreen.jsx       ← success screen + print support
  OfflineBanner.jsx       ← banner shown when network unavailable
```

---

### 1.2 Existing Files to Modify

| File | Change needed |
|------|--------------|
| `modules/localdb/localDB.js` | Increment `DB_VERSION` to `2`, add 3 new stores (see 1.5) |
| `modules/orchestrator/orchestrator.js` | Replace payment stub methods with real routing logic (see 1.7) |
| `modules/auth/authStore.js` | Add `email` field to user schema (required by PortOne) |
| `modules/auth/RegisterPage.jsx` | Add optional email field to registration form |
| `App.jsx` | Add `/payment` and `/receipt/:id` routes |

---

### 1.3 PortOne Customer Registration — Decision

**Approach: Silent first-payment registration (Option A)**

The citizen never sees a separate "set up payment profile" step. On their first payment attempt, the system automatically creates their PortOne customer profile in the background using data already in their KOISK account. The citizen only sees the payment screen.

**Field mapping — KOISK user → PortOne customer:**

| PortOne field | Source | Notes |
|--------------|--------|-------|
| `name` | `user.name` | Already collected at KOISK registration |
| `contact` | `+91` + `user.phone` | Prepend country code — phone is stored without it |
| `email` | `user.email` | **New field** — optional at KOISK registration, required for PortOne. If absent, generate placeholder: `{phone}@koisk.local` |
| `gstin` | Not collected | Omit — optional in PortOne |
| `notes` | `{ koisk_user_id: user.id, dept: dept }` | Trace back to KOISK record |

**When registration happens:**
1. Citizen initiates payment for the first time
2. `paymentService.js` checks `localDB` for stored `portoneCustomerId`
3. If not found → call `POST /api/v1/payments/customer/register` (backend creates PortOne customer)
4. Backend returns `portoneCustomerId`
5. Store `portoneCustomerId` in both:
   - `localDB` payments profile store (for offline/fast lookup)
   - PostgreSQL `payment_profiles` table via backend (for persistence)
6. Proceed to payment initiation with the customer ID

---

### 1.4 Payment Flow — Step by Step

The `PaymentFlow.jsx` component manages a 3-step wizard:

```
STEP 1: Bill Summary
  ┌─────────────────────────────┐
  │  ⚡ Electricity Bill        │
  │  Consumer: ELEC-MH-00234   │
  │  Period: February 2026     │
  │  Amount Due: ₹1,847        │
  │                             │
  │  [Continue to Payment →]   │
  └─────────────────────────────┘

STEP 2: Choose Payment Method
  ┌─────────────────────────────┐
  │  Pay via:                   │
  │  ○ PortOne (recommended)   │
  │  ○ Razorpay                │
  │                             │
  │  Method:                    │
  │  [UPI] [Credit Card]       │
  │  [Debit Card] [Net Banking]│
  │                             │
  │  → UPI selected:            │
  │    [ Enter UPI ID        ]  │
  │                             │
  │  [Pay ₹1,847 →]            │
  └─────────────────────────────┘

STEP 3: Processing → Receipt
  ┌─────────────────────────────┐
  │  ✅ Payment Successful      │
  │  Reference: PAY-ELEC-0047  │
  │  Amount: ₹1,847            │
  │  Method: UPI               │
  │  Time: 02 Mar 2026, 14:32  │
  │                             │
  │  [🖨️ Print Receipt]        │
  │  [← Back to Dashboard]     │
  └─────────────────────────────┘
```

**State machine inside PaymentFlow:**

```
IDLE → REGISTERING_CUSTOMER → INITIATING → AWAITING_INPUT 
     → PROCESSING → VERIFYING → SUCCESS | FAILED | OFFLINE_QUEUED
```

---

### 1.5 LocalDB — New Stores (DB_VERSION → 2)

Add these three stores in the `upgrade()` function of `localDB.js`:

#### Store: `paymentProfiles`
Holds the citizen's gateway customer IDs. One record per user.

```js
{
  id:                  string,  // same as user.id (UUID)
  userId:              string,  // FK → users.id
  portoneCustomerId:   string | null,  // returned by PortOne on registration
  razorpayCustomerId:  string | null,  // returned by Razorpay if used
  name:                string,  // copied from user.name at registration time
  contact:             string,  // +91XXXXXXXXXX format
  email:               string,  // used for PortOne registration
  defaultMethod:       'upi' | 'card' | 'netbanking' | null,
  preferredGateway:    'portone' | 'razorpay' | 'auto',
  createdAt:           ISO string,
  syncedToBackend:     boolean
}
```

Indexes: `byUserId` (unique)

#### Store: `payments`
History of completed payments. Also written here for offline-first display.

```js
{
  id:               string,   // UUID — generated frontend-side
  userId:           string,   // FK → users.id
  dept:             'electricity' | 'gas' | 'water',
  type:             'BILL_PAYMENT',
  billRef:          string,   // e.g. BILL-ELEC-202602
  amount:           number,   // in INR paise? No — store rupees as float
  currency:         'INR',
  gateway:          'portone' | 'razorpay' | 'mock',
  gatewayPaymentId: string | null,  // from gateway on success
  gatewayOrderId:   string | null,
  method:           'upi' | 'card' | 'netbanking',
  status:           'PENDING' | 'SUCCESS' | 'FAILED' | 'OFFLINE_QUEUED',
  referenceNo:      string,   // display reference e.g. PAY-ELEC-20260302-0047
  receiptData:      object,   // full receipt JSON for ReceiptScreen
  createdAt:        ISO string,
  paidAt:           ISO string | null,
  syncedToBackend:  boolean
}
```

Indexes: `byUserId`, `byStatus`, `byDept`

#### Store: `bills`
Pending bills shown on service home screens. Seeded for demo; fetched from backend in real mode.

```js
{
  id:           string,   // e.g. BILL-ELEC-202602
  userId:       string,
  dept:         'electricity' | 'gas' | 'water',
  consumerNo:   string,   // e.g. ELEC-MH-00234
  billMonth:    string,   // YYYY-MM
  amountDue:    number,
  dueDate:      ISO string,
  status:       'PENDING' | 'OVERDUE' | 'PAID',
  paidPaymentId: string | null,  // → payments.id when paid
  createdAt:    ISO string
}
```

Indexes: `byUserId`, `byDept`, `byStatus`

**Demo seed data to add** (in `_seedDemoData()`):

```js
// Bills
{ id: 'BILL-ELEC-202602', userId: DEMO_USER_ID, dept: 'electricity',
  consumerNo: 'ELEC-MH-00234', billMonth: '2026-02',
  amountDue: 1847, dueDate: '2026-03-10T00:00:00Z', status: 'PENDING' }

{ id: 'BILL-WATER-202602', userId: DEMO_USER_ID, dept: 'water',
  consumerNo: 'WAT-MH-00891', billMonth: '2026-02',
  amountDue: 340,  dueDate: '2026-03-05T00:00:00Z', status: 'PENDING' }

{ id: 'BILL-GAS-202602', userId: DEMO_USER_ID, dept: 'gas',
  consumerNo: 'GAS-MH-00156', billMonth: '2026-02',
  amountDue: 890,  dueDate: '2026-03-15T00:00:00Z', status: 'PENDING' }

// Payment profile for demo user (mock customer IDs)
{ id: DEMO_USER_ID, userId: DEMO_USER_ID,
  portoneCustomerId: 'cust_demo_portone_001',
  razorpayCustomerId: null,
  name: 'Ramesh Kumar', contact: '+919876543210', email: 'ramesh@koisk.local',
  defaultMethod: 'upi', preferredGateway: 'portone',
  createdAt: '2026-01-10T08:00:00Z', syncedToBackend: false }
```

---

### 1.6 Module: `paymentUtils.js`

Pure functions — no side effects, easy to unit test.

```
formatINR(amount)             → '₹1,847.00'
parseINR(string)              → 1847.00
validateUPIId(id)             → { valid: bool, error: string | null }
  Rules: format must be 'something@bankname'
         length 3–50 chars
         no spaces
validateCardNumber(num)       → { valid: bool, network: 'visa'|'mastercard'|'rupay'|null }
  Use Luhn algorithm — never send raw number to any store
validateExpiry(mm, yy)        → { valid: bool, error: string | null }
validateCVV(cvv, network)     → { valid: bool }  // 3 digits Visa/MC, 4 for Amex
maskCardNumber(num)           → '•••• •••• •••• 4242'
generateReferenceNo(dept)     → 'PAY-ELEC-20260302-0047'  // dept + date + counter
formatPhoneForGateway(phone)  → '+91' + phone  // prepend country code
getGatewayDisplayName(code)   → 'PortOne' | 'Razorpay'
isNetworkAvailable()          → boolean  // navigator.onLine
```

---

### 1.7 Module: `paymentService.js`

This is the only file in the payment module that touches the orchestrator. All components call `paymentService`, never the orchestrator directly.

**Interface:**

```js
// Check if user has a gateway customer profile
paymentService.getOrCreateCustomerProfile(userId)
  → Promise<{ portoneCustomerId, razorpayCustomerId, ... }>

// Fetch pending bills for a department
paymentService.getPendingBills(userId, dept)
  → Promise<Bill[]>
  // Mock mode: reads from localDB bills store
  // Real mode: GET /api/v1/{dept}/bills?userId=...

// Start a payment — returns order data from gateway
paymentService.initiatePayment({ userId, billId, amount, dept, method, gateway })
  → Promise<{ orderId, gatewayData, mode: 'mock'|'real' }>
  // Mock mode: generates fake orderId, no HTTP call
  // Real mode: POST /api/v1/payments/initiate

// Complete payment after gateway confirms on client side
paymentService.completePayment({ paymentId, orderId, gateway, gatewayPaymentId })
  → Promise<Receipt>
  // Mock mode: generates receipt, saves to localDB
  // Real mode: POST /api/v1/payments/complete

// Handle payment failure — queue offline if network issue
paymentService.handleFailure({ error, paymentData })
  → Promise<{ queued: boolean, message: string }>

// Get payment history for dashboard display
paymentService.getHistory(userId)
  → Promise<Payment[]>
  // Mock mode: reads localDB payments store
  // Real mode: GET /api/v1/payments/history/{userId}
```

**Routing logic inside paymentService:**

```
For every method:
  if orchestrator.isConnected():
    call orchestrator → HTTP → real backend
  else:
    call localDB directly OR mock simulation
    add to syncQueue if data needs to persist to backend later
```

---

### 1.8 Module: `gatewayAdapters.js`

Wraps the PortOne and Razorpay browser SDKs. This is the only file that imports gateway SDKs directly.

**PortOne adapter:**

```js
portoneAdapter = {
  // Load PortOne SDK script dynamically (avoid bundling)
  loadSDK()  → Promise<void>

  // Create customer on PortOne — called by paymentService on first payment
  registerCustomer({ name, contact, email, notes })
    → Promise<{ customerId: string }>
    // Calls POST /api/v1/payments/customer/register (backend proxies to PortOne)

  // Open PortOne payment UI
  openPayment({ orderId, customerId, amount, currency, method, prefill })
    → Promise<{ paymentId, status, method }>

  // Verify payment status
  verifyPayment(paymentId)
    → Promise<{ verified: boolean, status: string }>
}
```

**Razorpay adapter:**

```js
razorpayAdapter = {
  loadSDK()  → Promise<void>

  openPayment({ orderId, amount, currency, prefill, theme })
    → Promise<{ razorpay_payment_id, razorpay_order_id, razorpay_signature }>

  verifySignature({ orderId, paymentId, signature, secret })
    → boolean
}
```

**Key rule:** Neither adapter stores any raw card data. Card numbers are passed directly to the SDK's UI — they never appear in JavaScript variables, localStorage, or IndexedDB.

---

### 1.9 Module: `offlineQueue.js`

Manages payments that failed due to network loss.

```js
offlineQueue = {
  // Add failed payment to queue
  add(paymentData)  → Promise<{ queueId }>

  // Get all unsynced items
  getPending()  → Promise<QueueItem[]>

  // Mark item as successfully synced
  markSynced(queueId)  → Promise<void>

  // Mark item as permanently failed (retryCount > 3)
  markFailed(queueId, errorMessage)  → Promise<void>

  // Try to process all pending items (called when network returns)
  flush()  → Promise<{ synced: number, failed: number }>

  // Listen for network restoration and auto-flush
  watchNetwork()  → void  // registers window.addEventListener('online', flush)
}
```

**Queue item schema:**
```js
{
  id:          auto-increment,
  action:      'PAYMENT_INITIATE' | 'PAYMENT_COMPLETE' | 'CUSTOMER_REGISTER',
  payload:     object,   // full data needed to retry
  retryCount:  number,   // max 3 before marking FAILED
  status:      'PENDING' | 'SYNCED' | 'FAILED',
  createdAt:   ISO string,
  lastRetryAt: ISO string | null,
  errorLog:    string[]  // one entry per failed attempt
}
```

---

### 1.10 Module: `paymentStore.js` (Zustand)

Global UI state for the payment wizard. Only the PaymentFlow component family reads/writes this store.

```js
state = {
  // Current wizard step
  step: 'IDLE' | 'BILL_SUMMARY' | 'METHOD_SELECT' | 'INPUT' | 'PROCESSING' | 'SUCCESS' | 'FAILED',

  // Bill being paid
  activeBill: Bill | null,

  // Selected gateway and method
  selectedGateway: 'portone' | 'razorpay' | null,
  selectedMethod:  'upi' | 'card' | 'netbanking' | null,

  // Input values (in-memory only — never persisted)
  upiId:       string,
  cardData:    { number: string, expiry: string, cvv: string, name: string },
  // Note: cardData is cleared immediately after SDK call

  // Processing state
  loading:      boolean,
  error:        string | null,
  orderId:      string | null,

  // Completed payment
  receipt:      Receipt | null,

  // Offline state
  isOffline:    boolean,
  queuedCount:  number,

  // Actions
  setStep(step)
  setActiveBill(bill)
  setGateway(gateway)
  setMethod(method)
  setUpiId(id)
  setCardData(data)
  setLoading(bool)
  setError(msg)
  setReceipt(receipt)
  reset()           ← clears all state, called on logout and after receipt shown
  clearCardData()   ← called immediately after SDK payment call
}
```

---

### 1.11 Component: `PaymentFlow.jsx`

Top-level payment wizard. Reads from `paymentStore`, delegates rendering to sub-components.

**Props:**
```js
{
  billId:   string,   // which bill to pay — looked up from localDB
  dept:     'electricity' | 'gas' | 'water',
  onClose:  () => void  // called when citizen exits without paying
}
```

**Behaviour:**
- On mount: loads bill from `paymentService.getPendingBills()`, sets `activeBill` in store
- Renders correct sub-component based on `step` in store
- Shows `OfflineBanner` at top if `isOffline` is true — payment still allowed (queued)
- On success: navigates to `/receipt/:id`
- On back press at any step: confirms with citizen before discarding

---

### 1.12 Component: `PaymentMethodSelector.jsx`

Step 2 of the wizard.

**What it renders:**
- Gateway toggle: PortOne (default, recommended badge) | Razorpay
- Payment method tabs: UPI | Credit Card | Debit Card | Net Banking
- Conditionally renders `UPIInput` or `CardInput` or bank list based on selected method
- "Pay ₹X,XXX →" button — disabled until input is valid

---

### 1.13 Component: `UPIInput.jsx`

**What it renders:**
- Large touch-friendly input field for UPI ID
- Live validation as citizen types (format check via `paymentUtils.validateUPIId`)
- Green tick when format is valid
- Error message in red when invalid
- Common UPI app shortcuts (optional — GPay, PhonePe, Paytm icons that pre-fill `@okicici` etc.)

**Validation rules:**
- Must contain exactly one `@`
- Left part: 3–50 alphanumeric + dot + hyphen
- Right part (VPA handle): known bank handle OR any non-empty string
- No spaces anywhere

---

### 1.14 Component: `CardInput.jsx`

**What it renders:**
- Card number field — auto-formats as `XXXX XXXX XXXX XXXX`, detects Visa/Mastercard/RuPay
- Expiry field — auto-formats as `MM/YY`
- CVV field — masked input, 3-4 digits
- Name on card field
- Visual card preview showing masked number and detected network logo

**Security rules:**
- Raw card number is never stored in any variable after it leaves the input
- `paymentStore.cardData` holds it in-memory ONLY during the input step
- `clearCardData()` is called immediately after the SDK payment method is invoked
- CVV is never logged anywhere

---

### 1.15 Component: `ReceiptScreen.jsx`

**What it renders:**
- KOISK logo + "Payment Successful" header
- Reference number (large, prominent)
- Department icon + name
- Amount paid
- Payment method used
- Timestamp
- Consumer number
- Print button — triggers `window.print()`, receipt is styled with `@media print` CSS to hide navigation
- "Back to Dashboard" button — calls `paymentStore.reset()` then navigates

**Data source:** `paymentStore.receipt` — set by `paymentService.completePayment()`

---

### 1.16 Component: `OfflineBanner.jsx`

Shown at the top of `PaymentFlow` when `paymentStore.isOffline === true`.

```
┌─────────────────────────────────────────────────────┐
│ 📡 No internet connection                           │
│ Your payment will be queued and processed when      │
│ the connection is restored.    [X queued payments]  │
└─────────────────────────────────────────────────────┘
```

Auto-hides when `isOnline` becomes true.

---

### 1.17 Orchestrator Updates

In `orchestrator.js`, replace payment stub bodies:

```js
// Replace this stub:
onPaymentRequested(paymentData) {
  if (!this._backendConnected) { return { mode: 'mock' } }
  // TODO: POST ...
}

// With this routing:
async initiatePayment(payload) {
  if (!this._backendConnected) {
    return mockPaymentService.initiate(payload)     // ← mock simulation
  }
  return axios.post(`${this._backendBaseUrl}/api/v1/payments/initiate`, payload)
}

async registerCustomer(userData) {
  if (!this._backendConnected) {
    return { portoneCustomerId: `cust_mock_${Date.now()}` }  // ← mock ID
  }
  return axios.post(`${this._backendBaseUrl}/api/v1/payments/customer/register`, userData)
}

async completePayment(payload) {
  if (!this._backendConnected) {
    return mockPaymentService.complete(payload)
  }
  return axios.post(`${this._backendBaseUrl}/api/v1/payments/complete`, payload)
}
```

---

## 2. Backend API — Contract Specification

> This section is for the API team. The React UI will call exactly these endpoints with exactly these request shapes. Do not change field names without updating Section 1 simultaneously.

### 2.1 Endpoint List

| Method | Endpoint | Called by | Purpose |
|--------|----------|-----------|---------|
| POST | `/api/v1/payments/customer/register` | `gatewayAdapters.portoneAdapter.registerCustomer()` | Create PortOne customer, store ID |
| POST | `/api/v1/payments/initiate` | `orchestrator.initiatePayment()` | Create gateway order |
| POST | `/api/v1/payments/complete` | `orchestrator.completePayment()` | Verify + record completed payment |
| POST | `/api/v1/payments/webhook` | PortOne / Razorpay servers directly | Server-side payment confirmation |
| GET  | `/api/v1/payments/history/{userId}` | `paymentService.getHistory()` | Payment history for dashboard |
| GET  | `/api/v1/payments/status/{paymentId}` | `paymentService.verifyPayment()` | Poll payment status |

---

### 2.2 `POST /api/v1/payments/customer/register`

**Request:**
```json
{
  "userId":  "uuid-of-koisk-user",
  "name":    "Ramesh Kumar",
  "contact": "+919876543210",
  "email":   "ramesh@koisk.local",
  "notes":   { "koisk_user_id": "uuid", "dept": "electricity" }
}
```

**Response 200:**
```json
{
  "success": true,
  "portoneCustomerId": "cust_portone_abc123",
  "razorpayCustomerId": null
}
```

**Behaviour:**
- Check PostgreSQL `payment_profiles` table — if customer already registered, return existing IDs (idempotent)
- If new: call PortOne `/v2/customers` API with the request body
- Store returned `portoneCustomerId` in `payment_profiles` linked to `userId`
- Never expose API keys to frontend

---

### 2.3 `POST /api/v1/payments/initiate`

**Request:**
```json
{
  "userId":     "uuid",
  "billId":     "BILL-ELEC-202602",
  "dept":       "electricity",
  "amount":     1847.00,
  "currency":   "INR",
  "gateway":    "portone",
  "method":     "upi",
  "customerId": "cust_portone_abc123"
}
```

**Response 200:**
```json
{
  "success":     true,
  "orderId":     "order_xyz789",
  "gateway":     "portone",
  "gatewayData": { ... },
  "expiresAt":   "2026-03-02T14:47:00Z"
}
```

**Behaviour:**
- Validate JWT in Authorization header
- Create order via PortOne or Razorpay depending on `gateway` field
- Insert row into `payments` table with `status = 'pending'`
- Return `orderId` and gateway-specific data needed by frontend SDK

---

### 2.4 `POST /api/v1/payments/complete`

**Request:**
```json
{
  "paymentId":       "internal-uuid",
  "orderId":         "order_xyz789",
  "gateway":         "portone",
  "gatewayPaymentId":"pay_portone_def456"
}
```

**Response 200:**
```json
{
  "success":     true,
  "status":      "SUCCESS",
  "receipt": {
    "referenceNo":  "PAY-ELEC-20260302-0047",
    "amount":       1847.00,
    "dept":         "electricity",
    "method":       "upi",
    "paidAt":       "2026-03-02T14:35:22Z",
    "consumerNo":   "ELEC-MH-00234"
  }
}
```

**Behaviour:**
- Verify payment with PortOne/Razorpay server-to-server (not trusting frontend)
- Update `payments` table: `status = 'paid'`, `paid_at = now()`
- Generate `referenceNo` using format `PAY-{DEPT}-{DATE}-{SEQ}`
- Return receipt — frontend displays this on `ReceiptScreen`

---

### 2.5 `POST /api/v1/payments/webhook`

**Behaviour:**
- Validate HMAC signature from gateway headers
- Update payment status in database regardless of frontend state
- Handle cases where `/complete` was never called (browser closed mid-payment)
- Return `{ "received": true }` — gateway expects HTTP 200 quickly

---

### 2.6 Response Envelope (all endpoints)

All payment endpoints return this structure:
```json
{
  "success":    true | false,
  "data":       { ... } | null,
  "message":    "Human readable string",
  "timestamp":  "ISO 8601 UTC"
}
```

On error:
```json
{
  "success":    false,
  "error_code": "PAYMENT_FAILED" | "GATEWAY_ERROR" | "INSUFFICIENT_FUNDS" | ...,
  "message":    "Payment could not be processed. Please try again.",
  "timestamp":  "ISO 8601 UTC"
}
```

---

## 3. Database — Schema Additions

> This section is for the database team. Add these to `database/init.sql` and `database/models.py`.

### 3.1 New Tables

#### `payment_profiles`
```sql
CREATE TABLE payment_profiles (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    portone_customer_id  VARCHAR(200) UNIQUE,
    razorpay_customer_id VARCHAR(200),
    name                 VARCHAR(200) NOT NULL,
    contact              VARCHAR(20)  NOT NULL,  -- +91XXXXXXXXXX
    email                VARCHAR(200),
    default_method       VARCHAR(50),            -- upi | card | netbanking
    preferred_gateway    VARCHAR(50) DEFAULT 'portone',
    is_default           BOOLEAN DEFAULT TRUE,
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_pp_user_id ON payment_profiles(user_id);
CREATE INDEX idx_pp_portone ON payment_profiles(portone_customer_id);
```

#### `payments`
```sql
CREATE TABLE payments (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              UUID NOT NULL REFERENCES users(id),
    bill_id              VARCHAR(100) NOT NULL,
    department           VARCHAR(50)  NOT NULL,  -- electricity | gas | water
    amount               DECIMAL(10,2) NOT NULL,
    currency             VARCHAR(3) DEFAULT 'INR',

    gateway              VARCHAR(50)  NOT NULL,  -- portone | razorpay | mock
    gateway_payment_id   VARCHAR(200),
    gateway_order_id     VARCHAR(200),
    gateway_status       VARCHAR(50),

    payment_method       VARCHAR(50),            -- upi | card | netbanking
    consumer_number      VARCHAR(100),
    billing_period       VARCHAR(20),            -- YYYY-MM

    reference_no         VARCHAR(100) UNIQUE,    -- PAY-ELEC-20260302-0047
    status               VARCHAR(50) NOT NULL DEFAULT 'pending',
    error_message        TEXT,

    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at              TIMESTAMP,

    metadata             JSONB DEFAULT '{}'
);
CREATE INDEX idx_pay_user_id    ON payments(user_id);
CREATE INDEX idx_pay_status     ON payments(status);
CREATE INDEX idx_pay_created_at ON payments(created_at DESC);
CREATE INDEX idx_pay_dept       ON payments(department);
```

#### `refunds`
```sql
CREATE TABLE refunds (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id        UUID NOT NULL REFERENCES payments(id),
    amount            DECIMAL(10,2) NOT NULL,
    reason            TEXT,
    gateway_refund_id VARCHAR(200),
    status            VARCHAR(50) DEFAULT 'pending',
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_refunds_payment_id ON refunds(payment_id);
```

### 3.2 Modify Existing Table

```sql
-- Add to existing users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(200);
ALTER TABLE users ADD COLUMN IF NOT EXISTS portone_customer_id VARCHAR(200);
```

### 3.3 Status Values (use these exact strings — frontend checks them)

**payments.status:**
```
pending          → order created, payment not yet confirmed
paid             → confirmed successful
failed           → gateway returned failure
refunded         → refund processed
offline_queued   → no network, sitting in sync queue
```

---

## 4. Contracts — What Must Match Exactly

These are the field names that cross the frontend/backend boundary. Changing either side without updating the other will break the integration. Treat this table as frozen until both teams agree to change it.

| Frontend sends | Backend expects | Type |
|---------------|----------------|------|
| `userId` | `user_id` | UUID string |
| `billId` | `bill_id` | string |
| `dept` | `department` | `'electricity' \| 'gas' \| 'water'` |
| `amount` | `amount` | float (rupees, not paise) |
| `gateway` | `gateway` | `'portone' \| 'razorpay'` |
| `method` | `payment_method` | `'upi' \| 'card' \| 'netbanking'` |
| `customerId` | `portone_customer_id` (in payment_profiles) | string |

> **Note on naming:** Frontend uses camelCase. Backend uses snake_case. The backend must accept camelCase in request body OR the frontend paymentService must translate before sending. Recommended: backend accepts camelCase via Pydantic alias, returns snake_case. Frontend paymentService normalises response to camelCase before giving to components.

---

## 5. Mock Mode — Demo Behaviour

When backend is not connected (`orchestrator.isConnected() === false`), the payment module must still run a complete, convincing demo flow. No empty screens.

| Real action | Mock equivalent |
|------------|----------------|
| PortOne customer registration | Returns `cust_mock_{timestamp}` instantly |
| Create payment order | Returns `order_mock_{timestamp}` after 300ms |
| UPI payment processing | Shows QR → auto-confirms after **1.5 seconds** |
| Card payment processing | Shows spinner → auto-confirms after **1.8 seconds** |
| Receipt generation | Generates real-looking reference `PAY-ELEC-YYYYMMDD-NNNN` |
| Payment history | Reads from localDB — shows Ramesh Kumar's 4 seed records |
| Failure simulation | 1-in-20 chance of failure to demonstrate error handling |

Demo seed data in `localDB` provides the bills that appear on service screens. Without this seed data, the demo would show empty screens.

---

## 6. Build Order Recommendation

Build in this sequence to avoid blocking yourself:

```
1. paymentUtils.js          — pure functions, no dependencies, test immediately
2. localDB.js update        — add 3 stores + seed bills data
3. paymentStore.js          — Zustand store, no API needed
4. offlineQueue.js          — IndexedDB only, no network needed
5. Mock payment logic       — in orchestrator, enables full demo
6. ReceiptScreen.jsx        — needs paymentStore only
7. UPIInput.jsx             — needs paymentUtils only
8. CardInput.jsx            — needs paymentUtils only
9. PaymentMethodSelector.jsx— needs UPIInput + CardInput
10. PaymentFlow.jsx         — needs all above + paymentService
11. paymentService.js       — needs orchestrator + localDB
12. gatewayAdapters.js      — needs real backend keys (build last)
13. OfflineBanner.jsx       — needs offlineQueue
```

Items 1–10 can be fully built and demoed **without any backend**. Items 11–13 require the API team to have endpoints ready.

---

*End of document. Questions → review Section 4 contracts first before changing any field name.*
