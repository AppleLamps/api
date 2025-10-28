from fastapi import FastAPI, HTTPException, Query, Request, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import httpx
from bs4 import BeautifulSoup
import re
from datetime import datetime
import asyncio
from urllib.parse import urljoin, quote
import logging
import os
from dotenv import load_dotenv
import sentry_sdk
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis.asyncio as aioredis
import json
from models import init_db, get_api_key_record, update_api_key_usage, create_api_key, revoke_api_key, get_all_api_keys, SessionLocal, APIKey

# Load environment variables
load_dotenv()

# Environment configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
BASE_URL = os.getenv("BASE_URL", "https://grokipedia.com")
TIMEOUT = float(os.getenv("TIMEOUT", "30"))

# Rate limiting
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))

# Redis cache
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "true").lower() == "true"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

# Authentication
API_KEY_AUTH_ENABLED = os.getenv("API_KEY_AUTH_ENABLED", "true").lower() == "true"
ADMIN_KEY = os.getenv("ADMIN_KEY", "")

# Sentry error tracking
SENTRY_ENABLED = os.getenv("SENTRY_ENABLED", "false").lower() == "true"
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
if SENTRY_ENABLED and SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=ENVIRONMENT,
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
    )

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# CORS configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", '["*"]')
try:
    cors_origins = json.loads(CORS_ORIGINS) if CORS_ORIGINS != "*" else ["*"]
except:
    cors_origins = ["*"]

app = FastAPI(
    title="Grokipedia API",
    description="Programmatic access to Grokipedia content for AI models and applications",
    version="1.0.0",
    docs_url="/" if os.getenv("DOCS_ENABLED", "true") == "true" else None,
    redoc_url="/redoc" if os.getenv("REDOC_ENABLED", "true") == "true" else None,
    debug=DEBUG
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "HEAD", "OPTIONS"],
    allow_headers=["*"],
)

# Global Redis client
redis_client: Optional[aioredis.Redis] = None

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    logger.info(f"{request.method} {request.url.path} - IP: {get_remote_address(request)}")
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} - Status: {response.status_code}")
    return response

# Startup event
@app.on_event("startup")
async def startup():
    """Initialize database and Redis connection on startup"""
    global redis_client
    
    # Initialize database
    try:
        init_db()
        logger.info("✓ Database initialized - API key tables ready")
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
    
    if REDIS_ENABLED:
        try:
            redis_client = await aioredis.from_url(REDIS_URL)
            await redis_client.ping()
            logger.info("✓ Redis connected successfully")
        except Exception as e:
            logger.warning(f"✗ Failed to connect to Redis: {e}")
            redis_client = None
    logger.info(f"✓ API started in {ENVIRONMENT} mode")

# Shutdown event
@app.on_event("shutdown")
async def shutdown():
    """Close Redis connection on shutdown"""
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("✓ Redis connection closed")

# API Key authentication
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: Optional[str] = Depends(API_KEY_HEADER)) -> Optional[str]:
    """Verify API key if authentication is enabled"""
    if not API_KEY_AUTH_ENABLED:
        return None
    
    if not api_key:
        raise HTTPException(
            status_code=403,
            detail="API key required. Use header: X-API-Key"
        )
    
    db = SessionLocal()
    try:
        key_record = get_api_key_record(db, api_key)
        if not key_record:
            logger.warning(f"Invalid API key attempt: {api_key[:10]}...")
            raise HTTPException(status_code=403, detail="Invalid API key")
        
        logger.info(f"Authenticated user: {key_record.user_name} ({key_record.user_email})")
        
        # Update last used timestamp asynchronously
        asyncio.create_task(async_update_key_usage(api_key))
        
        return api_key
    finally:
        db.close()


async def async_update_key_usage(key: str):
    """Update API key usage timestamp (non-blocking)"""
    try:
        update_api_key_usage(key)
    except Exception as e:
        logger.debug(f"Failed to update key usage: {e}")

# Pydantic models
class Section(BaseModel):
    """Represents a section in an article"""
    title: str
    content: str
    level: int = Field(description="Heading level (1-6)")

class ArticleMetadata(BaseModel):
    """Metadata about the article"""
    fact_checked: Optional[str] = None
    last_updated: Optional[str] = None
    word_count: int = 0

class Article(BaseModel):
    """Complete article response"""
    title: str
    slug: str
    url: str
    summary: str = Field(description="First paragraph or intro text")
    full_content: str = Field(description="Complete article text")
    sections: List[Section]
    table_of_contents: List[str]
    references: List[str]
    metadata: ArticleMetadata
    scraped_at: str

