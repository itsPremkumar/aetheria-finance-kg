"""
Finance KG - OpenBB client.

Market data client for OpenBB with offline caching.
Supports stocks, ETFs, bonds, and market data.
"""

from __future__ import annotations
from typing import Any, Optional
import json
import urllib.request
import urllib.error


class OpenBBClient:
    """Client for OpenBB market data API with offline caching."""

    def __init__(
        self,
        token: Optional[str] = None,
        cache: Optional[Any] = None,
    ):
        self.token = token
        self.cache = cache
        self.base_url = "https://api.openbb.co/v1"
        self._headers = {
            "Content-Type": "application/json",
        }
        if token:
            self._headers["Authorization"] = f"Bearer {token}"

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        """Make a GET request to the OpenBB API."""
        url = f"{self.base_url}{path}"
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query}"

        # Check cache first
        if self.cache:
            cached = self.cache.get(url)
            if cached is not None:
                return cached

        # Make request
        request = urllib.request.Request(url, headers=self._headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode())
                if self.cache:
                    self.cache.set(url, data)
                return data
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            return {"error": str(e)}

    def get_stock_price(self, symbol: str) -> dict:
        """Get current stock price."""
        return self._get(f"/equity/price/{symbol}")

    def get_stock_info(self, symbol: str) -> dict:
        """Get stock information."""
        return self._get(f"/equity/info/{symbol}")

    def get_etf_info(self, symbol: str) -> dict:
        """Get ETF information."""
        return self._get(f"/etf/info/{symbol}")

    def get_bond_info(self, symbol: str) -> dict:
        """Get bond information."""
        return self._get(f"/fixedincome/bond/{symbol}")

    def get_market_summary(self) -> dict:
        """Get market summary."""
        return self._get("/market/summary")

    def get_sector_performance(self) -> dict:
        """Get sector performance."""
        return self._get("/market/sectors")

    def get_news(self, symbol: Optional[str] = None) -> list[dict]:
        """Get news for a symbol or general market news."""
        if symbol:
            return self._get(f"/news/equity/{symbol}")
        return self._get("/news/market")

    def get_financials(self, symbol: str) -> dict:
        """Get financial statements for a company."""
        return self._get(f"/equity/financials/{symbol}")

    def get_historical(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> list[dict]:
        """Get historical price data."""
        return self._get(
            f"/equity/historical/{symbol}",
            {"start": start_date, "end": end_date},
        )
