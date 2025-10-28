# Grokipedia SDK

A Python SDK for accessing Grokipedia content programmatically. This SDK provides a clean, simple interface to fetch articles, summaries, and sections from Grokipedia without needing to implement web scraping yourself.

## Installation

### From Source

```bash
cd grokipedia-sdk
pip install -r requirements.txt
```

### Install as Package

```bash
cd grokipedia-sdk
pip install -e .
```

## Quick Start

### Basic Usage

```python
from grokipedia_sdk import Client, ArticleNotFound

# Create a client instance
client = Client()

# Fetch a full article
try:
    article = client.get_article("Joe_Biden")
    print(f"Title: {article.title}")
    print(f"Summary: {article.summary}")
    print(f"Sections: {len(article.sections)}")
    print(f"References: {len(article.references)}")
except ArticleNotFound:
    print("Article not found")
except RequestError as e:
    print(f"Error: {e}")
finally:
    client.close()
```

### Using Context Manager

```python
from grokipedia_sdk import Client

# Using context manager (recommended)
with Client() as client:
    # Get article summary (faster, less data)
    summary = client.get_summary("Joe_Biden")
    print(f"Title: {summary.title}")
    print(f"Summary: {summary.summary}")
    print(f"Table of Contents: {summary.table_of_contents}")
```

### Fetching Specific Sections

```python
from grokipedia_sdk import Client

with Client() as client:
    # Get a specific section
    section = client.get_section("Joe_Biden", "Early Life")
    if section:
        print(f"Section: {section.title}")
        print(f"Content: {section.content}")
    else:
        print("Section not found")
```

## API Reference

### Client

#### `Client(base_url: str = "https://grokipedia.com", timeout: float = 30.0)`

Initialize the Grokipedia SDK client.

**Parameters:**
- `base_url` (str): Base URL for Grokipedia (default: https://grokipedia.com)
- `timeout` (float): Request timeout in seconds (default: 30.0)

#### `get_article(slug: str) -> Article`

Get a complete article from Grokipedia by slug.

**Parameters:**
- `slug` (str): Article slug (e.g., "Joe_Biden")

**Returns:**
- `Article`: Complete article object with full content, sections, references, and metadata

**Raises:**
- `ArticleNotFound`: If the article doesn't exist
- `RequestError`: For network or HTTP errors

#### `get_summary(slug: str) -> ArticleSummary`

Get just the summary/intro of an article (faster, less data).

**Parameters:**
- `slug` (str): Article slug (e.g., "Joe_Biden")

**Returns:**
- `ArticleSummary`: Article summary with table of contents

**Raises:**
- `ArticleNotFound`: If the article doesn't exist
- `RequestError`: For network or HTTP errors

#### `get_section(slug: str, section_title: str) -> Optional[Section]`

Get a specific section of an article by title.

**Parameters:**
- `slug` (str): Article slug (e.g., "Joe_Biden")
- `section_title` (str): Section title to search for

**Returns:**
- `Optional[Section]`: Section object if found, None otherwise

**Raises:**
- `ArticleNotFound`: If the article doesn't exist
- `RequestError`: For network or HTTP errors

### Models

#### `Article`

Complete article response with:
- `title` (str): Article title
- `slug` (str): Article slug
- `url` (str): Full URL to the article
- `summary` (str): First paragraph or intro text
- `full_content` (str): Complete article text
- `sections` (List[Section]): List of article sections
- `table_of_contents` (List[str]): Table of contents
- `references` (List[str]): List of reference URLs
- `metadata` (ArticleMetadata): Article metadata
- `scraped_at` (str): ISO timestamp of when content was scraped

#### `ArticleSummary`

Summary response with:
- `title` (str): Article title
- `slug` (str): Article slug
- `url` (str): Full URL to the article
- `summary` (str): Article summary
- `table_of_contents` (List[str]): Table of contents
- `scraped_at` (str): ISO timestamp

#### `Section`

Represents a section in an article:
- `title` (str): Section title
- `content` (str): Section content
- `level` (int): Heading level (1-6)

#### `ArticleMetadata`

Metadata about the article:
- `fact_checked` (Optional[str]): Fact-check information
- `last_updated` (Optional[str]): Last update date
- `word_count` (int): Word count

### Exceptions

#### `GrokipediaError`

Base exception for the SDK.

#### `ArticleNotFound`

Raised when an article (slug) does not exist.

#### `RequestError`

Raised for network or HTTP errors.

## Custom Configuration

```python
from grokipedia_sdk import Client

# Use custom base URL
client = Client(base_url="https://custom-grokipedia.com")

# Set custom timeout
client = Client(timeout=60.0)

# Combine both
client = Client(base_url="https://custom-grokipedia.com", timeout=60.0)
```

## Error Handling

```python
from grokipedia_sdk import Client, ArticleNotFound, RequestError

client = Client()

try:
    article = client.get_article("NonExistent_Article")
except ArticleNotFound:
    print("Article not found on Grokipedia")
except RequestError as e:
    print(f"Network or HTTP error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
finally:
    client.close()
```

## Examples

See `example.py` for more comprehensive examples.

## License

This SDK is provided as-is for educational and development purposes. Please review Grokipedia's Terms of Service before heavy usage.

## Notes

- This SDK scrapes content from Grokipedia's website
- Please respect rate limits and robots.txt
- Not affiliated with Grokipedia
- Cache your results appropriately for production use

