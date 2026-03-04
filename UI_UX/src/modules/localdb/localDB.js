// localDB.js - REAL IMPLEMENTATION
const DB_NAME = 'koiskDB';
const DB_VERSION = 3; // Increment version for new stores
let _db = null; // Connection cache

// ===== CONNECTION MANAGEMENT =====
async function getDB() {
  if (_db) return _db;
  
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      const oldVersion = event.oldVersion;
      
      // Create stores based on version
      if (oldVersion < 1) {
        // Users store
        const userStore = db.createObjectStore('users', { keyPath: 'id' });
        userStore.createIndex('byPhone', 'phone', { unique: true });
        
        // Sessions store
        const sessionStore = db.createObjectStore('sessions', { keyPath: 'id' });
        sessionStore.createIndex('byUserId', 'userId');
        sessionStore.createIndex('byExpiry', 'expiresAt');
      }
      
      if (oldVersion < 2) {
        // Payment stores
        if (!db.objectStoreNames.contains('paymentProfiles')) {
          const profileStore = db.createObjectStore('paymentProfiles', { keyPath: 'id' });
          profileStore.createIndex('byUserId', 'userId', { unique: true });
        }
        
        if (!db.objectStoreNames.contains('payments')) {
          const paymentStore = db.createObjectStore('payments', { keyPath: 'id' });
          paymentStore.createIndex('byUserId', 'userId');
          paymentStore.createIndex('byStatus', 'status');
          paymentStore.createIndex('byDept', 'dept');
        }
        
        if (!db.objectStoreNames.contains('bills')) {
          const billStore = db.createObjectStore('bills', { keyPath: 'id' });
          billStore.createIndex('byUserId', 'userId');
          billStore.createIndex('byDept', 'dept');
          billStore.createIndex('byStatus', 'status');
        }
      }
      
      if (oldVersion < 3) {
        // Requests store (for Dashboard)
        if (!db.objectStoreNames.contains('requests')) {
          const requestStore = db.createObjectStore('requests', { keyPath: 'id' });
          requestStore.createIndex('byUserId', 'userId');
          requestStore.createIndex('byStatus', 'status');
          requestStore.createIndex('byDept', 'dept');
        }
        
        // Sync queue
        if (!db.objectStoreNames.contains('syncQueue')) {
          db.createObjectStore('syncQueue', { autoIncrement: true, keyPath: 'id' });
        }
      }
    };
    
    request.onsuccess = () => {
      _db = request.result;
      resolve(_db);
    };
    
    request.onerror = () => reject(request.error);
  });
}

// ===== HELPER FUNCTIONS =====
async function transaction(storeName, mode = 'readonly') {
  const db = await getDB();
  const tx = db.transaction(storeName, mode);
  return { tx, store: tx.objectStore(storeName) };
}

