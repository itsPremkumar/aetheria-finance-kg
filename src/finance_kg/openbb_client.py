"""OpenBB Platform client with offline caching."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Optional

try:
    from openbb import obb

    HAS_OPENBB = True
except ImportError:
    HAS_OPENBB = False


class OpenBBClient:
    """Client for OpenBB Platform financial data.

    Wraps the OpenBB Python SDK with offline caching.
    """

    def __init__(self, cache: Optional["RawCache"] = None):
        if not HAS_OPENBB:
            raise ImportError(
                "openbb package is required. Install with: pip install finance-kg[openbb]"
            )
        self.cache = cache or RawCache()

    def get_historical_prices(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "1d",
    ) -> dict[str, Any]:
        """Fetch historical OHLCV prices for a security."""
        cache_key = f"obb:price:{symbol}:{start_date}:{end_date}:{interval}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        result = obb.equity.price.historical(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
        )
        data = result.to_dict(orient="records") if hasattr(result, "to_dict") else result
        self.cache.set(cache_key, data)
        return data

    def get_fundamentals(self, symbol: str) -> dict[str, Any]:
        """Fetch fundamental data for a company."""
        cache_key = f"obb:fundamentals:{symbol}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        result = obb.equity.fundamental(symbol=symbol)
        data = result.to_dict(orient="records") if hasattr(result, "to_dict") else result
        self.cache.set(cache_key, data)
        return data

    def get_etf_holdings(self, symbol: str) -> dict[str, Any]:
        """Fetch ETF holdings."""
        cache_key = f"obb:etf:{symbol}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        result = obb.etf.holdings(symbol=symbol)
        data = result.to_dict(orient="records") if hasattr(result, "to_dict") else result
        self.cache.set(cache_key, data)
        return data

    def get_index_constituents(self, symbol: str) -> dict[str, Any]:
        """Fetch index constituents."""
        cache_key = f"obb:index:{symbol}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        result = obb.index.constituents(symbol=symbol)
        data = result.to_dict(orient="records") if hasattr(result, "to_dict") else result
        self.cache.set(cache_key, data)
        return data

    def get_company_news(self, symbol: str) -> dict[str, Any]:
        """Fetch company news."""
        cache_key = f"obb:news:{symbol}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        result = obb.news.company(symbol=symbol)
        data = result.to_dict(orient="records") if hasattr(result, "to_dict") else result
        self.cache.set(cache_key, data)
        return data


class RawCache:
    """SQLite-based cache for raw API responses."""

    def __init__(self, db_path: str = ":memory:", ttl_seconds: int = 3600):
        self.db_path = db_path
        self.ttl_seconds = ttl_seconds
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.commit()

    def get(self, key: str) -> Optional[dict[str, Any]]:
        cursor = self.conn.execute(
            "SELECT data, created_at FROM cache WHERE key = ?", (key,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        data_str, created_at = row
        created = datetime.fromisoformat(created_at)
        if datetime.now() - created > timedelta(seconds=self.ttl_seconds):
            self.conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            self.conn.commit()
            return None
        return json.loads(data_str)

    def set(self, key: str, data: dict[str, Any]) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO cache (key, data) VALUES (?, ?)",
            (key, json.dumps(data)),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
