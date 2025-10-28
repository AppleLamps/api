"""Pydantic models for the Grokipedia SDK"""

from pydantic import BaseModel, Field
from typing import List, Optional


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


class ArticleSummary(BaseModel):
    """Summary response for an article"""
    title: str
    slug: str
    url: str
    summary: str
    table_of_contents: List[str]
    scraped_at: str


class SearchResult(BaseModel):
    """Search result item"""
    title: str
    slug: str
    url: str
    snippet: Optional[str] = None

