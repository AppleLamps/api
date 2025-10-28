# API Key Management Implementation Guide

## What Was Implemented

A complete, production-ready API key management system for the Grokipedia API with the following features:

### ✅ Core Features
- **Database-backed authentication**: SQLAlchemy ORM with support for SQLite, PostgreSQL, and MySQL
- **API key generation**: Cryptographically secure random keys with `grok_` prefix
- **Per-key rate limiting**: Each API key has its own configurable rate limit
- **Usage tracking**: Automatic `last_used` timestamp updates on each request
- **Key management**: Create, list, revoke, and delete keys
- **Soft-delete capability**: Revoke keys without losing audit history
- **Admin authentication**: Separate admin key for key management operations

### ✅ Tools Provided
1. **CLI Management Tool** (`manage_keys.py`)
   - Database initialization
   - Key creation and listing
   - Key revocation and deletion
   - Usage monitoring

2. **HTTP API Endpoints** (4 new admin endpoints)
   - `POST /admin/keys/create` - Create new key
   - `GET /admin/keys` - List keys
   - `GET /admin/keys/{key_id}` - Get details
   - `DELETE /admin/keys/{key_id}` - Revoke key

3. **Comprehensive Test Suite** (`test_api_keys.py`)
   - Tests all CRUD operations
   - Tests authentication flow
   - Tests revocation behavior
   - Tests invalid key rejection

---

## Files Modified/Created

### New Files Created:
```
models.py                          - SQLAlchemy ORM models and database utilities
manage_keys.py                     - CLI tool for key management
test_api_keys.py                   - Comprehensive test suite
docs/API_KEYS.md                   - Complete user documentation
docs/API_KEYS_IMPLEMENTATION.md    - This file
```

### Files Modified:
```
main.py                 - Added database imports, API key verification, admin endpoints
requirements.txt        - Added sqlalchemy==2.0.23, psycopg2-binary==2.9.9
.env.example           - Added DATABASE_URL and ADMIN_KEY configuration
```

---

## Installation Steps

### 1. Update Dependencies
```bash
pip install -r requirements.txt
```

The following packages were added:
- `sqlalchemy==2.0.23` - ORM framework
- `psycopg2-binary==2.9.9` - PostgreSQL driver

### 2. Set Environment Variables

Create or update your `.env` file:

```bash
# Enable API key authentication
API_KEY_AUTH_ENABLED=true

# Admin key (CHANGE THIS IN PRODUCTION!)
ADMIN_KEY=your-super-secure-admin-key-here-at-least-32-chars

# Database URL
# Development (SQLite):
DATABASE_URL=sqlite:///./grokipedia_api.db

# Production (PostgreSQL):
DATABASE_URL=postgresql://user:password@host:5432/grokipedia_api
```

### 3. Initialize Database

**Option A: Automatic (on API startup)**
- Database tables are created automatically
- Check logs for: `✓ Database initialized - API key tables ready`

**Option B: Manual (CLI)**
```bash
python manage_keys.py init
```

### 4. Create First API Key

```bash
python manage_keys.py create "User Name" "user@example.com" --rate-limit 20
```

Output shows the generated API key.

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────┐
│         API Request (with X-API-Key header)     │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
         ┌─────────────────────────┐
         │  verify_api_key()       │
         │  (FastAPI dependency)   │
         └────────────┬────────────┘
                     │
                     ▼
         ┌─────────────────────────┐
         │  Query Database         │
         │  (SQLAlchemy)           │
         └────────────┬────────────┘
                     │
      ┌──────────────┴──────────────┐
      │                             │
      ▼                             ▼
  ✓ Valid Key              ✗ Invalid/Revoked
  is_active=true           HTTP 403 Forbidden
      │
      ▼
  ┌─────────────────────┐
  │ Process Request     │
  │ + Update last_used  │
  │ + Apply rate limit  │
  └─────────────────────┘
```

### Database Schema

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

## Usage Examples

### Local Development

1. **Create keys**:
```bash
python manage_keys.py create "Dev User" "dev@localhost" --rate-limit 100
python manage_keys.py create "Test Bot" "bot@localhost" --rate-limit 50
```

2. **List keys**:
```bash
python manage_keys.py list
```

3. **Test with curl**:
```bash
export API_KEY="grok_your_key_here"
curl -H "X-API-Key: $API_KEY" http://localhost:8000/health
curl -H "X-API-Key: $API_KEY" http://localhost:8000/article/Joe_Biden
```

### Production Deployment (Railway)

1. **Add PostgreSQL plugin** (Railway automatically provides DATABASE_URL)

2. **Set environment variables** in Railway dashboard:
```
API_KEY_AUTH_ENABLED=true
ADMIN_KEY=your-production-key
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

