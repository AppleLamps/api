# Grokipedia API

A RESTful API that provides programmatic access to [Grokipedia](https://grokipedia.com) content, designed for AI models and applications that need structured access to Grokipedia articles.

## Features

- 🚀 **Fast & Async**: Built with FastAPI and async HTTP requests
- 📖 **Full Article Access**: Get complete articles with structured data
- 🔍 **Section Extraction**: Access specific sections of articles
- 📊 **Structured Data**: Returns JSON with sections, references, and metadata
- 🎯 **AI-Friendly**: Designed for easy integration with AI models
- 📚 **Auto Documentation**: Interactive API docs at `/` (Swagger UI)

## Installation

### Prerequisites
- Python 3.8 or higher
- pip

### Setup

1. **Clone or download this repository**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment variables** (optional):
```bash
cp .env.example .env
# Edit .env with your preferred settings
```

## Usage

### Start the API Server

```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Interactive Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health & Info

#### `GET /health`
Check API health status
```bash
curl http://localhost:8000/health
```

#### `GET /info`
Get API information and available endpoints
```bash
curl http://localhost:8000/info
```

#### `GET /stats`
Get Grokipedia statistics
```bash
curl http://localhost:8000/stats
```

### Articles

#### `GET /article/{slug}`
Get a complete article with all sections, references, and metadata

**Example**:
```bash
curl http://localhost:8000/article/Joe_Biden
```

**Response**:
```json
{
  "title": "Joe Biden",
  "slug": "Joe_Biden",
  "url": "https://grokipedia.com/page/Joe_Biden",
  "summary": "Joseph Robinette Biden Jr. (born November 20, 1942)...",
  "full_content": "...",
  "sections": [
    {
      "title": "Early life and education",
      "content": "...",
      "level": 2
    }
  ],
  "table_of_contents": [
    "Early life and education",
    "Family background and childhood",
    ...
  ],
  "references": [
    "https://example.com/ref1",
    ...
  ],
  "metadata": {
    "fact_checked": "Grok yesterday",
    "word_count": 15234
  },
  "scraped_at": "2025-10-28T12:34:56.789"
}
```

#### `GET /article/{slug}/summary`
Get just the summary and table of contents (faster, less data)

**Example**:
```bash
curl http://localhost:8000/article/Joe_Biden/summary
```

#### `GET /article/{slug}/section/{section_title}`
Get a specific section of an article

**Example**:
```bash
curl http://localhost:8000/article/Joe_Biden/section/Early_life
```

### Search (Basic)

#### `GET /search?q={query}&limit={limit}`
Search for articles (basic implementation)

**Example**:
```bash
curl "http://localhost:8000/search?q=Biden&limit=10"
```

## Usage Examples

### Python

```python
import requests

# Get an article
response = requests.get("http://localhost:8000/article/Joe_Biden")
article = response.json()

print(f"Title: {article['title']}")
print(f"Summary: {article['summary']}")
print(f"Sections: {len(article['sections'])}")

# Get just the summary
response = requests.get("http://localhost:8000/article/Joe_Biden/summary")
summary = response.json()
print(summary['summary'])
```

### JavaScript/Node.js

```javascript
// Get an article
fetch('http://localhost:8000/article/Joe_Biden')
  .then(response => response.json())
  .then(article => {
    console.log('Title:', article.title);
    console.log('Summary:', article.summary);
    console.log('Sections:', article.sections.length);
  });
```

### cURL

```bash
# Get full article
curl http://localhost:8000/article/Joe_Biden | jq .

# Get just the summary
curl http://localhost:8000/article/Joe_Biden/summary | jq .

# Get a specific section
curl http://localhost:8000/article/Joe_Biden/section/Presidency | jq .
```

### Using with AI Models

```python
import requests
import openai

# Fetch article content
response = requests.get("http://localhost:8000/article/Joe_Biden")
article = response.json()

# Use with OpenAI
client = openai.OpenAI()
completion = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant with access to Grokipedia."},
        {"role": "user", "content": f"Summarize this article:\n\n{article['full_content'][:4000]}"}
    ]
)

print(completion.choices[0].message.content)
```

## Response Models

### Article
- `title` (string): Article title
- `slug` (string): URL slug
- `url` (string): Full Grokipedia URL
- `summary` (string): First substantial paragraph
- `full_content` (string): Complete article text
- `sections` (array): Structured sections with titles and content
- `table_of_contents` (array): List of section titles
- `references` (array): External reference URLs
- `metadata` (object): Article metadata (fact-check info, word count)
- `scraped_at` (string): ISO 8601 timestamp

### Section
- `title` (string): Section heading
- `content` (string): Section text content
- `level` (integer): Heading level (2-6)

## Best Practices

### Rate Limiting
- Implement rate limiting for production use
- Cache responses when possible
- Add delays between requests
- Consider using Redis for distributed rate limiting

### Caching
Consider implementing caching to reduce load on Grokipedia:
```python
from functools import lru_cache
from datetime import datetime, timedelta

# Simple in-memory cache (for development)
@lru_cache(maxsize=100)
def cached_article(slug, cache_key):
    # Fetch article logic here
    pass

# For production, use Redis or similar
```

### Error Handling
The API returns standard HTTP status codes:
- `200`: Success
- `404`: Article not found
- `500`: Server error
- `504`: Timeout

## Legal & Ethical Considerations

⚠️ **Important**: This is an unofficial API that scrapes public content.

- ✅ Check Grokipedia's `robots.txt`: https://grokipedia.com/robots.txt
- ✅ Review their Terms of Service
- ✅ Respect rate limits
- ✅ Cache responses to minimize requests
- ✅ Attribute content properly

**This API is for educational and research purposes. Heavy production use should be coordinated with Grokipedia.**

## Development

### Project Structure
```
api/
├── main.py              # Main FastAPI application
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
└── README.md           # This file
```

### Future Enhancements

- [ ] Implement proper search functionality
- [ ] Add Redis caching layer
- [ ] Add rate limiting middleware
- [ ] Support for bulk article fetching
- [ ] Export articles to different formats (PDF, Markdown)
- [ ] Webhook support for article updates
- [ ] Authentication for private deployments
- [ ] Database for article indexing
- [ ] Support for article history/revisions

## Deployment

### Docker (Optional)

Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t grokipedia-api .
docker run -p 8000:8000 grokipedia-api
```

### Cloud Deployment

The API can be deployed to:
- **Railway**: `railway up`
- **Heroku**: Standard Python deployment
- **AWS Lambda**: Using Mangum adapter
- **Google Cloud Run**: Container-based deployment
- **DigitalOcean App Platform**: Git-based deployment

## Troubleshooting

### Connection Errors
- Check if Grokipedia is accessible
- Verify network connectivity
- Check firewall settings

### Timeout Errors
- Increase `TIMEOUT` value in settings
- Check for slow network connection

### Parse Errors
- Website structure may have changed
- Check if article slug is correct
- Verify HTML parsing logic

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - Feel free to use this for your projects.

## Disclaimer

This is an unofficial API and is not affiliated with, endorsed by, or connected to Grokipedia. Use responsibly and in accordance with Grokipedia's terms of service.

## Support

For issues or questions:
- Open an issue on GitHub
- Check existing documentation
- Review Grokipedia's official resources

---

**Built with FastAPI** 🚀 **Powered by BeautifulSoup** 🥣

