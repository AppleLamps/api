# Grokipedia API - API Key Management Guide

## Overview

The Grokipedia API now includes a **database-backed API key authentication system** that allows you to:

- Generate API keys for different users/applications
- Track API key usage (last used timestamp)
- Set per-key rate limits (requests per minute)
- Revoke keys without restarting the API
- Manage all keys through admin endpoints or CLI

## Quick Start

### 1. Initialize the Database

**Option A: Using CLI**
```bash
python manage_keys.py init
```

**Option B: On API startup**
- Database tables are created automatically when the API starts
- Check logs for: `✓ Database initialized - API key tables ready`

### 2. Create Your First API Key

**Option A: Using CLI (Recommended)**
```bash
python manage_keys.py create "User Name" "user@example.com" --rate-limit 20 --notes "My app"
```

Output:
```
✓ API key created successfully

  User: User Name
  Email: user@example.com
  Rate Limit: 20 requests/minute
  Key: grok_aBcDefGhIjKlMnOpQrStUvWxYz1234567890
  
  ⚠️  Save this key - you won't be able to see it again!
  Use it as: curl -H 'X-API-Key: grok_...' https://your-api.com/health
```

**Option B: Using HTTP API**
```bash
curl -X POST "http://localhost:8000/admin/keys/create?admin_key=YOUR_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_name": "User Name",
    "user_email": "user@example.com",
    "rate_limit": 20,
    "notes": "My app"
  }'
```

### 3. Use the API Key

Include the API key in requests using the `X-API-Key` header:

```bash
curl -H "X-API-Key: grok_aBcDefGhIjKlMnOpQrStUvWxYz1234567890" \
  https://your-api.com/article/Joe_Biden
```

**Python Example:**
```python
import httpx

headers = {"X-API-Key": "grok_aBcDefGhIjKlMnOpQrStUvWxYz1234567890"}
response = httpx.get("https://your-api.com/article/Joe_Biden", headers=headers)
print(response.json())
```

**JavaScript Example:**
```javascript
const headers = {
  "X-API-Key": "grok_aBcDefGhIjKlMnOpQrStUvWxYz1234567890"
};

fetch("https://your-api.com/article/Joe_Biden", { headers })
  .then(r => r.json())
  .then(data => console.log(data));
```

---

## CLI Management

The `manage_keys.py` script provides a command-line interface for key management:

### Initialize Database
```bash
python manage_keys.py init
```

### Create New Key
```bash
python manage_keys.py create "John Doe" "john@example.com"
python manage_keys.py create "Jane Doe" "jane@example.com" --rate-limit 50 --notes "Premium account"
```

**Options:**
- `name`: User's name (required)
- `email`: User's email (required)
- `--rate-limit`: Requests per minute (default: 10, max: 100)
- `--notes`: Optional notes about this key

### List Keys
```bash
# List active keys only
python manage_keys.py list

# List all keys (including revoked)
python manage_keys.py list --all
```

Output:
```
ID                                   User                 Email                          Rate Limit   Active   Last Used           
-------------------------------------------------------
abc123def456ghijk...                 John Doe             john@example.com               20           True     2025-10-28 14:32:10
xyz789abc123def45...                 Jane Doe             jane@example.com               50           True     2025-10-28 13:45:22

Total: 2 keys
```

### View Key Details
```bash
python manage_keys.py info abc123def456ghijk
```

Output:
```
API Key Details:
  ID: abc123def456ghijk
  User: John Doe
  Email: john@example.com
  Rate Limit: 20 requests/minute
  Active: True
  Created: 2025-10-28 12:00:00 UTC
  Last Used: 2025-10-28 14:32:10 UTC
  Notes: My app
```

### Revoke Key
```bash
# Deactivate (keep in database, can be reactivated)
python manage_keys.py revoke abc123def456ghijk
```

### Delete Key
```bash
# Permanently delete from database
python manage_keys.py delete abc123def456ghijk
```

---

## HTTP API Endpoints

### 1. Create API Key
**Endpoint:** `POST /admin/keys/create`

**Required:** Admin key via `?admin_key=YOUR_ADMIN_KEY` query parameter

**Request Body:**
```json
{
  "user_name": "User Name",
  "user_email": "user@example.com",
  "rate_limit": 20,
  "notes": "Optional notes"
}
```

