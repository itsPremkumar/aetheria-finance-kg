"""
Finance KG - Raw cache module.

Simple in-memory cache with TTL support for API responses.
"""

from __future__ import annotations
from typing import Any, Optional
import time


class RawCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self, ttl: int = 3600):
        self._cache: dict[str, tuple[Any, float]] = {}
        self.ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        """Get a cached value."""
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                return value
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set a cached value."""
        expiry = time.time() + (ttl or self.ttl)
        self._cache[key] = (value, expiry)

    def delete(self, key: str):
        """Delete a cached value."""
        self._cache.pop(key, None)

    def clear(self):
        """Clear all cached values."""
        self._cache.clear()

    def size(self) -> int:
        """Get the number of cached items."""
        return len(self._cache)
