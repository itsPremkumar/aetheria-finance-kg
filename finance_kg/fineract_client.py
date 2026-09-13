"""
Finance KG - Apache Fineract client.

REST API client for Apache Fineract with offline caching.
Supports clients, loans, accounts, and transactions APIs.
"""

from __future__ import annotations
from typing import Any, Optional
import json
import urllib.request
import urllib.error


class FineractClient:
    """Client for Apache Fineract REST API with offline caching."""

    def __init__(
        self,
        base_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        cache: Optional[Any] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.cache = cache
        self._headers = {
            "Content-Type": "application/json",
            "Fineract-Platform-TenantId": "default",
        }

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        """Make a GET request to the Fineract API."""
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

    def get_clients(self, offset: int = 0, limit: int = 100) -> list[dict]:
        """Get all clients from Fineract."""
        data = self._get("/fineract-provider/api/v1/clients", {"offset": offset, "limit": limit})
        return data.get("pageItems", [])

    def get_client(self, client_id: str) -> dict:
        """Get a specific client by ID."""
        return self._get(f"/fineract-provider/api/v1/clients/{client_id}")

    def get_loans(self, client_id: str) -> list[dict]:
        """Get all loans for a client."""
        data = self._get(f"/fineract-provider/api/v1/clients/{client_id}/accounts")
        return data.get("loanAccounts", [])

    def get_savings(self, client_id: str) -> list[dict]:
        """Get all savings accounts for a client."""
        data = self._get(f"/fineract-provider/api/v1/clients/{client_id}/accounts")
        return data.get("savingsAccounts", [])

    def get_loan_details(self, loan_id: str) -> dict:
        """Get details for a specific loan."""
        return self._get(f"/fineract-provider/api/v1/loans/{loan_id}")

    def get_transactions(
        self,
        account_type: str,
        account_id: str,
    ) -> list[dict]:
        """Get transactions for an account."""
        data = self._get(
            f"/fineract-provider/api/v1/{account_type}/{account_id}/transactions",
        )
        return data.get("pageItems", [])

    def get_offices(self) -> list[dict]:
        """Get all offices."""
        data = self._get("/fineract-provider/api/v1/offices")
        return data.get("pageItems", [])

    def get_staff(self) -> list[dict]:
        """Get all staff members."""
        data = self._get("/fineract-provider/api/v1/staff")
        return data.get("pageItems", [])