**Response (201 Created):**
```json
{
  "id": "abc123def456...",
  "key": "grok_aBcDefGhIjKlMnOpQrStUvWxYz...",
  "user_name": "User Name",
  "user_email": "user@example.com",
  "rate_limit": 20,
  "is_active": true,
  "created_at": "2025-10-28T12:00:00.000000",
  "last_used": null,
  "notes": "Optional notes"
}
```

### 2. List API Keys
**Endpoint:** `GET /admin/keys`

**Required:** Admin key via `?admin_key=YOUR_ADMIN_KEY` query parameter

**Query Parameters:**
- `admin_key` (required): Admin authentication key
- `active_only` (optional): `true` (default) or `false` - show active keys or all

**Response (200 OK):**
```json
[
  {
    "id": "abc123def456...",
    "user_name": "User Name",
    "user_email": "user@example.com",
    "rate_limit": 20,
    "is_active": true,
    "created_at": "2025-10-28T12:00:00.000000",
    "last_used": "2025-10-28T14:32:10.000000"
  }
]
```

### 3. Get Key Details
**Endpoint:** `GET /admin/keys/{key_id}`

**Required:** Admin key via `?admin_key=YOUR_ADMIN_KEY` query parameter

**Response (200 OK):**
```json
{
  "id": "abc123def456...",
  "user_name": "User Name",
  "user_email": "user@example.com",
  "rate_limit": 20,
  "is_active": true,
  "created_at": "2025-10-28T12:00:00.000000",
  "last_used": "2025-10-28T14:32:10.000000"
}
```

### 4. Revoke API Key
**Endpoint:** `DELETE /admin/keys/{key_id}`

**Required:** Admin key via `?admin_key=YOUR_ADMIN_KEY` query parameter

**Response (200 OK):**
```json
{
  "message": "API key revoked successfully",
  "key_id": "abc123def456..."
}
```

---

## Configuration

### Environment Variables

Add these to your `.env` file or Railway Variables:

```bash
# Enable API key authentication
API_KEY_AUTH_ENABLED=true

# Admin key for managing API keys (CHANGE IN PRODUCTION!)
ADMIN_KEY=your-super-secure-admin-key-here

# Database URL (SQLite, PostgreSQL, or MySQL)
# SQLite (development):
DATABASE_URL=sqlite:///./grokipedia_api.db

# PostgreSQL (production):
DATABASE_URL=postgresql://user:password@localhost:5432/grokipedia_api

# MySQL:
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/grokipedia_api
```

### Database Support

The system supports multiple databases:

**SQLite** (Default, Good for Development)
```
DATABASE_URL=sqlite:///./grokipedia_api.db
```

**PostgreSQL** (Recommended for Production)
```
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

**MySQL**
```
DATABASE_URL=mysql+pymysql://user:password@host:3306/dbname
```

---

## Railway Deployment

### 1. Add PostgreSQL Plugin
1. Go to your Railway project
2. Click "Add Service" → "Add Plugin" → Select "PostgreSQL"
3. Railway creates `DATABASE_URL` automatically ✓

### 2. Configure Environment Variables
In Railway dashboard, add to **Variables**:

```
API_KEY_AUTH_ENABLED=true
ADMIN_KEY=your-production-admin-key-change-this
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

Or use the Railway-generated variables:
```
API_KEY_AUTH_ENABLED=true
ADMIN_KEY=your-production-admin-key-change-this
DATABASE_URL=postgresql://${{Postgres.DATABASE_USER}}:${{Postgres.DATABASE_PASSWORD}}@${{Postgres.DATABASE_HOST}}:${{Postgres.DATABASE_PORT}}/${{Postgres.DATABASE_NAME}}
```

### 3. Deploy
```bash
git push railway
```

### 4. Create Initial Keys
You can use the CLI or HTTP API:

**Via CLI (if you have access to Railway shell):**
```bash
railway shell
python manage_keys.py create "User1" "user1@example.com" --rate-limit 20
```

**Via HTTP API:**
```bash
curl -X POST "https://your-railway-app.up.railway.app/admin/keys/create?admin_key=YOUR_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_name": "User1",
    "user_email": "user1@example.com",
    "rate_limit": 20
  }'
```

---

