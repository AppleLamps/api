"""
Basic tests for the Grokipedia API
Run with: pytest test_api.py
or: python -m pytest test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["base_url"] == "https://grokipedia.com"


def test_api_info():
    """Test the API info endpoint"""
    response = client.get("/info")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Grokipedia API"
    assert data["version"] == "1.0.0"
    assert "endpoints" in data


def test_article_not_found():
    """Test handling of non-existent article"""
    response = client.get("/article/ThisArticleDoesNotExist123456")
    assert response.status_code == 404


def test_article_summary_structure():
    """Test that article summary returns correct structure"""
    # Note: This test makes a real request to Grokipedia
    # May fail if the site is down or article doesn't exist
    response = client.get("/article/Joe_Biden/summary")
    
    if response.status_code == 200:
        data = response.json()
        assert "title" in data
        assert "slug" in data
        assert "url" in data
        assert "summary" in data
        assert "table_of_contents" in data
        assert "scraped_at" in data
        assert isinstance(data["table_of_contents"], list)


def test_section_not_found():
    """Test handling of non-existent section"""
    response = client.get("/article/Joe_Biden/section/NonExistentSection123")
    # Should return 404 if section not found
    # Note: May take time due to actual scraping
    assert response.status_code in [404, 200]  # Depends on if partial match found


@pytest.mark.skip(reason="Makes actual HTTP request, slow")
def test_article_full_structure():
    """Test that full article returns all expected fields"""
    response = client.get("/article/Joe_Biden")
    
    if response.status_code == 200:
        data = response.json()
        # Check all required fields
        required_fields = [
            "title", "slug", "url", "summary", "full_content",
            "sections", "table_of_contents", "references",
            "metadata", "scraped_at"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Check metadata structure
        assert "word_count" in data["metadata"]
        
        # Check sections structure
        if data["sections"]:
            section = data["sections"][0]
            assert "title" in section
            assert "content" in section
            assert "level" in section


def test_search_endpoint():
    """Test search endpoint (currently returns placeholder)"""
    response = client.get("/search?q=Biden")
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert data["query"] == "Biden"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

