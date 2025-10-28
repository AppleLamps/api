# Quick Start Guide

Get your Grokipedia API running in 3 minutes! 🚀

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Run the API

```bash
# Start the server
python main.py
```

The API will start at: **http://localhost:8000**

## Test it Out

### 1. Open Interactive Docs
Visit http://localhost:8000 in your browser to see the Swagger UI with all endpoints.

### 2. Try the Examples
In a new terminal, run:
```bash
python example_usage.py
```

### 3. Manual Test
```bash
# Health check
curl http://localhost:8000/health

# Get an article
curl http://localhost:8000/article/Joe_Biden | python -m json.tool

# Get just the summary (faster)
curl http://localhost:8000/article/Joe_Biden/summary
```

## Common Usage Patterns

### For AI Models
```python
import requests

# Fetch article
response = requests.get("http://localhost:8000/article/Joe_Biden")
article = response.json()

# Use the content
print(f"Title: {article['title']}")
print(f"Content: {article['full_content'][:500]}...")
```

### Get Specific Information
```python
# Get just a summary
response = requests.get("http://localhost:8000/article/Joe_Biden/summary")

# Get a specific section
response = requests.get("http://localhost:8000/article/Joe_Biden/section/Presidency")
```

## Available Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Interactive API documentation |
| `GET /health` | Health check |
| `GET /article/{slug}` | Get full article |
| `GET /article/{slug}/summary` | Get article summary |
| `GET /article/{slug}/section/{title}` | Get specific section |
| `GET /stats` | Get site statistics |
| `GET /info` | API information |

## Tips

- **Article slugs** use underscores: `Joe_Biden`, `Donald_Trump`
- **Cache responses** in production to reduce load
- **Check** `/info` endpoint for full API documentation
- **Use** `/summary` for faster responses when you don't need everything

## Next Steps

1. ✅ Read the full [README.md](README.md) for detailed documentation
2. ✅ Check [example_usage.py](example_usage.py) for more examples
3. ✅ Review the interactive docs at http://localhost:8000
4. ✅ Implement caching for production use

## Troubleshooting

**"Connection Error"**
- Make sure the API is running: `python main.py`
- Check if port 8000 is already in use

**"Article not found"**
- Verify the article exists on Grokipedia
- Check the slug format (use underscores, not spaces)

**"Timeout"**
- Article might be very large
- Check your internet connection
- Increase timeout in settings

---

Need help? Check the full [README.md](README.md) or open an issue!

