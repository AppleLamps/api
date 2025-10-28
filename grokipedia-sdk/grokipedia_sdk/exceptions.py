"""Custom exceptions for the Grokipedia SDK"""


class GrokipediaError(Exception):
    """Base exception for the SDK"""
    pass


class ArticleNotFound(GrokipediaError):
    """Raised when an article (slug) does not exist."""
    pass


class RequestError(GrokipediaError):
    """Raised for network or HTTP errors."""
    pass

