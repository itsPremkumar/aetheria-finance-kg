"""Apache Fineract API client with offline caching."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Optional
from urllib.parse import urljoin

import httpx


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


class FineractClient:
    """Client for Apache Fineract REST API.

    Supports offline-first operation via response caching.
    """

    def __init__(
        self,
        base_url: str,
        username: str = "mifos",
        password: str = "password",
        tenant_id: str = "default",
        cache: Optional[RawCache] = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.tenant_id = tenant_id
        self.cache = cache or RawCache()
        self.timeout = timeout
        self._token: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {"Fineract-Platform-TenantId": self.tenant_id}
            if self._token:
                headers["Authorization"] = f"Basic {self._token}"
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout,
            )
        return self._client

    async def authenticate(self) -> str:
        """Authenticate and store the access token."""
        client = await self._get_client()
        response = await client.post(
            "/fineract-provider/api/v1/authentication",
            params={
                "username": self.username,
                "password": self.password,
            },
        )
        response.raise_for_status()
        data = response.json()
        self._token = data.get("base64EncodedAuthenticationKey")
        return self._token

    async def _request(
        self, method: str, path: str, use_cache: bool = True, **kwargs: Any
    ) -> dict[str, Any]:
        """Make an API request with caching."""
        cache_key = f"{method}:{path}:{hash(str(kwargs))}"

        if use_cache and method.upper() == "GET":
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        client = await self._get_client()
        response = await client.request(method, path, **kwargs)
        response.raise_for_status()
        data = response.json()

        if use_cache and method.upper() == "GET":
            self.cache.set(cache_key, data)

        return data

    async def get_clients(
        self, offset: int = 0, limit: int = 100
    ) -> dict[str, Any]:
        """Retrieve all clients."""
        return await self._request(
            "GET",
            "/fineract-provider/api/v1/clients",
            params={"offset": offset, "limit": limit},
        )

    async def get_client(self, client_id: int) -> dict[str, Any]:
        """Retrieve a single client by ID."""
        return await self._request(
            "GET", f"/fineract-provider/api/v1/clients/{client_id}"
        )

    async def get_loans(
        self, offset: int = 0, limit: int = 100
    ) -> dict[str, Any]:
        """Retrieve all loan accounts."""
        return await self._request(
            "GET",
            "/fineract-provider/api/v1/loans",
            params={"offset": offset, "limit": limit},
        )

    async def get_loan(self, loan_id: int) -> dict[str, Any]:
        """Retrieve a single loan account."""
        return await self._request(
            "GET", f"/fineract-provider/api/v1/loans/{loan_id}"
        )

    async def get_savings_accounts(
        self, offset: int = 0, limit: int = 100
    ) -> dict[str, Any]:
        """Retrieve all savings accounts."""
        return await self._request(
            "GET",
            "/fineract-provider/api/v1/savingsaccounts",
            params={"offset": offset, "limit": limit},
        )

    async def get_gl_accounts(self) -> dict[str, Any]:
        """Retrieve chart of accounts (general ledger)."""
        return await self._request(
            "GET", "/fineract-provider/api/v1/glaccounts"
        )

    async def get_journal_entries(
        self, offset: int = 0, limit: int = 100
    ) -> dict[str, Any]:
        """Retrieve journal entries."""
        return await self._request(
            "GET",
            "/fineract-provider/api/v1/journalentries",
            params={"offset": offset, "limit": limit},
        )

    async def get_reports(self) -> dict[str, Any]:
        """Retrieve list of available reports."""
        return await self._request(
            "GET", "/fineract-provider/api/v1/reports"
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
