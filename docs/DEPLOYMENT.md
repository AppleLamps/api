# Grokipedia API - Deployment Guide

Complete guide for deploying the Grokipedia API to production.

## Quick Start (5 minutes)

### Step 1: Prepare Your Machine

```bash
# Clone the repository
git clone <your-repo-url>
cd api

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your settings
nano .env

# Key settings for production:
ENVIRONMENT=production
DEBUG=false
REDIS_ENABLED=true
REDIS_URL=redis://your-redis-host:6379
SENTRY_ENABLED=true
SENTRY_DSN=your-sentry-dsn
```

### Step 3: Test Locally

```bash
# Start the API
python main.py

# Test in another terminal
curl http://localhost:8000/health

# Try an article
curl http://localhost:8000/article/Joe_Biden
```

---

## Deployment Options

### Option 1: Railway (Easiest - Free Tier) ⭐ RECOMMENDED

**Pros**: 
- Auto-deploys from GitHub
- Free tier available
- Built-in Redis (auto-configured)
- HTTPS included
- No credit card needed
- Real-time logs

**Steps (5 minutes)**:

1. **Create Railway Account**
   ```
   Go to https://railway.app
   Sign up with GitHub
   ```

2. **Create New Project**
   ```
   Click "New Project"
   Select "Deploy from GitHub"
   Choose your grokipedia-api repo
   Railway auto-detects Python
   ```

3. **Add Redis Service**
   ```
   In your project canvas, click "+"
   Select "Add Service"
   Choose "Database" → "Redis"
   Railway creates Redis automatically
   ```

4. **Add Environment Variables**
   
   Railway auto-generates Redis variables. Go to your **project → Variables** and add:

   **Redis Configuration:**
   ```
   REDIS_URL=redis://${{REDISUSER}}:${{REDIS_PASSWORD}}@${{REDISHOST}}:${{REDISPORT}}
   REDIS_ENABLED=true
   REDIS_PASSWORD=${{REDIS_PASSWORD}}
   REDISHOST=${{RAILWAY_PRIVATE_DOMAIN}}
   REDISPORT=6379
   REDISUSER=default
   CACHE_TTL_SECONDS=3600
   ```

   **Application Configuration:**
   ```
   ENVIRONMENT=production
   DEBUG=false
   TIMEOUT=30
   RATE_LIMIT_ENABLED=true
   RATE_LIMIT_PER_MINUTE=10
   LOG_LEVEL=INFO
   ```

   **Optional (add later if needed):**
   ```
   SENTRY_ENABLED=false
   API_KEY_AUTH_ENABLED=false
   ```

5. **Deploy**
   ```bash
   # Option A: Automatic (recommended)
   # Just push to GitHub - Railway auto-deploys
   git push origin main
   
   # Option B: Manual
   # Click "Deploy" button in Railway dashboard
   ```

6. **Monitor Deployment**
   ```
   Watch logs in Railway dashboard
   Should see: "✓ Redis connected successfully"
   Should see: "✓ API started in production mode"
   ```

7. **Test Your API**
   ```bash
   # Get your Railway URL from dashboard
   curl https://your-app-name.up.railway.app/health
   
   # Should return:
   # {"status":"healthy","environment":"production","cache_enabled":true}
   ```

**Cost**: 
- Free tier or $5-20/month depending on usage
- Redis included

**Troubleshooting**:
- If deployment fails, check Railway logs
- If Redis won't connect, verify all `REDIS_*` variables are set
- If timeout, increase `TIMEOUT=60`

---

### Option 2: Render (Alternative - Free Tier)

**Pros**:
- Simple Git integration
- Free tier with 100 hours/month
- Built-in HTTPS
- Easy scaling

**Steps**:

1. **Create Render Account**
   - Go to https://render.com
   - Sign up

2. **Create Web Service**
   - Click "New+"
   - Select "Web Service"
   - Connect GitHub repository