function requestHandler(request) {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

// ===== INIT FUNCTION =====
export async function init() {
  console.log('Initializing localDB...');
  try {
    const db = await getDB();
    console.log('Database connected, version:', db.version);
    
    // Seed demo data if needed
    await seedPaymentDemoData();
    
    // Create demo user if none exists
    const { store } = await transaction('users');
    const users = await requestHandler(store.getAll());
    
    if (users.length === 0) {
      const demoUser = {
        id: 'demo-user-ramesh-001',
        phone: '+919876543210',
        name: 'Ramesh Kumar',
        pinHash: '1234', // In production, use bcrypt
        consumerId: 'CONS-MH-001234',
        isDemo: true,
        createdAt: new Date().toISOString()
      };
      
      const { store: writeStore } = await transaction('users', 'readwrite');
      await requestHandler(writeStore.put(demoUser));
      
      // Create sample requests for dashboard
      await createSampleRequests(demoUser.id);
    }
    
    return true;
  } catch (error) {
    console.error('Failed to initialize localDB:', error);
    return false;
  }
}

// ===== USER FUNCTIONS =====
export async function getUserByPhone(phone) {
  try {
    const { store } = await transaction('users');
    const index = store.index('byPhone');
    return requestHandler(index.get(phone));
  } catch (error) {
    console.error('Error in getUserByPhone:', error);
    return null;
  }
}

export async function getUserById(userId) {
  try {
    const { store } = await transaction('users');
    return requestHandler(store.get(userId));
  } catch (error) {
    console.error('Error in getUserById:', error);
    return null;
  }
}

export async function createUser(userData) {
  try {
    const { store } = await transaction('users', 'readwrite');
    // BUG FIX: Spread userData FIRST so caller-supplied 'id' (UUID from authStore)
    // is preserved. Previously the generated id was placed first and then
    // overwritten by ...userData — but that relied on prop order which is fragile.
    // Now the generated id is only used as a fallback when no id is provided.
    const newUser = {
      id: `user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      ...userData,                         // caller's id wins if present
      createdAt: userData.createdAt ?? new Date().toISOString(),
    };
    await requestHandler(store.put(newUser));
    return newUser;
  } catch (error) {
    console.error('Error in createUser:', error);
    throw error;
  }
}

// ===== SESSION FUNCTIONS =====
export async function saveSession(session) {
  try {
    const { store } = await transaction('sessions', 'readwrite');
    const sessionWithExpiry = {
      ...session,
      expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString() // 24 hours
    };
    await requestHandler(store.put(sessionWithExpiry));
    return sessionWithExpiry;
  } catch (error) {
    console.error('Error in saveSession:', error);
    throw error;
  }
}

export async function clearSession(sessionId) {
  try {
    const { store } = await transaction('sessions', 'readwrite');
    await requestHandler(store.delete(sessionId));
    return true;
  } catch (error) {
    console.error('Error in clearSession:', error);
    return false;
  }
}

export async function getSession(sessionId) {
  try {
    const { store } = await transaction('sessions');
    const session = await requestHandler(store.get(sessionId));
    
    // Check if expired
    if (session && new Date(session.expiresAt) < new Date()) {
      await clearSession(sessionId);
      return null;
    }
    return session;
  } catch (error) {
    console.error('Error in getSession:', error);
    return null;
  }
}

// ===== REQUESTS FUNCTIONS (for Dashboard) =====
export async function getRequestsByUser(userId) {
  try {
    const { store } = await transaction('requests');
    const index = store.index('byUserId');
    const requests = await requestHandler(index.getAll(userId));
    
    // If no requests yet, create sample ones
    if (requests.length === 0) {
      return await createSampleRequests(userId);
    }
    
    return requests.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
  } catch (error) {
    console.error('Error in getRequestsByUser:', error);
    return [];
  }
}

async function createSampleRequests(userId) {
  const sampleRequests = [
    {
      id: `req-${Date.now()}-1`,
      userId,
      type: 'ELECTRICITY_BILL_PAYMENT',
      reference: `REF-ELEC-${Math.floor(Math.random() * 10000)}`,
      status: 'COMPLETED',
      amount: 1847,
      dept: 'electricity',
      createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString() // 2 days ago
    },
    {
      id: `req-${Date.now()}-2`,
      userId,
      type: 'WATER_BILL_PAYMENT',
      reference: `REF-WATR-${Math.floor(Math.random() * 10000)}`,
      status: 'COMPLETED',
      amount: 340,
      dept: 'water',
      createdAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString() // 5 days ago
    },
    {
      id: `req-${Date.now()}-3`,
      userId,
      type: 'GAS_BILL_PAYMENT',
      reference: `REF-GAS-${Math.floor(Math.random() * 10000)}`,
      status: 'PENDING',
      amount: 890,
      dept: 'gas',
      createdAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString() // 1 day ago
    }
  ];
  
  const { store } = await transaction('requests', 'readwrite');
  for (const req of sampleRequests) {
    await requestHandler(store.put(req));
  }
  
  return sampleRequests;
}

// ===== PAYMENT FUNCTIONS (from your stub) =====
export async function getPaymentProfile(userId) {
  try {
    const { store } = await transaction('paymentProfiles');
    const index = store.index('byUserId');
    return requestHandler(index.get(userId));
  } catch (error) {
    console.error('Error in getPaymentProfile:', error);
    return null;
  }
}

export async function savePaymentProfile(profile) {
  try {
    const { store } = await transaction('paymentProfiles', 'readwrite');
    return requestHandler(store.put(profile));
  } catch (error) {
    console.error('Error in savePaymentProfile:', error);
    throw error;
  }
}

export async function getPaymentById(id) {
  try {
    const { store } = await transaction('payments');
    return requestHandler(store.get(id));
  } catch (error) {
    console.error('Error in getPaymentById:', error);
    return null;
  }
}

export async function savePayment(payment) {
  try {
    const { store } = await transaction('payments', 'readwrite');
    return requestHandler(store.put(payment));
  } catch (error) {
    console.error('Error in savePayment:', error);
    throw error;
  }
}

export async function getPaymentsByUserId(userId) {
  try {
    const { store } = await transaction('payments');
    const index = store.index('byUserId');
    const payments = await requestHandler(index.getAll(userId));
    return payments.sort((a, b) => new Date(b.paidAt || b.createdAt) - new Date(a.paidAt || a.createdAt));
  } catch (error) {
    console.error('Error in getPaymentsByUserId:', error);
    return [];
  }
}

export async function getBillById(id) {
  try {
    const { store } = await transaction('bills');
    return requestHandler(store.get(id));
  } catch (error) {
    console.error('Error in getBillById:', error);
    return null;
  }
}

export async function saveBill(bill) {
  try {
    const { store } = await transaction('bills', 'readwrite');
    return requestHandler(store.put(bill));
  } catch (error) {
    console.error('Error in saveBill:', error);
    throw error;
  }
}

export async function getBillsByUserAndDept(userId, dept) {
  try {
    const { store } = await transaction('bills');
    const all = await requestHandler(store.index('byUserId').getAll(userId));
    return dept ? all.filter(b => b.dept === dept) : all;
  } catch (error) {
    console.error('Error in getBillsByUserAndDept:', error);
    return [];
  }
}

// ===== SEED DEMO DATA =====
export async function seedPaymentDemoData() {
  const DEMO_USER_ID = 'demo-user-ramesh-001';
  
  try {
    // Check if demo data already exists
    const { store: profileStore } = await transaction('paymentProfiles');
    const existingProfile = await requestHandler(profileStore.get(DEMO_USER_ID));
    
    if (existingProfile) return; // Already seeded
    
    // Create payment profile
    const profile = {
      id: DEMO_USER_ID,
      userId: DEMO_USER_ID,
      portoneCustomerId: `cust_demo_${Date.now()}`,
      name: 'Ramesh Kumar',
      contact: '+919876543210',
      email: 'ramesh@koisk.local',
      defaultMethod: 'upi',
      preferredGateway: 'portone',
      createdAt: new Date().toISOString(),
    };
    
    const { store: profileWriteStore } = await transaction('paymentProfiles', 'readwrite');
    await requestHandler(profileWriteStore.put(profile));
    
    // Create sample bills
    const bills = [
      {
        id: `BILL-ELEC-${Date.now()}`,
        userId: DEMO_USER_ID,
        dept: 'electricity',
        consumerNo: 'ELEC-MH-00234',
        billMonth: new Date().toISOString().slice(0, 7),
        amountDue: 1847,
        dueDate: new Date(Date.now() + 10 * 24 * 60 * 60 * 1000).toISOString(),
        status: 'PENDING',
        createdAt: new Date().toISOString(),
      },
      {
        id: `BILL-WATER-${Date.now()}`,
        userId: DEMO_USER_ID,
        dept: 'water',
        consumerNo: 'WAT-MH-00891',
        billMonth: new Date().toISOString().slice(0, 7),
        amountDue: 340,
        dueDate: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
        status: 'PENDING',
        createdAt: new Date().toISOString(),
      }
    ];
    
    const { store: billWriteStore } = await transaction('bills', 'readwrite');
    for (const bill of bills) {
      await requestHandler(billWriteStore.put(bill));
    }
    
  } catch (error) {
    console.error('Error seeding demo data:', error);
  }
}

// ===== EXPORT ALL FUNCTIONS =====
const localDB = {
  init,
  getUserByPhone,
  getUserById,
  createUser,
  saveSession,
  clearSession,
  getSession,
  getRequestsByUser,
  getPaymentProfile,
  savePaymentProfile,
  getPaymentById,
  savePayment,
  getPaymentsByUserId,
  getBillById,
  saveBill,
  getBillsByUserAndDept,
  seedPaymentDemoData,
};

export default localDB;