class SearchResult(BaseModel):
    """Search result item"""
    title: str
    slug: str
    url: str
    snippet: Optional[str] = None

class HealthResponse(BaseModel):
    """API health check response"""
    status: str
    timestamp: str
    base_url: str

class StatsResponse(BaseModel):
    """Statistics from Grokipedia homepage"""
    articles_available: int
    scraped_at: str


# API Key Management Models
class APIKeyCreateRequest(BaseModel):
    """Request model for creating a new API key"""
    user_name: str = Field(..., min_length=1, max_length=100)
    user_email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    rate_limit: int = Field(default=10, ge=1, le=100)
    notes: Optional[str] = Field(None, max_length=500)


class APIKeyResponse(BaseModel):
    """Response model for API key operations"""
    id: str
    key: str
    user_name: str
    user_email: str
    rate_limit: int
    is_active: bool
    created_at: str
    last_used: Optional[str]
    notes: Optional[str]


class APIKeyListResponse(BaseModel):
    """Response model for listing API keys"""
    id: str
    user_name: str
    user_email: str
    rate_limit: int
    is_active: bool
    created_at: str
    last_used: Optional[str]


# Helper functions
async def get_from_cache(key: str) -> Optional[str]:
    """Get data from Redis cache"""
    if not redis_client:
        return None
    try:
        data = await redis_client.get(key)
        if data:
            logger.debug(f"Cache hit: {key}")
            return data.decode() if isinstance(data, bytes) else data
    except Exception as e:
        logger.warning(f"Cache read error: {e}")
    return None

async def set_in_cache(key: str, value: str, ttl: int = CACHE_TTL):
    """Set data in Redis cache"""
    if not redis_client:
        return
    try:
        await redis_client.setex(key, ttl, value)
        logger.debug(f"Cache set: {key}")
    except Exception as e:
        logger.warning(f"Cache write error: {e}")

async def fetch_html(url: str) -> str:
    """Fetch HTML content from URL with error handling and caching"""
    # Try cache first
    cache_key = f"html:{url}"
    cached = await get_from_cache(cache_key)
    if cached:
        return cached
    
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        try:
            headers = {
                "User-Agent": "GrokipediaAPI/1.0 (Educational API; +https://github.com/yourrepo)"
            }
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            html = response.text
            
            # Cache the HTML
            await set_in_cache(cache_key, html)
            
            return html
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Article not found: {url}")
            logger.error(f"HTTP error {e.response.status_code} fetching {url}")
            raise HTTPException(status_code=e.response.status_code, detail=f"Error fetching page: {str(e)}")
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching {url}")
            raise HTTPException(status_code=504, detail="Request timeout - Grokipedia took too long to respond")
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error fetching page: {str(e)}")


def extract_sections(soup: BeautifulSoup) -> tuple[List[Section], List[str]]:
    """Extract sections and table of contents from article"""
    sections = []
    toc = []
    
    # Find all heading tags
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    
    for heading in headings:
        level = int(heading.name[1])  # Extract number from h1, h2, etc.
        title = heading.get_text(strip=True)
        
        # Skip the main article title (usually h1)
        if level == 1:
            continue
            
        toc.append(title)
        
        # Get content after heading until next heading
        content_parts = []
        for sibling in heading.find_next_siblings():
            if sibling.name and sibling.name.startswith('h'):
                break
            text = sibling.get_text(strip=True)
            if text:
                content_parts.append(text)
        
        sections.append(Section(
            title=title,
            content=" ".join(content_parts),
            level=level
        ))
    
    return sections, toc


def extract_references(soup: BeautifulSoup) -> List[str]:
    """Extract reference links from article"""
    references = []
    
    # Look for References heading (h2 with id or text "References")
    ref_section = soup.find(['h2', 'h3'], string=re.compile(r'^References?$', re.IGNORECASE))
    if not ref_section:
        # Try finding by id
        ref_section = soup.find(id='references') or soup.find(id='References')
    
    if ref_section:
        # Get all content after references section
        current = ref_section.find_next_sibling()
        while current:
            # Stop if we hit another major section
            if current.name in ['h1', 'h2']:
                break
            
            # Extract all links from ordered/unordered lists
            if current.name in ['ol', 'ul']:
                for link in current.find_all('a', href=True):
                    href = link.get('href', '')
                    if href.startswith('http'):
                        references.append(href)
            
            # Extract links from paragraphs or divs
            elif current.name in ['p', 'div']:
                for link in current.find_all('a', href=True):
                    href = link.get('href', '')
                    if href.startswith('http'):
                        references.append(href)
            
            current = current.find_next_sibling()
    
    # Fallback: Find all external links (excluding Grokipedia itself)
    if not references:
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href', '')
            if href.startswith('http') and 'grokipedia.com' not in href:
                references.append(href)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_refs = []
    for ref in references:
        if ref not in seen:
            seen.add(ref)
            unique_refs.append(ref)
    
    return unique_refs


