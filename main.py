from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import httpx
from bs4 import BeautifulSoup
import re
from datetime import datetime
import asyncio
from urllib.parse import urljoin, quote

app = FastAPI(
    title="Grokipedia API",
    description="Programmatic access to Grokipedia content for AI models and applications",
    version="1.0.0",
    docs_url="/",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
BASE_URL = "https://grokipedia.com"
TIMEOUT = 30.0

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


# Helper functions
async def fetch_html(url: str) -> str:
    """Fetch HTML content from URL with error handling"""
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        try:
            headers = {
                "User-Agent": "GrokipediaAPI/1.0 (Educational API; +https://github.com/yourrepo)"
            }
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Article not found: {url}")
            raise HTTPException(status_code=e.response.status_code, detail=f"Error fetching page: {str(e)}")
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Request timeout")
        except Exception as e:
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
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health and connectivity"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        base_url=BASE_URL
    )


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
async def get_article(slug: str):
    """
    Get a complete article from Grokipedia by slug
    
    Example: /article/Joe_Biden
    """
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
async def get_article_summary(slug: str):
    """
    Get just the summary/intro of an article (faster, less data)
    """
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
async def get_article_section(slug: str, section_title: str):
    """
    Get a specific section of an article by title
    """
    article = await get_article(slug)
    
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
async def search_articles(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results")
):
    """
    Search for articles (Note: This is a basic implementation)
    
    For actual search, you would need to implement either:
    1. Scraping Grokipedia's search results page
    2. Maintaining your own index
    3. Using their API if available
    """
    # This is a placeholder - implement actual search logic based on site structure
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
async def api_info():
    """Get information about this API"""
    return {
        "name": "Grokipedia API",
        "version": "1.0.0",
        "description": "Unofficial API for accessing Grokipedia content",
        "endpoints": {
            "GET /health": "Health check",
            "GET /stats": "Get site statistics",
            "GET /article/{slug}": "Get full article",
            "GET /article/{slug}/summary": "Get article summary",
            "GET /article/{slug}/section/{section_title}": "Get specific section",
            "GET /search?q={query}": "Search articles (basic)",
            "GET /info": "This endpoint"
        },
        "base_url": BASE_URL,
        "notes": [
            "This is an unofficial API that scrapes content",
            "Please respect rate limits and robots.txt",
            "Consider caching responses to reduce load",
            "For production use, implement proper rate limiting"
        ],
        "legal": "Please check Grokipedia's Terms of Service before heavy usage"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

