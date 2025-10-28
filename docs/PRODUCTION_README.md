# Grokipedia API - Production Ready 🚀

An unofficial API for accessing Grokipedia content programmatically. Production-ready with rate limiting, caching, authentication, and comprehensive monitoring.

## What's Included

✅ **Rate Limiting** - Prevent abuse with configurable request limits
✅ **Redis Caching** - Reduce load with intelligent caching
✅ **API Authentication** - Optional API key protection
✅ **Error Tracking** - Sentry integration for monitoring
✅ **Logging** - Comprehensive request/error logging
✅ **CORS** - Configurable cross-origin support
✅ **Documentation** - Auto-generated API docs

## Quick Deploy (5 Min)

### Railway (Recommended)

```bash
# 1. Fork this repo on GitHub
# 2. Go to railway.app
# 3. Create new project → Connect GitHub → Select repo
# 4. Add Redis plugin
# 5. Set environment variables (copy from .env.example)
# 6. Deploy (auto-deploys on git push)
```

### Local Development

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env  # Edit settings

# Run
python main.py
```

## Configuration

All configuration via `.env` file:

```env
# Core
ENVIRONMENT=production
DEBUG=false

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=10

# Redis Caching
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379

# Monitoring
SENTRY_ENABLED=true
SENTRY_DSN=your-dsn

# API Keys (optional)
API_KEY_AUTH_ENABLED=false
API_SECRET_KEY=your-secret-key
```

## API Endpoints

| Endpoint | Rate Limit | Description |
|----------|-----------|-------------|
| `GET /health` | 10/min | Health check |
| `GET /article/{slug}` | 10/min | Get full article |
| `GET /article/{slug}/summary` | 10/min | Get summary |
| `GET /article/{slug}/section/{title}` | 10/min | Get specific section |
| `GET /search?q=query` | 10/min | Search articles |
| `GET /info` | 50/min | API information |

### Example Requests

```bash
# Health check
curl https://api.yourdomain.com/health

# Get article
curl https://api.yourdomain.com/article/Joe_Biden

# Get summary (faster)
curl https://api.yourdomain.com/article/Joe_Biden/summary

# Get section
curl https://api.yourdomain.com/article/Joe_Biden/section/Presidency

# With API key (if enabled)
curl -H "X-API-Key: your-key" https://api.yourdomain.com/article/Joe_Biden
```

## Deployment

### Step-by-Step

1. **Choose Platform** (Railway recommended)
   - Railway: <https://railway.app>
   - Render: <https://render.com>
   - Fly.io: <https://fly.io>

2. **Configure Environment**
   - Copy `.env.example` settings
   - Set `ENVIRONMENT=production`
   - Provide Redis URL
   - Add Sentry DSN (optional)

3. **Deploy**
   - Connect GitHub repo
   - Auto-deploys on push

4. **Monitor**
   - Check health: `GET /health`
   - View logs in dashboard
   - Setup uptime monitoring

### Full Deployment Guide

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## Features

### Rate Limiting

Prevents abuse with configurable per-minute limits:

```env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=10  # Requests per minute per IP
```

Returns `429 Too Many Requests` when exceeded.

### Caching

Redis caching reduces Grokipedia load:

```env
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379
CACHE_TTL_SECONDS=3600  # 1 hour cache
```

First request caches; subsequent requests use cache.

### Authentication (Optional)

Protect your API with API keys:

```env
API_KEY_AUTH_ENABLED=true
API_SECRET_KEY=your-super-secret-key
```

Clients must include header:

```
X-API-Key: your-super-secret-key
```

### Monitoring

Track errors and performance with Sentry:

```env
SENTRY_ENABLED=true
SENTRY_DSN=https://key@sentry.io/project
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### Logging

Comprehensive logging to files:

```env
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
LOG_FORMAT=json
```

## Production Checklist

Before going live:

- [ ] `.env` configured with production values
- [ ] Redis URL verified and tested
- [ ] Sentry DSN configured
- [ ] API keys generated (if using auth)
- [ ] Rate limits adjusted for expected load
- [ ] HTTPS enabled on deployment platform
- [ ] Uptime monitoring configured
- [ ] Error alerts configured
- [ ] Logs being collected
- [ ] Documentation reviewed