def extract_fact_check_info(soup: BeautifulSoup) -> Optional[str]:
    """Extract fact-check information if available"""
    # Method 1: Look in meta tags
    meta_desc = soup.find('meta', {'property': 'og:description'})
    if meta_desc:
        content = meta_desc.get('content', '')
        if 'Fact-checked' in content:
            match = re.search(r'Fact-checked by (.+?)(?:\.|$)', content)
            if match:
                return match.group(1).strip()
    
    # Method 2: Look for text in the page
    # Search for elements containing "Fact-checked"
    for element in soup.find_all(string=re.compile(r'Fact-checked by', re.IGNORECASE)):
        text = element.strip()
        # Extract just the fact-check info
        match = re.search(r'Fact-checked by\s+(.+?)(?:\s*[A-Z]|$)', text)
        if match:
            fact_check = match.group(1).strip()
            # Clean up common concatenations
            fact_check = re.split(r'\s{2,}|\n', fact_check)[0]
            return fact_check
    
    return None


# API Endpoints
@app.get("/health")
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute") if RATE_LIMIT_ENABLED else lambda f: f
async def health_check(request: Request, api_key: Optional[str] = Depends(verify_api_key)):
    """Check API health and connectivity"""
    logger.info("Health check endpoint called")
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "base_url": BASE_URL,
        "environment": ENVIRONMENT,
        "cache_enabled": REDIS_ENABLED
    }


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get statistics from Grokipedia homepage"""
    html = await fetch_html(BASE_URL)
    soup = BeautifulSoup(html, 'html.parser')
    
    # Look for "Articles Available" text
    articles_count = 0
    text = soup.get_text()
    match = re.search(r'Articles Available(\d+)', text)
    if match:
        articles_count = int(match.group(1))
    
    return StatsResponse(
        articles_available=articles_count,
        scraped_at=datetime.utcnow().isoformat()
    )


@app.get("/article/{slug}", response_model=Article)
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute") if RATE_LIMIT_ENABLED else lambda f: f
async def get_article(request: Request, slug: str, api_key: Optional[str] = Depends(verify_api_key)):
    """
    Get a complete article from Grokipedia by slug
    
    Example: /article/Joe_Biden
    """
    logger.info(f"Fetching article: {slug}")
    url = f"{BASE_URL}/page/{slug}"
    html = await fetch_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract title first
    title_tag = soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else slug.replace('_', ' ')
    
    # Extract summary from meta description (most reliable)
    summary = ""
    meta_desc = soup.find('meta', {'property': 'og:description'}) or soup.find('meta', {'name': 'description'})
    if meta_desc:
        summary = meta_desc.get('content', '').strip()
    
    # Fallback: Extract from first paragraph if no meta description
    if not summary:
        # Try to find main article content area
        main_content = soup.find('article') or soup.find('main') or soup
        
        # Look for first substantial paragraph after h1
        if title_tag:
            # Get next elements after title
            for sibling in title_tag.find_next_siblings(['p', 'div']):
                text = sibling.get_text(strip=True)
                # Look for substantial content (intro paragraph is usually 200+ chars)
                if len(text) > 200 and not text.startswith('Jump to') and not text.startswith('From '):
                    summary = text
                    break
        
        # Last resort: first substantial paragraph anywhere
        if not summary:
            paragraphs = main_content.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 200:
                    summary = text
                    break
    
    # Extract references BEFORE modifying soup
    references = extract_references(soup)
    
    # Extract metadata BEFORE modifying soup
    fact_checked = extract_fact_check_info(soup)
    
    # NOW remove unwanted elements for clean text
    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'button']):
        element.decompose()
    
    # Get full text content
    full_content = soup.get_text(separator='\n', strip=True)
    
    # Extract sections and TOC
    sections, toc = extract_sections(soup)
    
    # Calculate word count
    word_count = len(full_content.split())
    
    metadata = ArticleMetadata(
        fact_checked=fact_checked,
        word_count=word_count
    )
    
    return Article(
        title=title,
        slug=slug,
        url=url,
        summary=summary,
        full_content=full_content,
        sections=sections,
        table_of_contents=toc,
        references=references,
        metadata=metadata,
        scraped_at=datetime.utcnow().isoformat()
    )


@app.get("/article/{slug}/summary")
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute") if RATE_LIMIT_ENABLED else lambda f: f
async def get_article_summary(request: Request, slug: str, api_key: Optional[str] = Depends(verify_api_key)):
    """
    Get just the summary/intro of an article (faster, less data)
    """
    logger.info(f"Fetching summary: {slug}")
    url = f"{BASE_URL}/page/{slug}"
    html = await fetch_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract title
    title_tag = soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else slug.replace('_', ' ')
    
    # Extract summary from meta description (most reliable)
    summary = ""
    meta_desc = soup.find('meta', {'property': 'og:description'}) or soup.find('meta', {'name': 'description'})
    if meta_desc:
        summary = meta_desc.get('content', '').strip()
    
    # Fallback: Extract from first paragraph if no meta description
    if not summary:
        main_content = soup.find('article') or soup.find('main') or soup
        if title_tag:
            for sibling in title_tag.find_next_siblings(['p', 'div']):
                text = sibling.get_text(strip=True)
                if len(text) > 200 and not text.startswith('Jump to'):
                    summary = text
                    break
        
        if not summary:
            paragraphs = main_content.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 200:
                    summary = text
                    break
    
    # Extract TOC for quick overview
    toc = []
    headings = soup.find_all(['h2', 'h3'])
    for h in headings[:10]:  # Limit to first 10
        toc.append(h.get_text(strip=True))
    
    return {
        "title": title,
        "slug": slug,
        "url": url,
        "summary": summary,
        "table_of_contents": toc,
        "scraped_at": datetime.utcnow().isoformat()
    }


@app.get("/article/{slug}/section/{section_title}")
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute") if RATE_LIMIT_ENABLED else lambda f: f
async def get_article_section(request: Request, slug: str, section_title: str, api_key: Optional[str] = Depends(verify_api_key)):
    """
    Get a specific section of an article by title
    """
    logger.info(f"Fetching section '{section_title}' from '{slug}'")
    article = await get_article(request, slug, api_key)
    
    # Find matching section (case-insensitive, partial match)
    section_title_lower = section_title.lower().replace('_', ' ')
    
    for section in article.sections:
        if section_title_lower in section.title.lower():
            return {
                "article_title": article.title,
                "section": section,
                "url": article.url
            }
    
    raise HTTPException(
        status_code=404,
        detail=f"Section '{section_title}' not found in article '{slug}'"
    )


@app.get("/search")
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute") if RATE_LIMIT_ENABLED else lambda f: f
async def search_articles(request: Request, q: str = Query(..., description="Search query"), limit: int = Query(10, ge=1, le=50, description="Maximum number of results"), api_key: Optional[str] = Depends(verify_api_key)):
    """
    Search for articles (Note: This is a basic implementation)
    
    For actual search, you would need to implement either:
    1. Scraping Grokipedia's search results page
    2. Maintaining your own index
    3. Using their API if available
    """
    logger.info(f"Search query: {q}")
    return {
        "query": q,
        "results": [],
        "message": "Search functionality requires either scraping search results page or maintaining an index"
    }


@app.get("/random")
async def get_random_article():
    """
    Get a random article (if Grokipedia supports it)
    """
    # Check if there's a /random endpoint
    try:
        url = f"{BASE_URL}/random"
        html = await fetch_html(url)
        # Extract slug from final URL after redirect
        # This is a placeholder - implement based on actual site behavior
        return {
            "message": "Random article feature - implementation depends on site support"
        }
    except:
        raise HTTPException(
            status_code=501,
            detail="Random article feature not available"
        )


# Rate limiting info endpoint
@app.get("/info")
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE * 5}/minute") if RATE_LIMIT_ENABLED else lambda f: f  # Higher limit for info
async def api_info(request: Request, api_key: Optional[str] = Depends(verify_api_key)):
    """Get information about this API"""
    logger.info("API info endpoint called")
    return {
        "name": "Grokipedia API",
        "version": "1.0.0",
        "environment": ENVIRONMENT,
        "description": "Unofficial API for accessing Grokipedia content",
        "documentation": "https://yourdomain.com/docs" if not DEBUG else "http://localhost:8000/",
        "endpoints": {
            "GET /health": "Health check",
            "GET /article/{slug}": "Get full article",
            "GET /article/{slug}/summary": "Get article summary",
            "GET /article/{slug}/section/{section_title}": "Get specific section",
            "GET /search?q={query}": "Search articles",
            "GET /info": "This endpoint"
        },
        "base_url": BASE_URL,
        "rate_limit": {
            "enabled": RATE_LIMIT_ENABLED,
            "requests_per_minute": RATE_LIMIT_PER_MINUTE
        },
        "cache": {
            "enabled": REDIS_ENABLED,
            "ttl_seconds": CACHE_TTL
        },
        "notes": [
            "This is an unofficial API that scrapes content from Grokipedia",
            "Please respect rate limits and robots.txt",
            "Cache is enabled to reduce load on Grokipedia",
            "For production use, implement proper monitoring"
        ],
        "legal": "Not affiliated with Grokipedia. Please review their ToS before heavy usage"
    }


# API Key Management Endpoints
@app.post("/admin/keys/create", response_model=APIKeyResponse)
async def create_new_api_key(request: APIKeyCreateRequest, admin_key: str = Query(..., description="Admin key for authorization")):
    """
    Create a new API key (requires admin key)
    
    Example admin_key query: ?admin_key=your-admin-key
    """
    # Verify admin key
    if not admin_key or admin_key != ADMIN_KEY or not ADMIN_KEY:
        logger.warning(f"Unauthorized API key creation attempt")
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    try:
        new_key = create_api_key(
            user_name=request.user_name,
            user_email=request.user_email,
            rate_limit=request.rate_limit,
            notes=request.notes
        )
        
        db = SessionLocal()
        try:
            key_record = db.query(APIKey).filter(APIKey.key == new_key).first()
            logger.info(f"✓ Created API key for {request.user_name} ({request.user_email})")
            
            return APIKeyResponse(
                id=key_record.id,
                key=new_key,
                user_name=key_record.user_name,
                user_email=key_record.user_email,
                rate_limit=key_record.rate_limit,
                is_active=key_record.is_active,
                created_at=key_record.created_at.isoformat(),
                last_used=key_record.last_used.isoformat() if key_record.last_used else None,
                notes=key_record.notes
            )
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating API key: {str(e)}")


@app.get("/admin/keys", response_model=List[APIKeyListResponse])
async def list_api_keys(admin_key: str = Query(...), active_only: bool = Query(True)):
    """
    List all API keys (requires admin key)
    
    Example: /admin/keys?admin_key=your-admin-key&active_only=true
    """
    # Verify admin key
    if not admin_key or admin_key != ADMIN_KEY or not ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    try:
        keys = get_all_api_keys(active_only=active_only)
        logger.info(f"Listed {len(keys)} API keys")
        
        return [
            APIKeyListResponse(
                id=key.id,
                user_name=key.user_name,
                user_email=key.user_email,
                rate_limit=key.rate_limit,
                is_active=key.is_active,
                created_at=key.created_at.isoformat(),
                last_used=key.last_used.isoformat() if key.last_used else None
            )
            for key in keys
        ]
    except Exception as e:
        logger.error(f"Error listing API keys: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing API keys: {str(e)}")


@app.delete("/admin/keys/{key_id}")
async def revoke_key(key_id: str, admin_key: str = Query(...)):
    """
    Revoke an API key (requires admin key)
    
    Example: /admin/keys/key-id?admin_key=your-admin-key
    """
    # Verify admin key
    if not admin_key or admin_key != ADMIN_KEY or not ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    try:
        success = revoke_api_key(key_id)
        if not success:
            raise HTTPException(status_code=404, detail="API key not found")
        
        logger.info(f"✓ Revoked API key: {key_id}")
        return {"message": "API key revoked successfully", "key_id": key_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking API key: {e}")
        raise HTTPException(status_code=500, detail=f"Error revoking API key: {str(e)}")


@app.get("/admin/keys/{key_id}")
async def get_key_details(key_id: str, admin_key: str = Query(...)):
    """
    Get details about a specific API key (requires admin key)
    """
    # Verify admin key
    if not admin_key or admin_key != ADMIN_KEY or not ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    try:
        db = SessionLocal()
        try:
            key_record = db.query(APIKey).filter(APIKey.id == key_id).first()
            if not key_record:
                raise HTTPException(status_code=404, detail="API key not found")
            
            return APIKeyListResponse(
                id=key_record.id,
                user_name=key_record.user_name,
                user_email=key_record.user_email,
                rate_limit=key_record.rate_limit,
                is_active=key_record.is_active,
                created_at=key_record.created_at.isoformat(),
                last_used=key_record.last_used.isoformat() if key_record.last_used else None
            )
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching API key details: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching API key details: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

