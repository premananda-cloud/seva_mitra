# KOISK Database & OAuth2 Security Guide

Complete guide for PostgreSQL database setup and OAuth 2.0 authentication implementation.

## 📋 Table of Contents

- [Database Schema](#database-schema)
- [OAuth2 Implementation](#oauth2-implementation)
- [Setup Instructions](#setup-instructions)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

## 🗄️ Database Schema

### Overview

The database includes tables for:
- User management with OAuth2 support
- Service requests (utilities: electricity, water, gas)
- Meter/consumer records
- Payment history

### Database Diagram

```
Users
├── ServiceRequests (1 to many)
├── ElectricityMeters (1 to many)
├── WaterConsumers (1 to many)
├── GasConsumers (1 to many)
└── PaymentHistory (1 to many)
```

### Tables

#### 1. Users Table

Stores user account information with OAuth2 support.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(10),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    email_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    google_id VARCHAR(255) UNIQUE
);
```

**Fields:**
- `username` - Unique login identifier
- `email` - Unique email address
- `hashed_password` - bcrypt hashed password
- `is_active` - Account activation status
- `google_id` - Google OAuth ID (for Google login)

#### 2. ServiceRequests Table

Tracks all service requests across utilities.

```sql
CREATE TABLE service_requests (
    id SERIAL PRIMARY KEY,
    service_request_id VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    service_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'DRAFT',
    payload TEXT,
    correlation_id VARCHAR(100),
    error_code VARCHAR(50),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
```

**Status Values:**
- DRAFT - Initial state
- SUBMITTED - Sent to department
- ACKNOWLEDGED - Received by department
- PENDING - Being processed
- APPROVED - Approved by department
- IN_PROGRESS - Work in progress
- DELIVERED - Completed successfully
- FAILED - Failed processing
- CANCELLED - Cancelled by user

#### 3. ElectricityMeters Table

Electricity meter records.

```sql
CREATE TABLE electricity_meters (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    meter_number VARCHAR(50) UNIQUE NOT NULL,
    meter_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'ACTIVE',
    load_requirement FLOAT,
    monthly_bill FLOAT DEFAULT 0.0,
    outstanding_amount FLOAT DEFAULT 0.0,
    last_reading FLOAT,
    last_reading_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4. WaterConsumers Table

Water supply consumer records.

```sql
CREATE TABLE water_consumers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    consumer_number VARCHAR(50) UNIQUE NOT NULL,
    property_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'ACTIVE',
    monthly_bill FLOAT DEFAULT 0.0,
    outstanding_amount FLOAT DEFAULT 0.0,
    last_reading FLOAT,
    last_reading_date TIMESTAMP,
    usage_limit FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 5. GasConsumers Table

Gas supply consumer records.

```sql
CREATE TABLE gas_consumers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    consumer_number VARCHAR(50) UNIQUE NOT NULL,
    connection_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'ACTIVE',
    monthly_bill FLOAT DEFAULT 0.0,
    outstanding_amount FLOAT DEFAULT 0.0,
    last_reading FLOAT,
    last_reading_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 6. PaymentHistory Table

Payment transaction records.

```sql
CREATE TABLE payment_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    service_request_id INTEGER REFERENCES service_requests(id),
    service_type VARCHAR(50) NOT NULL,
    amount FLOAT NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'PENDING',
    transaction_id VARCHAR(100),
    reference_number VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
```

## 🔐 OAuth2 Implementation

### OAuth2 Password Flow (Resource Owner Password Credentials)

Used for login with username and password.

**Flow:**

```
Client                    Server
  |                         |
  |--[username, password]-->|
  |                         |
  |<--[access_token]--------|
  |   [refresh_token]       |
  |                         |
  |--[Authorization header]-|
  |   (with access_token)   |
  |                         |
  |<--[Protected Resource]--|
```

### Token Structure

**Access Token (JWT):**
```json
{
  "sub": "123",                          // User ID
  "username": "johndoe",                 // Username
  "exp": 1707024000,                     // Expiration time
  "iat": 1706937600                      // Issued at
}
```

**Refresh Token (JWT):**
```json
{
  "sub": "123",
  "username": "johndoe",
  "type": "refresh",
  "exp": 1707628800
}
```

### Security Features

1. **Password Hashing**
   - Algorithm: bcrypt
   - Cost factor: 12 (default from passlib)
   - Never stored in plaintext

2. **JWT Tokens**
   - Algorithm: HS256
   - Signed with SECRET_KEY
   - Includes expiration time

3. **Token Refresh**
   - Access token: 30 minutes (default)
   - Refresh token: 7 days (default)
   - Automatic refresh on 401 response

4. **HTTPS (Production)**
   - Always use HTTPS in production
   - Tokens transmitted securely

## 🚀 Setup Instructions

### Step 1: PostgreSQL Installation

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**macOS (Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**Windows:**
Download from https://www.postgresql.org/download/windows/

### Step 2: Create Database

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create user
CREATE USER koisk_user WITH PASSWORD 'koisk_password';

# Create database
CREATE DATABASE koisk_db OWNER koisk_user;

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE koisk_db TO koisk_user;

# Exit
\q
```

### Step 3: Initialize Tables

**Using Python Script:**

```bash
cd /path/to/project
python
```

```python
from src.database.database import init_db, engine
init_db()
exit()
```

**Or using CLI:**

```bash
python -c "from src.database.database import init_db, engine; init_db()"
```

### Step 4: Environment Configuration

Create `.env` in backend root:

```env
# Database
DATABASE_URL=postgresql://koisk_user:koisk_password@localhost:5432/koisk_db

# Security
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# Email (for verification)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_password
```

### Step 5: Update FastAPI

```python
# In your FastAPI app (koisk_api.py)

from fastapi import Depends
from src.database.database import get_db, init_db
from src.api.auth_routes import router as auth_router
from src.security.auth import get_current_user

# Initialize database
init_db()

# Include auth routes
app.include_router(auth_router)

# Example: Protected endpoint
@app.get("/api/v1/protected")
async def protected_route(current_user_id: int = Depends(get_current_user)):
    return {"user_id": current_user_id}
```

## 🔒 Security Best Practices

### 1. Password Security

✅ DO:
- Hash passwords with bcrypt
- Require minimum 8 characters
- Support special characters
- Implement rate limiting on login attempts

❌ DON'T:
- Store plaintext passwords
- Use weak hashing (MD5, SHA1)
- Allow weak passwords
- Log passwords

### 2. Token Security

✅ DO:
- Use HTTPS for all token transmission
- Set short expiration times (15-30 minutes)
- Implement refresh token rotation
- Store tokens securely (httpOnly cookies or secure storage)

❌ DON'T:
- Transmit tokens over HTTP
- Store tokens in localStorage (XSS vulnerable)
- Use extremely long expiration times
- Expose tokens in logs

### 3. Database Security

✅ DO:
- Use strong database passwords
- Enable SSL/TLS for database connections
- Regular backups
- Encrypt sensitive data

❌ DON'T:
- Use default credentials
- Store passwords in code
- Share database credentials
- Expose database to public internet

### 4. API Security

✅ DO:
- Use CORS properly
- Implement rate limiting
- Validate all input
- Use HTTPS in production

❌ DON'T:
- Allow all origins (CORS: *)
- Expose sensitive errors
- Trust user input
- Use HTTP in production

### 5. Session Security

✅ DO:
- Implement automatic logout
- Require re-authentication for sensitive operations
- Monitor for suspicious activity
- Implement CSRF protection

❌ DON'T:
- Store sessions in localStorage
- Allow unlimited session duration
- Skip authentication checks
- Ignore security headers

## 🐛 Troubleshooting

### Database Connection Issues

**Error:** `could not connect to server`

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Verify credentials
psql -U koisk_user -h localhost -d koisk_db

# Check connection string format
# postgresql://username:password@host:port/database
```

### Authentication Issues

**Error:** `Invalid authentication credentials`

```bash
# Verify JWT_SECRET in .env
# Verify user exists in database
psql -c "SELECT * FROM users WHERE username='johndoe';"

# Check token expiration
python -c "import jwt; print(jwt.decode('token', options={'verify_signature': False}))"
```

### CORS Issues

**Error:** `Access-Control-Allow-Origin` not set

```python
# Ensure CORS is properly configured
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Match frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Password Reset

**Reset user password:**

```bash
psql -U koisk_user -d koisk_db

UPDATE users 
SET hashed_password = crypt('newpassword', gen_salt('bf', 12))
WHERE username = 'johndoe';
```

## 📊 Database Backups

### Backup Database

```bash
pg_dump -U koisk_user -d koisk_db > backup.sql
```

### Restore Database

```bash
psql -U koisk_user -d koisk_db < backup.sql
```

### Automated Backups

Create backup script (`backup.sh`):

```bash
#!/bin/bash
BACKUP_DIR="/path/to/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="$BACKUP_DIR/koisk_db_$TIMESTAMP.sql"

pg_dump -U koisk_user -d koisk_db > "$FILENAME"
gzip "$FILENAME"

# Keep only last 30 days
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete
```

Schedule with cron:

```bash
# Run backup daily at 2 AM
0 2 * * * /path/to/backup.sh
```

## 📈 Monitoring

### Monitor Database

```sql
-- Check database size
SELECT datname, pg_size_pretty(pg_database_size(datname)) 
FROM pg_database;

-- Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables;

-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Check slow queries
SELECT query, mean_exec_time 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC;
```

### Monitor Authentication

```sql
-- Failed login attempts
SELECT user_id, COUNT(*) as attempts
FROM logs
WHERE event = 'login_failed'
GROUP BY user_id
ORDER BY attempts DESC;

-- Active sessions
SELECT user_id, COUNT(DISTINCT token) 
FROM sessions 
WHERE expires_at > NOW()
GROUP BY user_id;
```

---

**Database setup complete!** 🎉

For more information, visit:
- PostgreSQL Docs: https://www.postgresql.org/docs/
- OAuth2 Spec: https://oauth.net/2/
- JWT: https://jwt.io