## Monitoring & Observability

### Health Checks

```bash
# Check API health
curl https://api.yourdomain.com/health

# Expected response:
{
  "status": "healthy",
  "environment": "production",
  "cache_enabled": true,
  "timestamp": "2025-10-28T..."
}
```

### Logs

Logs to stdout (captured by your platform):

```
2025-10-28 12:34:56 - main - INFO - GET /article/Joe_Biden - IP: 192.168.1.1
2025-10-28 12:34:57 - main - INFO - GET /article/Joe_Biden - Status: 200
```

### Metrics

Available at `/info` endpoint:

```json
{
  "rate_limit": {
    "enabled": true,
    "requests_per_minute": 10
  },
  "cache": {
    "enabled": true,
    "ttl_seconds": 3600
  }
}
```

## Scaling

### Increasing Capacity

1. **More requests?** Increase rate limit:

   ```env
   RATE_LIMIT_PER_MINUTE=50
   ```

2. **Slower responses?** Increase cache TTL:

   ```env
   CACHE_TTL_SECONDS=7200
   ```

3. **More servers?** Scale deployment:
   - Railway: Increase instance size
   - Render: Multiple web services
   - Fly.io: `fly scale vm`

### Load Testing

```bash
# Test with Apache Bench
ab -n 100 -c 10 https://api.yourdomain.com/health

# Test with wrk
wrk -t4 -c100 -d30s https://api.yourdomain.com/health
```

## Legal & Compliance

### ⚖️ Important

- **Not affiliated** with Grokipedia or xAI
- **Educational use** - data from public sources
- **Respect ToS** - follow Grokipedia's terms
- **Rate limits** - don't overload servers
- **Attribution** - credit Grokipedia in output

### Required Files

- [TERMS_OF_SERVICE.md](TERMS_OF_SERVICE.md) - Share with users
- [PRIVACY_POLICY.md](PRIVACY_POLICY.md) - Share with users

## Troubleshooting

### API Won't Start

```bash
# Check syntax
python -m py_compile main.py

# Test locally
python main.py
```

### Redis Connection Fails

```bash
# Verify URL format
REDIS_URL=redis://host:port/0

# Test connection
redis-cli -u redis://host:port ping
```

### High Memory Usage

```env
# Reduce cache retention
CACHE_TTL_SECONDS=1800

# Reduce log level
LOG_LEVEL=WARNING
```

### Slow Responses

```bash
# Check Grokipedia status
curl https://grokipedia.com/

# Increase timeout
TIMEOUT=60

# Verify Redis is running
redis-cli ping
```

## Support

- **Docs**: Read [README.md](README.md)
- **Deploy**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Issues**: Report on GitHub
- **Contact**: <admin@yourdomain.com>

## Files Overview

```
├── main.py                    # FastAPI application
├── requirements.txt           # Python dependencies
├── .env.example              # Configuration template
├── DEPLOYMENT.md             # Deployment guide
├── PRODUCTION_README.md      # This file
├── TERMS_OF_SERVICE.md       # ToS for users
├── PRIVACY_POLICY.md         # Privacy policy
├── start_production.sh       # Production startup script
├── example_usage.py          # Example code
├── test_api.py              # API tests
└── README.md                 # Full documentation
```

## Performance

Expected performance with caching enabled:

| Metric | Value |
|--------|-------|
| Cached Response | <50ms |
| First Request | 500-2000ms (depends on Grokipedia) |
| Cache Hit Rate | 80-90% (typical) |
| Memory Usage | ~50-200MB |
| CPU Usage | Low (idle), Medium (load) |

## Cost Estimates

| Platform | Free Tier | Starter | Notes |
|----------|-----------|---------|-------|
| Railway | Project | $5/mo | Recommended |
| Render | 100h/mo | $7/mo | Good alternative |
| Fly.io | Always-free | $3/mo | Budget option |

Total with Redis: Add $3-10/mo

## License

MIT License - Use freely with attribution.

---

**Ready to deploy? Start with [DEPLOYMENT.md](DEPLOYMENT.md)**

🚀 Happy API serving!