## Security Best Practices

### 1. Keep Admin Key Secure
- Store `ADMIN_KEY` in environment variables, never in code
- Use a strong, random string (minimum 32 characters recommended)
- Change it regularly in production
- Don't share it

### 2. API Key Format
- Keys start with `grok_` prefix for easy identification
- Uses cryptographically secure random tokens
- Keys are unique and indexed in database

### 3. Rate Limiting
- Each key has its own rate limit (requests per minute)
- Combined with IP-based rate limiting
- Monitor usage patterns for suspicious activity

### 4. Auditing
- `created_at`: When key was created
- `last_used`: Last API call timestamp (auto-updated)
- `is_active`: Soft-delete flag (revoke without losing history)

### 5. Key Rotation
- Regularly create new keys for users
- Revoke old keys after transition period
- Monitor `last_used` to identify unused keys

---

## Troubleshooting

### Database Connection Error
```
Error initializing database: could not translate host name "localhost" to address
```

**Solution:** Make sure `DATABASE_URL` is correct. For Railway, use the provided `${{Postgres.DATABASE_URL}}`

### Admin Key Not Working
```
403 Unauthorized: Invalid admin key
```

**Solution:** 
- Verify `ADMIN_KEY` matches what you set in environment variables
- Check for typos or extra spaces
- In development, default is set in `.env`

### API Key Not Recognized
```
403 Forbidden: Invalid API key
```

**Solution:**
- Verify key exists: `python manage_keys.py list`
- Check if key is active: `python manage_keys.py info {key_id}`
- Ensure header is correct: `X-API-Key: {key}`
- Check key spelling (case-sensitive)

### Rate Limit Exceeded
```
429 Too Many Requests: You have exceeded the rate limit
```

**Solution:**
- Check user's `rate_limit`: `python manage_keys.py info {key_id}`
- Increase rate limit: Delete key and create new one with higher limit
- Or wait for rate limit window to reset

---

## Database Schema

```sql
CREATE TABLE api_keys (
  id VARCHAR(36) PRIMARY KEY,
  key VARCHAR(255) UNIQUE NOT NULL,
  user_name VARCHAR(255) NOT NULL,
  user_email VARCHAR(255) NOT NULL,
  rate_limit INTEGER DEFAULT 10,
  is_active BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  last_used DATETIME,
  notes TEXT,
  
  INDEX idx_key (key),
  INDEX idx_active (is_active)
);
```

---

## API Key Lifecycle

```
CREATE KEY
  ↓ (stored in database with is_active=true)
  ↓
USE KEY IN API CALLS
  ↓ (last_used timestamp updated on each call)
  ↓
REVOKE KEY (when compromised or no longer needed)
  ↓ (set is_active=false, key no longer works)
  ↓
DELETE KEY (if you want to remove from database entirely)
  ↓ (key completely removed)
```

---

## Examples

### Example: Multi-User Setup

```bash
# Create keys for different users/apps
python manage_keys.py create "Mobile App" "mobile@mycompany.com" --rate-limit 50 --notes "iOS app"
python manage_keys.py create "Web Dashboard" "web@mycompany.com" --rate-limit 30 --notes "React web app"
python manage_keys.py create "Data Pipeline" "data@mycompany.com" --rate-limit 100 --notes "Daily batch jobs"

# List all keys
python manage_keys.py list

# Monitor usage
python manage_keys.py info <key_id_for_data_pipeline>
```

### Example: Key Rotation

```bash
# User's key is about to expire
python manage_keys.py info old_key_id

# Create new key for same user
NEW_KEY=$(python manage_keys.py create "User Name" "user@example.com" --rate-limit 20)

# Notify user to update their code
# After grace period, revoke old key
python manage_keys.py revoke old_key_id
```

### Example: Usage Monitoring

```bash
# Check which keys haven't been used in 30 days
python manage_keys.py list | grep "Never"  # Never used
python manage_keys.py list | grep -E "2025-09"  # Last used in Sept
```

---

## Support

For issues or questions:
1. Check logs: API logs show all key creation/usage
2. Verify `.env` variables: `API_KEY_AUTH_ENABLED=true`
3. Test manually: `python manage_keys.py list`
4. Check database: SQLite file at `grokipedia_api.db` or PostgreSQL connection