3. **Configure Service**
   - **Name**: grokipedia-api
   - **Region**: Choose closest to you
   - **Branch**: main
   - **Runtime**: Python 3.11
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app`

4. **Add Environment Variables**
   - Paste all variables from `.env.example`
   - Set `ENVIRONMENT=production`

5. **Add Redis**
   - Create Redis instance separately
   - Link connection string as `REDIS_URL`

6. **Deploy**
   - Push to GitHub: automatic deployment

**Cost**: Free tier (with limitations) or $7-15/month Pro

---

### Option 3: Fly.io (Global Distribution)

**Pros**:
- Deploys to multiple regions
- Always-free tier available
- Great for global API

**Steps**:

1. **Install Fly CLI**
   ```bash
   curl https://fly.io/install.sh | sh
   ```

2. **Create Fly App**
   ```bash
   fly auth login
   fly launch
   ```

3. **Configure fly.toml**
   ```toml
   app = "grokipedia-api"
   
   [build]
   builder = "paacketo"
   
   [env]
   ENVIRONMENT = "production"
   DEBUG = "false"
   ```

4. **Set Secrets**
   ```bash
   fly secrets set SENTRY_DSN=your-dsn
   fly secrets set REDIS_URL=redis://...
   ```

5. **Deploy**
   ```bash
   fly deploy
   ```

**Cost**: Free tier or $3/month

---

### Option 4: AWS Lambda + API Gateway

**Pros**:
- Serverless (pay per request)
- Scales automatically
- Part of AWS free tier

**Note**: Requires more setup. Recommend other options for simplicity.

---

## Production Checklist

### Before Deployment

- [ ] All environment variables configured
- [ ] Redis instance created and tested
- [ ] Sentry DSN configured
- [ ] API key generated (if using auth)
- [ ] Rate limits adjusted for expected load
- [ ] Cache TTL set appropriately

### Deployment

- [ ] Code committed to main branch
- [ ] All tests passing locally
- [ ] No debug mode enabled
- [ ] HTTPS configured
- [ ] Logging configured
- [ ] Error tracking enabled

### Post-Deployment

- [ ] Health check returning 200
- [ ] Can fetch articles successfully
- [ ] Rate limiting working
- [ ] Logs appearing in monitoring
- [ ] Uptime monitoring configured
- [ ] Error alerts configured

---

## Monitoring & Logs

### Railway Logs
```bash
# View live logs
railway logs

# Filter by service
railway logs --service main
```

### Render Logs
- View in Render dashboard
- Real-time log streaming

### Sentry Monitoring
- Dashboard: https://sentry.io
- Track errors and performance
- Set up alerts for critical errors

### Uptime Monitoring

```bash
# UptimeRobot (Free)
# Monitor: https://yourdomain.com/health
# Interval: Every 5 minutes
# Alert on down
```

---

## Scaling

### If You're Getting Rate Limited

1. **Increase Rate Limit**
   ```
   RATE_LIMIT_PER_MINUTE=50
   ```

2. **Add More Servers**
   - Railway: Increase instance size
   - Render: Add web services
   - Fly: Scale with fly scale

3. **Improve Caching**
   ```
   CACHE_TTL_SECONDS=7200  # Increase to 2 hours
   ```

---

## Database Setup (Optional)

For caching articles in a database:

### PostgreSQL Setup

**On Railway**:
```bash
# Add PostgreSQL plugin
# Copy DATABASE_URL automatically
```

**Create Tables**:
```sql
CREATE TABLE cached_articles (
    slug VARCHAR PRIMARY KEY,
    content JSONB,
    cached_at TIMESTAMP,
    ttl INTEGER
);

CREATE INDEX idx_slug ON cached_articles(slug);
CREATE INDEX idx_cached_at ON cached_articles(cached_at);
```

---

## SSL/HTTPS

Most platforms include HTTPS automatically:
- Railway: ✓ Included
- Render: ✓ Included
- Fly.io: ✓ Included

For custom domains, enable auto-renewal.

---

## Cost Summary

| Service | Free Tier | Paid Tier | Recommendation |
|---------|-----------|-----------|-----------------|
| Railway | Project | $5+/mo | **Best** |
| Render | 100h/mo | $7+/mo | Great |
| Fly.io | Always-free | $3+/mo | Budget |
| AWS Lambda | 1M requests | $0.002/req | Complex |

---

## Troubleshooting

### API Won't Start

```bash
# Check for syntax errors
python -m py_compile main.py

# Run locally with verbose output
python main.py --verbose
```

### Redis Connection Failed

```bash
# Test Redis locally
redis-cli ping

# Check connection string format
# Should be: redis://host:port/database
```

### High Memory Usage

```bash
# Reduce cache TTL
CACHE_TTL_SECONDS=1800

# Reduce log retention
LOG_LEVEL=WARNING
```

### Slow Response Times

```bash
# Check Grokipedia availability
curl https://grokipedia.com/health

# Increase timeout
TIMEOUT=60

# Enable caching
REDIS_ENABLED=true
```

---

## Support

- **Documentation**: Read README.md
- **Issues**: Report on GitHub
- **Questions**: Email admin@yourdomain.com

---

**Happy Deploying! 🚀**
