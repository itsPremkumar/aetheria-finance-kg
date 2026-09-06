"""
integrations/sec_edgar.py - SEC EDGAR filing integration.

Parses SEC EDGAR filings (10-K, 10-Q, 8-K) and maps them into the
Finance Knowledge Graph.

SEC EDGAR Reference:
- 10-K: Annual report (comprehensive business and financial overview)
- 10-Q: Quarterly report (quarterly financial statements)
- 8-K: Current report (material events)
- 13F: Institutional holdings
- Form 4: Insider trading
- S-1: IPO registration

Data Model Mapping:
- SEC Filer -> finance:Corporation
- SEC Filing -> finance:FinancialStatement / finance:CurrentReport
- SEC Item (e.g., Item 1A Risk Factors) -> finance:RiskDisclosure
- SEC Financial Data -> finance:FinancialMetric
- SEC Executive -> finance:Executive
- SEC Insider Transaction -> finance:InsiderTransaction
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Optional

from rdflib import URIRef

from ..graph.knowledge_graph import FinanceKnowledgeGraph
from ..ontology.namespaces import SEC as SEC_NS

logger = logging.getLogger(__name__)


class SECEDGARIntegration:
    """
    Integrates SEC EDGAR filing data into the Finance Knowledge Graph.
    
    Supports:
    - 10-K annual reports (business overview, financials, risks)
    - 10-Q quarterly reports (quarterly financials)
    - 8-K current reports (material events)
    - 13F institutional holdings
    - Form 4 insider trading
    - Executive compensation data
    
    Usage:
        kg = FinanceKnowledgeGraph()
        sec = SECEDGARIntegration(kg)
        
        # Load from parsed filing data
        sec.load_10k_from_data(filing_dict)
        
        # Or load from offline data
        sec.load_filer_from_data(filer_dict)
    """

    # 10-K section items
    TEN_K_ITEMS = {
        "item_1": "Business",
        "item_1a": "Risk Factors",
        "item_1b": "Unresolved Staff Comments",
        "item_2": "Properties",
        "item_3": "Legal Proceedings",
        "item_4": "Mine Safety Disclosures",
        "item_5": "Market for Registrant's Common Equity",
        "item_6": "Selected Financial Data",
        "item_7": "MD&A",
        "item_7a": "Quantitative and Qualitative Disclosures",
        "item_8": "Financial Statements",
        "item_9": "Changes in Disagreements with Accountants",
        "item_9a": "Controls and Procedures",
        "item_9b": "Other Information",
    }

    # 10-Q section items
    TEN_Q_ITEMS = {
        "item_1": "Financial Statements",
        "item_2": "MD&A",
        "item_3": "Quantitative and Qualitative Disclosures",
        "item_4": "Controls and Procedures",
        "item_5": "Other Information",
        "item_6": "Exhibits",
    }

    # 8-K event items
    EIGHT_K_ITEMS = {
        "item_1_1": "Entry into a Material Definitive Agreement",
        "item_1_2": "Termination of a Material Definitive Agreement",
        "item_2_1": "Acquisition or Disposition of Assets",
        "item_2_2": "Results of Operations and Financial Condition",
        "item_2_3": "Creation of a Direct Financial Obligation",
        "item_4_1": "Changes in Registrant's Certifying Accountant",
        "item_5_1": "Changes in Control of Registrant",
        "item_5_2": "Departure of Directors or Officers",
        "item_5_3": "Amendments to Articles of Incorporation",
        "item_6_1": "Submission of Matters to a Vote",
        "item_7_1": "Regulation FD Disclosure",
        "item_8_1": "Other Events",
        "item_9_1": "Financial Statements and Exhibits",
    }

    def __init__(self, kg: FinanceKnowledgeGraph) -> None:
        self.kg = kg
        self._cik_map: dict[str, URIRef] = {}  # CIK -> KG URI

    def load_filer_from_data(self, filer_data: dict[str, Any]) -> URIRef:
        """
        Load SEC filer (company) data from a dict.
        
        Expected dict keys:
        - cik: str (Central Index Key, e.g., "0000320193")
        - name: str (e.g., "Apple Inc.")
        - ticker: str (e.g., "AAPL")
        - sic: str (Standard Industrial Classification code)
        - state: str
        - fiscal_year_end: str (MMDD)
        - business_address: dict
        - mailing_address: dict
        
        Args:
            filer_data: Filer data dict
            
        Returns:
            Entity URI created in the KG
        """
        return self._map_filer_to_entity(filer_data)

    def load_10k_from_data(self, filing_data: dict[str, Any]) -> URIRef:
        """
        Load 10-K annual report data from a dict.
        
        Expected dict keys:
        - cik: str
        - company_name: str
        - form_type: str ("10-K")
        - filing_date: str (ISO date)
        - fiscal_year_end: str (ISO date)
        - items: dict[str, str] (item number -> text content)
        - financial_data: dict[str, float] (metric name -> value)
        
        Args:
            filing_data: 10-K filing data dict
            
        Returns:
            Entity URI created in the KG
        """
        return self._map_10k_to_entity(filing_data)

    def load_10q_from_data(self, filing_data: dict[str, Any]) -> URIRef:
        """
        Load 10-Q quarterly report data from a dict.
        
        Expected dict keys:
        - cik: str
        - company_name: str
        - form_type: str ("10-Q")
        - filing_date: str (ISO date)
        - fiscal_quarter: str (e.g., "Q1", "Q2")
        - fiscal_year: int
        - items: dict[str, str]
        - financial_data: dict[str, float]
        
        Args:
            filing_data: 10-Q filing data dict
            
        Returns:
            Entity URI created in the KG
        """
        return self._map_10q_to_entity(filing_data)

    def load_8k_from_data(self, filing_data: dict[str, Any]) -> URIRef:
        """
        Load 8-K current report data from a dict.
        
        Expected dict keys:
        - cik: str
        - company_name: str
        - form_type: str ("8-K")
        - filing_date: str (ISO date)
        - items: list[str] (e.g., ["item_2_1", "item_9_1"])
        - event_description: str
        
        Args:
            filing_data: 8-K filing data dict
            
        Returns:
            Entity URI created in the KG
        """
        return self._map_8k_to_entity(filing_data)

    def load_insider_transaction_from_data(
        self, transaction_data: dict[str, Any]
    ) -> URIRef:
        """
        Load Form 4 insider transaction data from a dict.
        
        Expected dict keys:
        - cik: str
        - company_name: str
        - owner_name: str
        - owner_title: str
        - transaction_date: str (ISO date)
        - transaction_type: str ("P" for purchase, "S" for sale)
        - shares: float
        - price: float
        - total_value: float
        
        Args:
            transaction_data: Insider transaction data dict
            
        Returns:
            Entity URI created in the KG
        """
        return self._map_insider_transaction_to_entity(transaction_data)

    def load_executive_compensation_from_data(
        self, comp_data: dict[str, Any]
    ) -> URIRef:
        """
        Load executive compensation data from a dict.
        
        Expected dict keys:
        - cik: str
        - company_name: str
        - name: str
        - title: str
        - year: int
        - salary: float
        - bonus: float
        - stock_awards: float
        - total_compensation: float
        
        Args:
            comp_data: Executive compensation data dict
            
        Returns:
            Entity URI created in the KG
        """
        return self._map_executive_compensation_to_entity(comp_data)

    # ---- Mapping Methods ----

    def _map_filer_to_entity(self, data: dict[str, Any]) -> URIRef:
        """Map SEC filer data to a KG entity."""
        cik = data.get("cik", "")
        name = data.get("name", f"CIK_{cik}")
        
        properties: dict[str, Any] = {}
        if cik:
            properties["cik"] = cik
        if data.get("ticker"):
            properties["hasTicker"] = data["ticker"]
        if data.get("sic"):
            properties["sicCode"] = data["sic"]
        if data.get("state"):
            properties["state"] = data["state"]
        if data.get("fiscal_year_end"):
            properties["fiscalYearEnd"] = data["fiscal_year_end"]
        
        uri = self.kg.add_entity(
            label=name,
            entity_type="Corporation",
            properties=properties,
            namespace=SEC_NS,
            source="sec_edgar",
            timestamp=datetime.now(),
        )
        
        if cik:
            self._cik_map[cik] = uri
        return uri

    def _map_10k_to_entity(self, data: dict[str, Any]) -> URIRef:
        """Map 10-K filing data to a KG entity."""
        cik = data.get("cik", "")
        company_name = data.get("company_name", "Unknown")
        filing_date = data.get("filing_date", "")
        fiscal_year_end = data.get("fiscal_year_end", "")
        
        label = f"{company_name} 10-K {fiscal_year_end}"
        
        properties: dict[str, Any] = {}
        if data.get("filing_date"):
            properties["filingDate"] = data["filing_date"]
        if data.get("fiscal_year_end"):
            properties["fiscalYearEnd"] = data["fiscal_year_end"]
        
        # Add financial data
        for metric, value in data.get("financial_data", {}).items():
            safe_key = metric.lower().replace(" ", "_")[:40]
            properties[safe_key] = value
        
        uri = self.kg.add_entity(
            label=label,
            entity_type="FinancialStatement",
            properties=properties,
            namespace=SEC_NS,
            source="sec_edgar",
            timestamp=datetime.now(),
        )
        
        # Link to company
        if cik in self._cik_map:
            self.kg.add_relation(
                self._cik_map[cik],
                uri,
                "hasFinancialStatement",
                source_name="sec_edgar",
            )
        
        # Add risk disclosures
        risk_text = data.get("items", {}).get("item_1a", "")
        if risk_text:
            risk_uri = self._add_risk_disclosure(risk_text, uri, company_name, filing_date)
            self.kg.add_relation(
                uri, risk_uri, "containsRiskDisclosure", source_name="sec_edgar"
            )
        
        return uri

    def _map_10q_to_entity(self, data: dict[str, Any]) -> URIRef:
        """Map 10-Q filing data to a KG entity."""
        cik = data.get("cik", "")
        company_name = data.get("company_name", "Unknown")
        fiscal_quarter = data.get("fiscal_quarter", "")
        fiscal_year = data.get("fiscal_year", "")
        
        label = f"{company_name} 10-Q {fiscal_quarter} {fiscal_year}"
        
        properties: dict[str, Any] = {}
        if data.get("filing_date"):
            properties["filingDate"] = data["filing_date"]
        if data.get("fiscal_quarter"):
            properties["fiscalQuarter"] = data["fiscal_quarter"]
        if data.get("fiscal_year"):
            properties["fiscalYear"] = data["fiscal_year"]
        
        for metric, value in data.get("financial_data", {}).items():
            safe_key = metric.lower().replace(" ", "_")[:40]
            properties[safe_key] = value
        
        uri = self.kg.add_entity(
            label=label,
            entity_type="FinancialStatement",
            properties=properties,
            namespace=SEC_NS,
            source="sec_edgar",
            timestamp=datetime.now(),
        )
        
        if cik in self._cik_map:
            self.kg.add_relation(
                self._cik_map[cik],
                uri,
                "hasFinancialStatement",
                source_name="sec_edgar",
            )
        
        return uri

    def _map_8k_to_entity(self, data: dict[str, Any]) -> URIRef:
        """Map 8-K filing data to a KG entity."""
        cik = data.get("cik", "")
        company_name = data.get("company_name", "Unknown")
        filing_date = data.get("filing_date", "")
        
        label = f"{company_name} 8-K {filing_date}"
        
        properties: dict[str, Any] = {}
        if data.get("filing_date"):
            properties["filingDate"] = data["filing_date"]
        if data.get("event_description"):
            properties["eventDescription"] = data["event_description"]
        
        # Add event items
        for item in data.get("items", []):
            item_desc = self.EIGHT_K_ITEMS.get(item, item)
            properties[f"event_{item}"] = item_desc
        
        uri = self.kg.add_entity(
            label=label,
            entity_type="CurrentReport",
            properties=properties,
            namespace=SEC_NS,
            source="sec_edgar",
            timestamp=datetime.now(),
        )
        
        if cik in self._cik_map:
            self.kg.add_relation(
                self._cik_map[cik],
                uri,
                "filedCurrentReport",
                source_name="sec_edgar",
            )
        
        return uri

    def _map_insider_transaction_to_entity(self, data: dict[str, Any]) -> URIRef:
        """Map Form 4 insider transaction to a KG entity."""
        owner_name = data.get("owner_name", "Unknown")
        transaction_date = data.get("transaction_date", "")
        transaction_type = data.get("transaction_type", "")
        
        type_label = "Purchase" if transaction_type == "P" else "Sale"
        label = f"Insider {type_label} - {owner_name} {transaction_date}"
        
        properties: dict[str, Any] = {}
        if data.get("owner_title"):
            properties["ownerTitle"] = data["owner_title"]
        if data.get("transaction_date"):
            properties["transactionDate"] = data["transaction_date"]
        if data.get("transaction_type"):
            properties["transactionType"] = transaction_type
        if data.get("shares"):
            properties["shares"] = data["shares"]
        if data.get("price"):
            properties["price"] = data["price"]
        if data.get("total_value"):
            properties["totalValue"] = data["total_value"]
        
        uri = self.kg.add_entity(
            label=label,
            entity_type="InsiderTransaction",
            properties=properties,
            namespace=SEC_NS,
            source="sec_edgar",
            timestamp=datetime.now(),
        )
        
        # Link to company
        cik = data.get("cik", "")
        if cik in self._cik_map:
            self.kg.add_relation(
                uri,
                self._cik_map[cik],
                "involvesCompany",
                source_name="sec_edgar",
            )
        
        return uri

    def _map_executive_compensation_to_entity(self, data: dict[str, Any]) -> URIRef:
        """Map executive compensation data to a KG entity."""
        name = data.get("name", "Unknown")
        year = data.get("year", "")
        title = data.get("title", "")
        
        label = f"Compensation - {name} ({title}) {year}"
        
        properties: dict[str, Any] = {}
        if data.get("title"):
            properties["title"] = data["title"]
        if data.get("year"):
            properties["year"] = data["year"]
        if data.get("salary"):
            properties["salary"] = data["salary"]
        if data.get("bonus"):
            properties["bonus"] = data["bonus"]
        if data.get("stock_awards"):
            properties["stockAwards"] = data["stock_awards"]
        if data.get("total_compensation"):
            properties["totalCompensation"] = data["total_compensation"]
        
        uri = self.kg.add_entity(
            label=label,
            entity_type="ExecutiveCompensation",
            properties=properties,
            namespace=SEC_NS,
            source="sec_edgar",
            timestamp=datetime.now(),
        )
        
        # Link to company
        cik = data.get("cik", "")
        if cik in self._cik_map:
            self.kg.add_relation(
                uri,
                self._cik_map[cik],
                "compensatedBy",
                source_name="sec_edgar",
            )
        
        return uri

    def _add_risk_disclosure(
        self, text: str, filing_uri: URIRef, company_name: str, filing_date: str
    ) -> URIRef:
        """Add a risk disclosure entity from 10-K Item 1A."""
        label = f"Risk Disclosure - {company_name} {filing_date}"
        
        # Extract key risk phrases
        risk_phrases = self._extract_risk_phrases(text)
        
        properties: dict[str, Any] = {
            "riskText": text[:5000],  # Truncate for storage
            "riskCount": len(risk_phrases),
        }
        for i, phrase in enumerate(risk_phrases[:10]):
            properties[f"risk_{i+1}"] = phrase[:200]
        
        return self.kg.add_entity(
            label=label,
            entity_type="RiskDisclosure",
            properties=properties,
            namespace=SEC_NS,
            source="sec_edgar",
            timestamp=datetime.now(),
        )

    @staticmethod
    def _extract_risk_phrases(text: str) -> list[str]:
        """Extract key risk phrases from risk disclosure text."""
        # Simple extraction: split by periods, filter for risk-related sentences
        sentences = re.split(r'[.!?]+', text)
        risk_keywords = [
            "risk", "uncertain", "may", "could", "adverse", "negative",
            "decline", "loss", "impairment", "litigation", "regulatory",
            "competition", "market", "economic", "financial",
        ]
        risk_phrases: list[str] = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and any(kw in sentence.lower() for kw in risk_keywords):
                risk_phrases.append(sentence)
        return risk_phrases[:20]

    # ---- Sample Data Generators (for PoC) ----

    @staticmethod
    def generate_sample_filers() -> list[dict[str, Any]]:
        """Generate sample SEC filer data for testing."""
        return [
            {
                "cik": "0000320193",
                "name": "Apple Inc.",
                "ticker": "AAPL",
                "sic": "3571",
                "state": "CA",
                "fiscal_year_end": "0930",
                "business_address": {
                    "street": "One Apple Park Way",
                    "city": "Cupertino",
                    "state": "CA",
                    "zip": "95014",
                },
            },
            {
                "cik": "0000789019",
                "name": "Microsoft Corporation",
                "ticker": "MSFT",
                "sic": "7372",
                "state": "WA",
                "fiscal_year_end": "0630",
                "business_address": {
                    "street": "One Microsoft Way",
                    "city": "Redmond",
                    "state": "WA",
                    "zip": "98052",
                },
            },
        ]

    @staticmethod
    def generate_sample_10k() -> dict[str, Any]:
        """Generate sample 10-K filing data for testing."""
        return {
            "cik": "0000320193",
            "company_name": "Apple Inc.",
            "form_type": "10-K",
            "filing_date": "2023-11-03",
            "fiscal_year_end": "2023-09-30",
            "items": {
                "item_1": "Apple Inc. designs, manufactures and markets smartphones, personal computers, tablets, wearables and accessories...",
                "item_1a": "The Company's business, reputation, results of operations, financial condition and stock price can be affected by a number of factors, whether currently known or unknown...",
                "item_7": "Management's Discussion and Analysis of Financial Condition and Results of Operations...",
                "item_8": "The information required by this Item 1 is incorporated herein by reference to the Consolidated Financial Statements...",
            },
            "financial_data": {
                "Total Net Sales": 383285000000,
                "Net Income": 96995000000,
                "Total Assets": 352583000000,
                "Total Liabilities": 290437000000,
                "Total Equity": 62146000000,
                "Earnings Per Share": 6.16,
                "Research and Development Expense": 29715000000,
            },
        }

    @staticmethod
    def generate_sample_10q() -> dict[str, Any]:
        """Generate sample 10-Q filing data for testing."""
        return {
            "cik": "0000320193",
            "company_name": "Apple Inc.",
            "form_type": "10-Q",
            "filing_date": "2024-02-01",
            "fiscal_quarter": "Q1",
            "fiscal_year": 2024,
            "items": {
                "item_1": "The condensed consolidated financial statements of Apple Inc. included herein have been prepared, without audit...",
                "item_2": "Management's Discussion and Analysis of Financial Condition and Results of Operations...",
            },
            "financial_data": {
                "Net Sales": 119575000000,
                "Net Income": 33916000000,
                "Earnings Per Share": 2.18,
            },
        }

    @staticmethod
    def generate_sample_8k() -> dict[str, Any]:
        """Generate sample 8-K filing data for testing."""
        return {
            "cik": "0000320193",
            "company_name": "Apple Inc.",
            "form_type": "8-K",
            "filing_date": "2024-01-10",
            "items": ["item_2_2", "item_7_1", "item_9_1"],
            "event_description": "Apple Inc. issued a press release announcing financial results for its fiscal 2024 first quarter ended December 30, 2023.",
        }

    @staticmethod
    def generate_sample_insider_transactions() -> list[dict[str, Any]]:
        """Generate sample insider transaction data for testing."""
        return [
            {
                "cik": "0000320193",
                "company_name": "Apple Inc.",
                "owner_name": "Tim Cook",
                "owner_title": "Chief Executive Officer",
                "transaction_date": "2023-10-15",
                "transaction_type": "S",
                "shares": 511000,
                "price": 175.50,
                "total_value": 89680500,
            },
            {
                "cik": "0000320193",
                "company_name": "Apple Inc.",
                "owner_name": "Luca Maestri",
                "owner_title": "Chief Financial Officer",
                "transaction_date": "2023-11-01",
                "transaction_type": "S",
                "shares": 25000,
                "price": 178.00,
                "total_value": 4450000,
            },
        ]

    @staticmethod
    def generate_sample_executive_compensation() -> list[dict[str, Any]]:
        """Generate sample executive compensation data for testing."""
        return [
            {
                "cik": "0000320193",
                "company_name": "Apple Inc.",
                "name": "Tim Cook",
                "title": "Chief Executive Officer",
                "year": 2023,
                "salary": 3000000,
                "bonus": 12000000,
                "stock_awards": 45000000,
                "total_compensation": 60000000,
            },
            {
                "cik": "0000320193",
                "company_name": "Apple Inc.",
                "name": "Luca Maestri",
                "title": "Chief Financial Officer",
                "year": 2023,
                "salary": 1000000,
                "bonus": 5000000,
                "stock_awards": 20000000,
                "total_compensation": 26000000,
            },
        ]
