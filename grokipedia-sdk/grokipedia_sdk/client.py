"""Core SDK client for interacting with Grokipedia"""

import httpx
from bs4 import BeautifulSoup
import re
from datetime import datetime
from typing import Optional, List, Tuple
from urllib.parse import urljoin

from .models import Article, ArticleSummary, Section, ArticleMetadata
from .exceptions import ArticleNotFound, RequestError


class Client:
    """Client for accessing Grokipedia content"""
    
    def __init__(self, base_url: str = "https://grokipedia.com", timeout: float = 30.0):
        """
        Initialize the Grokipedia SDK client.
        
        Args:
            base_url: Base URL for Grokipedia (default: https://grokipedia.com)
            timeout: Request timeout in seconds (default: 30.0)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout, follow_redirects=True)
    
    def __enter__(self):
        """Support for context manager"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up httpx client on exit"""
        self.close()
    
    def close(self):
        """Close the HTTP client"""
        if self._client:
            self._client.close()
    
    def _fetch_html(self, url: str) -> str:
        """
        Fetch HTML content from URL with error handling.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content as string
            
        Raises:
            ArticleNotFound: If the article is not found (404)
            RequestError: For other HTTP errors or network issues
        """
        try:
            headers = {
                "User-Agent": "GrokipediaSDK/1.0 (Python SDK; +https://github.com/yourrepo)"
            }
            response = self._client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ArticleNotFound(f"Article not found: {url}")
            raise RequestError(f"HTTP error {e.response.status_code} fetching {url}: {str(e)}")
        except httpx.TimeoutException:
            raise RequestError(f"Request timeout - Grokipedia took too long to respond")
        except Exception as e:
            raise RequestError(f"Error fetching {url}: {str(e)}")
    
    def _extract_sections(self, soup: BeautifulSoup) -> Tuple[List[Section], List[str]]:
        """
        Extract sections and table of contents from article.
        
        Args:
            soup: BeautifulSoup object of the article
            
        Returns:
            Tuple of (sections list, table of contents list)
        """
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
    
    def _extract_references(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract reference links from article.
        
        Args:
            soup: BeautifulSoup object of the article
            
        Returns:
            List of reference URLs
        """
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
    
    def _extract_fact_check_info(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract fact-check information if available.
        
        Args:
            soup: BeautifulSoup object of the article
            
        Returns:
            Fact-check information or None
        """
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
    
    def _extract_summary(self, soup: BeautifulSoup, title_tag) -> str:
        """
        Extract summary/intro text from article.
        
        Args:
            soup: BeautifulSoup object of the article
            title_tag: The h1 title tag
            
        Returns:
            Summary text
        """
        summary = ""
        
        # Extract summary from meta description (most reliable)
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
        
        return summary
    
    def get_article(self, slug: str) -> Article:
        """
        Get a complete article from Grokipedia by slug.
        
        Args:
            slug: Article slug (e.g., "Joe_Biden")
            
        Returns:
            Article object with full content
            
        Raises:
            ArticleNotFound: If the article doesn't exist
            RequestError: For network or HTTP errors
        """
        url = f"{self.base_url}/page/{slug}"
        html = self._fetch_html(url)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title first
        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else slug.replace('_', ' ')
        
        # Extract summary
        summary = self._extract_summary(soup, title_tag)
        
        # Extract references BEFORE modifying soup
        references = self._extract_references(soup)
        
        # Extract metadata BEFORE modifying soup
        fact_checked = self._extract_fact_check_info(soup)
        
        # NOW remove unwanted elements for clean text
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'button']):
            element.decompose()
        
        # Get full text content
        full_content = soup.get_text(separator='\n', strip=True)
        
        # Extract sections and TOC
        sections, toc = self._extract_sections(soup)
        
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
    
    def get_summary(self, slug: str) -> ArticleSummary:
        """
        Get just the summary/intro of an article (faster, less data).
        
        Args:
            slug: Article slug (e.g., "Joe_Biden")
            
        Returns:
            ArticleSummary object with summary and TOC
            
        Raises:
            ArticleNotFound: If the article doesn't exist
            RequestError: For network or HTTP errors
        """
        url = f"{self.base_url}/page/{slug}"
        html = self._fetch_html(url)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else slug.replace('_', ' ')
        
        # Extract summary
        summary = self._extract_summary(soup, title_tag)
        
        # Extract TOC for quick overview
        toc = []
        headings = soup.find_all(['h2', 'h3'])
        for h in headings[:10]:  # Limit to first 10
            toc.append(h.get_text(strip=True))
        
        return ArticleSummary(
            title=title,
            slug=slug,
            url=url,
            summary=summary,
            table_of_contents=toc,
            scraped_at=datetime.utcnow().isoformat()
        )
    
    def get_section(self, slug: str, section_title: str) -> Optional[Section]:
        """
        Get a specific section of an article by title.
        
        Args:
            slug: Article slug (e.g., "Joe_Biden")
            section_title: Section title to search for
            
        Returns:
            Section object if found, None otherwise
            
        Raises:
            ArticleNotFound: If the article doesn't exist
            RequestError: For network or HTTP errors
        """
        article = self.get_article(slug)
        
        # Find matching section (case-insensitive, partial match)
        section_title_lower = section_title.lower().replace('_', ' ')
        
        for section in article.sections:
            if section_title_lower in section.title.lower():
                return section
        
        return None

