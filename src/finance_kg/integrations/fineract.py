"""
integrations/fineract.py - Apache Fineract integration.

Maps Fineract's core banking domain (clients, loans, savings, accounting)
into the Finance Knowledge Graph.

Fineract API Reference:
- Clients: /fineract-provider/api/v1/clients
- Loans: /fineract-provider/api/v1/loans
- Savings: /fineract-provider/api/v1/savings
- Accounting: /fineract-provider/api/v1/glaccounts
- Reports: /fineract-provider/api/v1/runreports
- Batch API: /fineract-provider/api/v1/batches

Data Model Mapping:
- Fineract Client -> finance:Organization / finance:Person
- Fineract Loan -> finance:Loan
- Fineract Savings Account -> finance:Account
- Fineract GL Account -> finance:Asset / finance:Liability / finance:Equity
- Fineract Transaction -> finance:FinancialTransaction
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional
from urllib.parse import urljoin

from rdflib import URIRef

from ..graph.knowledge_graph import FinanceKnowledgeGraph
from ..ontology.namespaces import FINERACT

logger = logging.getLogger(__name__)


class FineractConfig:
    """Configuration for Fineract API connection."""
    
    def __init__(
        self,
        base_url: str = "https://demo.fineract.dev/fineract-provider/api/v1",
        tenant_id: str = "default",
        username: string = "mifos",
        password: string = "password",
        page_size: int = 200,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.tenant_id = tenant_id
        self.username = username
        self.password = password
        self.page_size = page_size


class FineractIntegration:
    """
    Integrates Apache Fineract data into the Finance Knowledge Graph.
    
    Supports:
    - Client data (individuals and organizations)
    - Loan portfolio (individual and group loans)
    - Savings accounts
    - General ledger / accounting entries
    - Financial reports (balance sheet, income statement)
    
    Usage:
        kg = FinanceKnowledgeGraph()
        fin = FineractIntegration(kg)
        
        # Load from live API
        fin.load_clients(base_url="https://your-fineract-server/api/v1")
        
        # Or load from offline data (JSON exports)
        fin.load_clients_from_data(client_list)
    """

    def __init__(self, kg: FinanceKnowledgeGraph) -> None:
        self.kg = kg
        self.config: Optional[FineractConfig] = None
        self._client_map: dict[int, URIRef] = {}  # Fineract ID -> KG URI
        self._loan_map: dict[int, URIRef] = {}

    def load_clients_from_data(self, clients: list[dict[str, Any]]) -> list[URIRef]:
        """
        Load Fineract client data from a list of client dicts.
        
        Expected dict keys from Fineract API:
        - id: int
        - accountNo: str
        - firstname: str (individual) or fullname (organization)
        - lastname: str (individual)
        - officeName: str
        - status: dict with 'code' (e.g., "clientStatusType.active")
        - active: bool
        - activationDate: list [year, month, day]
        - submittedOnDate: list [year, month, day]
        
        Args:
            clients: List of client dicts from Fineract
            
        Returns:
            List of entity URIs created in the KG
        """
        uris: list[URIRef] = []
        for client in clients:
            uri = self._map_client_to_entity(client)
            uris.append(uri)
        logger.info("Loaded %d Fineract clients into KG", len(uris))
        return uris

    def load_loans_from_data(self, loans: list[dict[str, Any]]) -> list[URIRef]:
        """
        Load Fineract loan data from a list of loan dicts.
        
        Expected dict keys from Fineract API:
        - id: int
        - accountNo: str
        - status: dict with 'code' (e.g., "loanStatusType.active")
        - clientId: int (links to a client)
        - clientName: str
        - loanProductName: str
        - principal: float
        - approvedPrincipal: float
        - numberOfRepayments: int
        - interestRatePerPeriod: float
        - termPrincipalFrequencyType: dict
        - timeline: dict with expectedDisbursementDate
        
        Args:
            loans: List of loan dicts from Fineract
            
        Returns:
            List of entity URIs created in the KG
        """
        uris: list[URIRef] = []
        for loan in loans:
            uri = self._map_loan_to_entity(loan)
            uris.append(uri)
        logger.info("Loaded %d Fineract loans into KG", len(uris))
        return uris

    def load_savings_from_data(self, accounts: list[dict[str, Any]]) -> list[URIRef]:
        """
        Load Fineract savings account data.
        
        Expected dict keys:
        - id: int
        - accountNo: str
        - clientId: int
        - clientName: str
        - savingsProductName: str
        - currency: dict with 'code'
        - accountBalance: float
        - status: dict with 'code'
        
        Args:
            accounts: List of savings account dicts
            
        Returns:
            List of entity URIs created
        """
        uris: list[URIRef] = []
        for acc in accounts:
            uri = self._map_savings_to_entity(acc)
            uris.append(uri)
        logger.info("Loaded %d Fineract savings accounts into KG", len(uris))
        return uris

    def load_gl_accounts_from_data(self, accounts: list[dict[str, Any]]) -> list[URIRef]:
        """
        Load Fineract GL (General Ledger) accounts.
        
        Expected dict keys:
        - id: int
        - name: str
        - glCode: str
        - type: dict with 'code' (e.g., "accountType.asset")
        - usage: dict with 'code' ("accountUsage.detail")
        - manualEntriesAllowed: bool
        - disabled: bool
        
        Args:
            accounts: List of GL account dicts
            
        Returns:
            List of entity URIs created
        """
        uris: list[URIRef] = []
        for acc in accounts:
            uri = self._map_gl_account_to_entity(acc)
            uris.append(uri)
        logger.info("Loaded %d Fineract GL accounts into KG", len(uris))
        return uris

    def load_loan_transactions_from_data(
        self, transactions: list[dict[str, Any]]
    ) -> list[URIRef]:
        """
        Load Fineract loan transactions (repayments, disbursements).
        
        Expected dict keys:
        - id: int
        - type: dict with 'code' ("loanTransactionType.repayment")
        - date: list [year, month, day]
        - amount: float
        - principalPortion: float
        - interestPortion: float
        - loanId: int (links to a loan)
        
        Args:
            transactions: List of transaction dicts
            
        Returns:
            List of entity URIs created
        """
        uris: list[URIRef] = []
        for tx in transactions:
            uri = self._map_transaction_to_entity(tx)
            uris.append(uri)
        logger.info("Loaded %d Fineract transactions into KG", len(uris))
        return uris

    # ---- Mapping Methods ----

    def _map_client_to_entity(self, client: dict[str, Any]) -> URIRef:
        """Map a Fineract client to a KG entity."""
        client_id = client.get("id", 0)
        firstname = client.get("firstname", "")
        lastname = client.get("lastname", "")
        fullname = client.get("fullname", "")
        
        if fullname:
            label = fullname
        elif firstname or lastname:
            label = f"{firstname} {lastname}".strip()
        else:
            label = client.get("accountNo", f"Client_{client_id}")
        
        # Determine entity type
        if fullname:
            entity_type = "Organization"
        elif firstname and lastname:
            entity_type = "Person"
        else:
            entity_type = "LegalEntity"
        
        properties: dict[str, Any] = {}
        if client.get("accountNo"):
            properties["accountNo"] = client["accountNo"]
        if client.get("officeName"):
            properties["officeName"] = client["officeName"]
        if client.get("status", {}).get("value"):
            properties["status"] = client["status"]["value"]
        if client.get("activationDate"):
            properties["activationDate"] = self._parse_fineract_date(client["activationDate"])
        
        uri = self.kg.add_entity(
            label=label,
            entity_type=entity_type,
            properties=properties,
            namespace=FINERACT,
            source="fineract",
            timestamp=datetime.now(),
        )
        
        self._client_map[client_id] = uri
        return uri

    def _map_loan_to_entity(self, loan: dict[str, Any]) -> URIRef:
        """Map a Fineract loan to a KG entity."""
        loan_id = loan.get("id", 0)
        label = f"Loan {loan.get('accountNo', loan_id)}"
        
        properties: dict[str, Any] = {}
        if loan.get("principal"):
            properties["hasLoanAmount"] = loan["principal"]
        if loan.get("numberOfRepayments"):
            properties["numberOfRepayments"] = loan["numberOfRepayments"]
        if loan.get("interestRatePerPeriod"):
            properties["hasInterestRate"] = loan["interestRatePerPeriod"]
        if loan.get("loanProductName"):
            properties["loanProduct"] = loan["loanProductName"]
        if loan.get("status", {}).get("value"):
            properties["status"] = loan["status"]["value"]
        if loan.get("timeline", {}).get("expectedDisbursementDate"):
            properties["expectedDisbursementDate"] = self._parse_fineract_date(
                loan["timeline"]["expectedDisbursementDate"]
            )
        
        uri = self.kg.add_entity(
            label=label,
            entity_type="Loan",
            properties=properties,
            namespace=FINERACT,
            source="fineract",
            timestamp=datetime.now(),
        )
        
        self._loan_map[loan_id] = uri
        
        # Link loan to client if available
        client_id = loan.get("clientId")
        if client_id and client_id in self._client_map:
            self.kg.add_relation(
                self._client_map[client_id],
                uri,
                "hasLoan",
                source_name="fineract",
            )
        
        return uri

    def _map_savings_to_entity(self, acc: dict[str, Any]) -> URIRef:
        """Map a Fineract savings account to a KG entity."""
        acc_id = acc.get("id", 0)
        label = f"Savings {acc.get('accountNo', acc_id)}"
        
        properties: dict[str, Any] = {}
        if acc.get("accountBalance"):
            properties["balance"] = acc["accountBalance"]
        if acc.get("currency", {}).get("code"):
            properties["currency"] = acc["currency"]["code"]
        if acc.get("savingsProductName"):
            properties["productName"] = acc["savingsProductName"]
        if acc.get("status", {}).get("value"):
            properties["status"] = acc["status"]["value"]
        
        uri = self.kg.add_entity(
            label=label,
            entity_type="Account",
            properties=properties,
            namespace=FINERACT,
            source="fineract",
            timestamp=datetime.now(),
        )
        
        # Link to client
        client_id = acc.get("clientId")
        if client_id and client_id in self._client_map:
            self.kg.add_relation(
                self._client_map[client_id],
                uri,
                "hasAccount",
                source_name="fineract",
            )
        
        return uri

    def _map_gl_account_to_entity(self, acc: dict[str, Any]) -> URIRef:
        """Map a Fineract GL account to a KG entity."""
        acc_id = acc.get("id", 0)
        name = acc.get("name", f"GL_Account_{acc_id}")
        
        # Map Fineract account types to FIBO types
        type_code = acc.get("type", {}).get("code", "")
        type_mapping = {
            "accountType.asset": "Asset",
            "accountType.liability": "Liability",
            "accountType.equity": "Equity",
            "accountType.income": "Revenue",
            "accountType.expense": "Expense",
        }
        entity_type = type_mapping.get(type_code, "Asset")
        
        properties: dict[str, Any] = {}
        if acc.get("glCode"):
            properties["glCode"] = acc["glCode"]
        if acc.get("usage", {}).get("code"):
            properties["usage"] = acc["usage"]["code"]
        
        uri = self.kg.add_entity(
            label=name,
            entity_type=entity_type,
            properties=properties,
            namespace=FINERACT,
            source="fineract",
            timestamp=datetime.now(),
        )
        return uri

    def _map_transaction_to_entity(self, tx: dict[str, Any]) -> URIRef:
        """Map a Fineract transaction to a KG entity."""
        tx_id = tx.get("id", 0)
        label = f"Transaction {tx_id}"
        
        properties: dict[str, Any] = {}
        if tx.get("amount"):
            properties["amount"] = tx["amount"]
        if tx.get("principalPortion"):
            properties["principalPortion"] = tx["principalPortion"]
        if tx.get("interestPortion"):
            properties["interestPortion"] = tx["interestPortion"]
        if tx.get("type", {}).get("value"):
            properties["transactionType"] = tx["type"]["value"]
        if tx.get("date"):
            properties["date"] = self._parse_fineract_date(tx["date"])
        
        uri = self.kg.add_entity(
            label=label,
            entity_type="FinancialTransaction",
            properties=properties,
            namespace=FINERACT,
            source="fineract",
            timestamp=datetime.now(),
        )
        
        # Link to loan
        loan_id = tx.get("loanId")
        if loan_id and loan_id in self._loan_map:
            self.kg.add_relation(
                uri,
                self._loan_map[loan_id],
                "appliesToLoan",
                source_name="fineract",
            )
        
        return uri

    @staticmethod
    def _parse_fineract_date(date_val: Any) -> Optional[str]:
        """Parse Fineract date format [year, month, day] to ISO string."""
        if isinstance(date_val, list) and len(date_val) >= 3:
            try:
                return f"{date_val[0]:04d}-{date_val[1]:02d}-{date_val[2]:02d}"
            except (ValueError, TypeError):
                return None
        elif isinstance(date_val, str):
            return date_val
        return None

    # ---- Sample Data Generators (for PoC) ----

    @staticmethod
    def generate_sample_clients() -> list[dict[str, Any]]:
        """Generate sample Fineract client data for testing."""
        return [
            {
                "id": 1,
                "accountNode": "000000001",
                "firstname": "John",
                "lastname": "Doe",
                "officeName": "Head Office",
                "status": {"code": "clientStatusType.active", "value": "Active"},
                "active": True,
                "activationDate": [2020, 1, 15],
                "submittedOnDate": [2020, 1, 10],
            },
            {
                "id": 2,
                "accountNo": "000000002",
                "fullname": "Acme Microfinance",
                "officeName": "Head Office",
                "status": {"code": "clientStatusType.active", "value": "Active"},
                "active": True,
                "activationDate": [2019, 6, 1],
                "submittedOnDate": [2019, 5, 28],
            },
            {
                "id": 3,
                "accountNo": "000000003",
                "firstname": "Jane",
                "lastname": "Smith",
                "officeName": "Branch Office",
                "status": {"code": "clientStatusType.active", "value": "Active"},
                "active": True,
                "activationDate": [2021, 3, 20],
                "submittedOnDate": [2021, 3, 15],
            },
        ]

    @staticmethod
    def generate_sample_loans() -> list[dict[str, Any]]:
        """Generate sample Fineract loan data for testing."""
        return [
            {
                "id": 1,
                "accountNo": "000000000000001",
                "status": {"code": "loanStatusType.active", "value": "Active"},
                "clientId": 1,
                "clientName": "John Doe",
                "loanProductName": "Small Business Loan",
                "principal": 5000.00,
                "approvedPrincipal": 5000.00,
                "numberOfRepayments": 12,
                "interestRatePerPeriod": 1.5,
                "termPrincipalFrequencyType": {"code": "termFrequency.periodFrequencyType.months"},
                "timeline": {"expectedDisbursementDate": [2023, 2, 1]},
            },
            {
                "id": 2,
                "accountNo": "000000000000002",
                "status": {"code": "loanStatusType.active", "value": "Active"},
                "clientId": 2,
                "clientName": "Acme Microfinance",
                "loanProductName": "Group Loan",
                "principal": 25000.00,
                "approvedPrincipal": 25000.00,
                "numberOfRepayments": 24,
                "interestRatePerPeriod": 1.0,
                "termPrincipalFrequencyType": {"code": "termFrequency.periodFrequencyType.months"},
                "timeline": {"expectedDisbursementDate": [2023, 1, 15]},
            },
        ]

    @staticmethod
    def generate_sample_savings() -> list[dict[str, Any]]:
        """Generate sample Fineract savings data for testing."""
        return [
            {
                "id": 1,
                "accountNo": "000000000000001",
                "clientId": 1,
                "clientName": "John Doe",
                "savingsProductName": "Regular Savings",
                "currency": {"code": "USD"},
                "accountBalance": 1250.50,
                "status": {"code": "savingsAccountStatusType.active", "value": "Active"},
            },
            {
                "id": 2,
                "accountNo": "000000000000002",
                "clientId": 3,
                "clientName": "Jane Smith",
                "savingsProductName": "Fixed Deposit",
                "currency": {"code": "USD"},
                "accountBalance": 5000.00,
                "status": {"code": "savingsAccountStatusType.active", "value": "Active"},
            },
        ]

    @staticmethod
    def generate_sample_gl_accounts() -> list[dict[str, Any]]:
        """Generate sample Fineract GL account data for testing."""
        return [
            {
                "id": 1,
                "name": "Cash and Balances",
                "glCode": "10000",
                "type": {"code": "accountType.asset"},
                "usage": {"code": "accountUsage.detail"},
                "manualEntriesAllowed": True,
                "disabled": False,
            },
            {
                "id": 2,
                "name": "Loan Portfolio",
                "glCode": "20000",
                "type": {"code": "accountType.asset"},
                "usage": {"code": "accountUsage.detail"},
                "manualEntriesAllowed": True,
                "disabled": False,
            },
            {
                "id": 3,
                "name": "Customer Deposits",
                "glCode": "30000",
                "type": {"code": "accountType.liability"},
                "usage": {"code": "accountUsage.detail"},
                "manualEntriesAllowed": True,
                "disabled": False,
            },
            {
                "id": 4,
                "name": "Retained Earnings",
                "glCode": "40000",
                "type": {"code": "accountType.equity"},
                "usage": {"code": "accountUsage.detail"},
                "manualEntriesAllowed": True,
                "disabled": False,
            },
            {
                "id": 5,
                "name": "Interest Income",
                "glCode": "50000",
                "type": {"code": "accountType.income"},
                "usage": {"code": "accountUsage.detail"},
                "manualEntriesAllowed": True,
                "disabled": False,
            },
        ]

    @staticmethod
    def generate_sample_transactions() -> list[dict[str, Any]]:
        """Generate sample Fineract transaction data for testing."""
        return [
            {
                "id": 1,
                "type": {"code": "loanTransactionType.repayment", "value": "Repayment"},
                "date": [2023, 3, 1],
                "amount": 450.00,
                "principalPortion": 425.00,
                "interestPortion": 25.00,
                "loanId": 1,
            },
            {
                "id": 2,
                "type": {"code": "loanTransactionType.repayment", "value": "Repayment"},
                "date": [2023, 4, 1],
                "amount": 450.00,
                "principalPortion": 428.00,
                "interestPortion": 22.00,
                "loanId": 1,
            },
        ]