3. **Deploy**:
```bash
git push railway
```

4. **Create keys via HTTP API**:
```bash
curl -X POST "https://your-app.up.railway.app/admin/keys/create?admin_key=YOUR_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_name": "User1",
    "user_email": "user1@example.com",
    "rate_limit": 20
  }'
```

---

## Code Integration Points

### In `main.py`:

1. **Import models** (line 22):
```python
from models import init_db, get_api_key_record, update_api_key_usage, ...
```

2. **Initialize database on startup** (lines 106-119):
```python
@app.on_event("startup")
async def startup():
    init_db()  # Creates tables automatically
    ...
```

3. **Verify API keys** (lines 164-189):
```python
def verify_api_key(api_key: Optional[str] = Depends(API_KEY_HEADER)) -> Optional[str]:
    # Checks database for valid, active keys
    ...
```

4. **Admin endpoints** (lines ~730-850):
```python
@app.post("/admin/keys/create")
@app.get("/admin/keys")
@app.delete("/admin/keys/{key_id}")
@app.get("/admin/keys/{key_id}")
```

### In `models.py`:

Core database functions:
- `init_db()` - Initialize tables
- `create_api_key()` - Generate and store new key
- `get_api_key_record()` - Verify key
- `update_api_key_usage()` - Track usage
- `revoke_api_key()` - Soft-delete
- `get_all_api_keys()` - List keys

---

## Testing

### Run the Test Suite

```bash
python test_api_keys.py
```

Tests cover:
1. ✅ Creating API keys
2. ✅ Listing keys
3. ✅ Using keys for authentication
4. ✅ Rejecting invalid keys
5. ✅ Getting key details
6. ✅ Revoking keys
7. ✅ Rejecting revoked keys

### Manual Testing

**Test 1: Create and use a key**
```bash
# Create key
python manage_keys.py create "Test User" "test@example.com"

# Use it (replace with actual key)
curl -H "X-API-Key: grok_xxxx" http://localhost:8000/health

# Should return 200 OK
```

**Test 2: Invalid key rejection**
```bash
curl -H "X-API-Key: invalid_key" http://localhost:8000/health
# Should return 403 Forbidden
```

**Test 3: Revoked key rejection**
```bash
# Revoke key
python manage_keys.py revoke <key_id>

# Try to use it
curl -H "X-API-Key: grok_xxxx" http://localhost:8000/health
# Should return 403 Forbidden
```

---

## Configuration Reference

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `API_KEY_AUTH_ENABLED` | bool | `true` | Enable/disable authentication |
| `ADMIN_KEY` | string | (none) | Admin key for managing API keys |
| `DATABASE_URL` | string | `sqlite:///./grokipedia_api.db` | Database connection URL |
| `RATE_LIMIT_PER_MINUTE` | int | `10` | IP-based rate limit |

### Database URLs

**SQLite (Development)**
```
sqlite:///./grokipedia_api.db
```

**PostgreSQL (Production)**
```
postgresql://user:password@host:5432/dbname
```

**MySQL**
```
mysql+pymysql://user:password@host:3306/dbname
```

---

## Security Considerations

### 1. Admin Key
- Generate a strong, random string (minimum 32 characters)
- Store in environment variables, never in code
- Rotate regularly in production
- Don't expose in logs or error messages

### 2. API Keys
- Never log the full API key, only first 10 characters
- Keys are indexed for fast lookup
- Use HTTPS in production (Railway provides SSL)
- Implement key expiration if needed

### 3. Rate Limiting
- IP-based rate limiting (SlowAPI) still applies
- Per-key rate limiting adds additional layer
- Monitor for abuse patterns
- Log failed authentication attempts

### 4. Database
- PostgreSQL recommended for production
- Use strong database passwords
- Enable SSL for database connections
- Regular backups

---

## Monitoring & Maintenance

### Monitor Key Usage

```bash
# View all active keys
python manage_keys.py list

# Check specific key details
python manage_keys.py info <key_id>

# Check last used (useful for finding unused keys)
python manage_keys.py list | grep "Never"
```

### Audit Trail

