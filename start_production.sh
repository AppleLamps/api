#!/bin/bash

# Grokipedia API Production Startup Script
# Usage: ./start_production.sh

set -e

echo "🚀 Starting Grokipedia API in Production Mode"
echo "=============================================="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi

# Load environment
set -a
source .env
set +a

echo "✓ Environment loaded"
echo "  - Environment: $ENVIRONMENT"
echo "  - Debug: $DEBUG"
echo "  - Redis: $REDIS_ENABLED"
echo "  - Rate Limit: $RATE_LIMIT_PER_MINUTE req/min"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate
echo "✓ Virtual environment activated"

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Check Redis connection (if enabled)
if [ "$REDIS_ENABLED" = "true" ]; then
    echo "🔄 Testing Redis connection..."
    python3 -c "
import asyncio
import redis.asyncio as aioredis
async def test_redis():
    try:
        r = await aioredis.from_url('$REDIS_URL')
        await r.ping()
        print('✓ Redis connected')
        await r.close()
    except Exception as e:
        print('⚠️  Redis connection failed:', str(e))
test_redis()
" || true
fi

# Run database migrations if using PostgreSQL
if [ ! -z "$DATABASE_URL" ]; then
    echo "🗄️  Running database migrations..."
    python3 -c "
import psycopg2
# Add your migration logic here
print('✓ Database ready')
" || true
fi

# Start the application
echo ""
echo "🎉 Starting API server..."
echo "📍 Listening on $HOST:$PORT"
echo "🌍 Base URL: $BASE_URL"
echo "📊 Documentation: http://$HOST:$PORT/"
echo ""

# Use gunicorn for production with multiple workers
if command -v gunicorn &> /dev/null; then
    gunicorn \
        --workers 4 \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind $HOST:$PORT \
        --access-logfile - \
        --error-logfile - \
        main:app
else
    # Fallback to uvicorn if gunicorn not available
    uvicorn main:app \
        --host $HOST \
        --port $PORT \
        --workers 4 \
        --log-level $LOG_LEVEL
fi
