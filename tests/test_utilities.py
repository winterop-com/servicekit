"""Tests for utility functions."""

from unittest.mock import MagicMock

from fastapi import Request

from servicekit.api.utilities import build_location_url


def test_build_location_url_with_https():
    """Test building full URL for Location header with HTTPS."""
    request = MagicMock(spec=Request)
    request.url.scheme = "https"
    request.url.netloc = "example.com"

    result = build_location_url(request, "/api/resource/123")
    assert result == "https://example.com/api/resource/123"


def test_build_location_url_with_http():
    """Test building URL with HTTP scheme."""
    request = MagicMock(spec=Request)
    request.url.scheme = "http"
    request.url.netloc = "localhost:8000"

    result = build_location_url(request, "/items/1")
    assert result == "http://localhost:8000/items/1"


def test_build_location_url_with_port():
    """Test building URL with custom port."""
    request = MagicMock(spec=Request)
    request.url.scheme = "https"
    request.url.netloc = "api.example.com:9000"

    result = build_location_url(request, "/v1/users/456")
    assert result == "https://api.example.com:9000/v1/users/456"