The database maintains:
- `created_at`: When key was generated
- `last_used`: When key was last used for API call
- `is_active`: Whether key is still valid
- History of revocations

### Regular Maintenance

1. **Weekly**: Check for unused keys
```bash
python manage_keys.py list
```

2. **Monthly**: Review key activity
3. **Quarterly**: Rotate admin key
4. **As needed**: Revoke compromised keys

---

## Troubleshooting

### Issue: "Database initialization failed"

**Cause**: DATABASE_URL is incorrect or database is not accessible

**Solution**:
1. Verify DATABASE_URL is correct
2. Test database connection manually
3. For PostgreSQL: ensure psycopg2 is installed

```bash
pip install psycopg2-binary
```

### Issue: "Admin key not working"

**Cause**: ADMIN_KEY doesn't match or has typo

**Solution**:
1. Check .env file for exact value
2. Look for trailing spaces
3. Verify env vars loaded: add debug print

```python
print(f"ADMIN_KEY: {ADMIN_KEY}")  # Debug
```

### Issue: "403 Forbidden: Invalid API key"

**Cause**: 
- Key doesn't exist
- Key is revoked
- Wrong header name

**Solution**:
1. Verify key exists: `python manage_keys.py list`
2. Check if active: `python manage_keys.py info <key_id>`
3. Ensure header is `X-API-Key: ` (not `X-API-KEY:`)

### Issue: "Rate limit exceeded"

**Cause**: User hit per-key or IP-based rate limit

**Solution**:
1. Check key's rate_limit: `python manage_keys.py info <key_id>`
2. Create new key with higher limit if needed
3. Implement caching/queue in client code

---

## Next Steps

### Optional Enhancements

1. **Key Expiration**
   - Add `expires_at` field
   - Check in verification
   - Auto-revoke expired keys

2. **Usage Quotas**
   - Track total requests per key
   - Implement quota limits
   - Daily/monthly reset

3. **Scopes/Permissions**
   - Limit which endpoints each key can access
   - Different permission levels
   - Fine-grained access control

4. **Dashboard**
   - Web UI for key management
   - Visual usage analytics
   - Usage graphs

5. **Webhooks**
   - Notify users when quota near limit
   - Alert on unusual activity

---

## Files Summary

### `models.py` (87 lines)
Database models and utilities for API key management.

**Key Functions**:
- `init_db()` - Initialize tables
- `create_api_key()` - Create new key
- `get_api_key_record()` - Verify key
- `update_api_key_usage()` - Track usage
- `revoke_api_key()` - Revoke key

### `manage_keys.py` (180 lines)
CLI tool for API key management.

**Commands**:
- `python manage_keys.py init`
- `python manage_keys.py create <name> <email>`
- `python manage_keys.py list [--all]`
- `python manage_keys.py revoke <key_id>`
- `python manage_keys.py delete <key_id>`
- `python manage_keys.py info <key_id>`

### `test_api_keys.py` (280 lines)
Comprehensive test suite for API key system.

**Tests**:
- Key creation
- Key listing
- Authentication flow
- Invalid key rejection
- Key details retrieval
- Key revocation
- Revoked key rejection

### `docs/API_KEYS.md` (300+ lines)
Complete user-facing documentation with examples.

### `main.py` (modified)
- Added database initialization
- Added API key verification
- Added 4 new admin endpoints
- Added usage tracking

### `requirements.txt` (modified)
- Added SQLAlchemy
- Added psycopg2-binary

### `.env.example` (modified)
- Added DATABASE_URL
- Added ADMIN_KEY
- Updated API_KEY_AUTH_ENABLED

---

## Deployment Checklist

- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Set `API_KEY_AUTH_ENABLED=true` in environment
- [ ] Generate secure `ADMIN_KEY` (32+ chars)
- [ ] Configure `DATABASE_URL` (PostgreSQL for production)
- [ ] Initialize database: `python manage_keys.py init`
- [ ] Test: `python test_api_keys.py`
- [ ] Create first user key: `python manage_keys.py create ...`
- [ ] Deploy to Railway/Render/Fly.io
- [ ] Create keys for production users
- [ ] Monitor logs for authentication issues
- [ ] Document keys for team members

---

## Support

For issues:
1. Check logs: `API logs show authentication events`
2. Test database: `python manage_keys.py list`
3. Verify env vars: Print them in startup
4. Check database schema: `sqlite3 grokipedia_api.db ".schema"`
5. Review `docs/API_KEYS.md` troubleshooting section

