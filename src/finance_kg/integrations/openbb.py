"""
integrations/openbb.py - OpenBB Platform integration.

Maps OpenBB's financial market data into the Finance Knowledge Graph.

OpenBB Platform Reference:
- Python SDK: from openbb import obb
- Router pattern: obb.equity.price.historical(symbol="AAPL")
- Providers: yfinance, polygon, fmp, intrinio, benzinga, etc.
- Data types: equities, ETFs, indices, fundamentals, options, crypto

Data Model Mapping:
- OpenBB Equity -> finance:Stock / finance:EquitySecurity
- OpenBB ETF -> finance:ExchangeTradedFund
- OpenBB Index -> finance:MarketIndex
- OpenBB Company -> finance:Corporation
- OpenBB Financial Statement -> finance:FinancialStatement
- OpenBB Earnings -> finance:IncomeStatement
- OpenBB News -> finance:NewsArticle
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from rdflib import URIRef

from ..graph.knowledge_graph import FinanceKnowledgeGraph
from ..ontology.namespaces import OPENBB

logger = logging.getLogger(__name__)


class OpenBBIntegration:
    """
    Integrates OpenBB Platform data into the Finance Knowledge Graph.
    
    Supports:
    - Equity/Stock data (price, fundamentals, company info)
    - ETF data (holdings, sector weights, performance)
    - Index data (S&P 500, NASDAQ, etc.)
    - Financial statements (income, balance sheet, cash flow)
    - Earnings data (quarterly, annual)
    - News and sentiment data
    - Economic indicators
    
    Usage:
        kg = FinanceKnowledgeGraph()
        obb_int = OpenBBIntegration(kg)
        
        # Load from OpenBB SDK (requires openbb package)
        obb_int.load_equity_data("AAPL")
        
        # Or load from offline data (JSON exports)
        obb_int.load_equity_from_data(equity_dict)
    """

    def __init__(self, kg: FinanceKnowledgeGraph) -> None:
        self.kg = kg
        self._company_map: dict[str, URIRef] = {}  # ticker -> KG URI

    def load_equity_from_data(self, equity_data: dict[str, Any]) -> URIRef:
        """
        Load equity/stock data from a dict.
        
        Expected dict keys (from OpenBB equity.search or equity.profile):
        - symbol: str (e.g., "AAPL")
        - name: str (e.g., "Apple Inc.")
        - sector: str
        - industry: str
        - market_cap: float
        - exchange: str
        - cik: str
        - isin: str
        - cusip: str
        - description: str
        - website: str
        - employees: int
        - country: str
        
        Args:
            equity_data: Equity data dict
            
        Returns:
            Entity URI created in the KG
        """
        return self._map_equity_to_entity(equity_data)

    def load_etf_from_data(self, etf_data: dict[str, Any]) -> URIRef:
        """
        Load ETF data from a dict.
        
        Expected dict keys:
        - symbol: str (e.g., "SPY")
        - name: str (e.g., "SPDR S&P 500 ETF Trust")
        - aum: float (assets under management)
        - issuer: str
        - sector_weights: dict[str, float]
        - top_holdings: list[dict]
        
        Args:
            etf_data: ETF data dict
            
        Returns:
            Entity URI created in the KG
        """
        return self._map_etf_to_entity(etf_data)

    def load_index_from_data(self, index_data: dict[str, Any]) -> URIRef:
        """
        Load market index data from a dict.
        
        Expected dict keys:
        - symbol: str (e.g., "SPX")
        - name: str (e.g., "S&P 500")
        - exchange: str
        - currency: str
        - num_constituents: int
        
        Args:
            index_data: Index data dict
            
        Returns:
            Entity URI created in the KG
        """
        return self._map_index_to_entity(index_data)

    def load_financial_statement_from_data(
        self, statement_data: dict[str, Any]
    ) -> URIRef:
        """
        Load financial statement data from a dict.
        
        Expected dict keys:
        - ticker: str
        - statement_type: str ("income_statement", "balance_sheet", "cash_flow")
        - period: str ("annual", "quarterly")
        - fiscal_year: int
        - fiscal_period: str ("FY", "Q1", "Q2", "Q3", "Q4")
        - report_date: str (ISO date)
        - items: list[dict] with keys: label, value, unit
        
        Args:
            statement_data: Financial statement data dict
            
        Returns:
            Entity URI created in the KG
        """
        return self._map_financial_statement_to_entity(statement_data)

    def load_earnings_from_data(self, earnings_data: dict[str, Any]) -> URIRef:
        """
        Load earnings data from a dict.
        
        Expected dict keys:
        - ticker: str
        - report_date: str (ISO date)
        - fiscal_period: str
        - eps_actual: float
        - eps_estimate: float
        - revenue_actual: float
        - revenue_estimate: float
        
        Args:
            earnings_data: Earnings data dict
            
        Returns:
            Entity URI created in the KG
        """
        return self._map_earnings_to_entity(earnings_data)

    def load_news_from_data(self, news_data: dict[str, Any]) -> URIRef:
        """
        Load news article data from a dict.
        
        Expected dict keys:
        - title: str
        - source: str
        - date: str (ISO datetime)
        - url: str
        - summary: str
        - tickers: list[str]
        - sentiment: str ("positive", "negative", "neutral")
        
        Args:
            news_data: News data dict
            
        Returns:
            Entity URI created in the KG
        """
        return self._map_news_to_entity(news_data)

    def load_company_from_data(self, company_data: dict[str, Any]) -> URIRef:
        """
        Load company profile data from a dict.
        
        Expected dict keys:
        - ticker: str
        - name: str
        - sector: str
        - industry: str
        - market_cap: float
        - pe_ratio: float
        - dividend_yield: float
        - beta: float
        - eps: float
        - revenue: float
        - employees: int
        - country: str
        - exchange: str
        
        Args:
            company_data: Company data dict
            
        Returns:
            Entity URI created in the KG
        """
        return self._map_company_to_entity(company_data)

    # ---- Mapping Methods ----

    def _map_equity_to_entity(self, data: dict[str, Any]) -> URIRef:
        """Map OpenBB equity data to a KG entity."""
        symbol = data.get("symbol", "")
        name = data.get("name", symbol)
        
        properties: dict[str, Any] = {}
        if symbol:
            properties["hasTicker"] = symbol
        if data.get("isin"):
            properties["hasISIN"] = data["isin"]
        if data.get("cusip"):
            properties["hasCUSIP"] = data["cusip"]
        if data.get("sector"):
            properties["sector"] = data["sector"]
        if data.get("industry"):
            properties["industry"] = data["industry"]
        if data.get("market_cap"):
            properties["hasMarketCap"] = data["market_cap"]
        if data.get("exchange"):
            properties["exchange"] = data["exchange"]
        if data.get("cik"):
            properties["cik"] = data["cik"]
        if data.get("description"):
            properties["description"] = data["description"]
        if data.get("website"):
            properties["website"] = data["website"]
        if data.get("employees"):
            properties["hasEmployeeCount"] = data["employees"]
        if data.get("country"):
            properties["country"] = data["country"]
        
        uri = self.kg.add_entity(
            label=name,
            entity_type="Corporation",
            properties=properties,
            namespace=OPENBB,
            source="openbb",
            timestamp=datetime.now(),
        )
        
        if symbol:
            self._company_map[symbol] = uri
        return uri

    def _map_etf_to_entity(self, data: dict[str, Any]) -> URIRef:
        """Map OpenBB ETF data to a KG entity."""
        symbol = data.get("symbol", "")
        name = data.get("name", symbol)
        
        properties: dict[str, Any] = {}
        if symbol:
            properties["hasTicker"] = symbol
        if data.get("aum"):
            properties["aum"] = data["aum"]
        if data.get("issuer"):
            properties["issuer"] = data["issuer"]
        if data.get("sector_weights"):
            properties["sectorWeights"] = str(data["sector_weights"])
        
        uri = self.kg.add_entity(
            label=name,
            entity_type="ExchangeTradedFund",
            properties=properties,
            namespace=OPENBB,
            source="openbb",
            timestamp=datetime.now(),
        )
        
        # Link ETF holdings to companies
        for holding in data.get("top_holdings", []):
            ticker = holding.get("symbol", "")
            if ticker in self._company_map:
                self.kg.add_relation(
                    uri,
                    self._company_map[ticker],
                    "holdsStake",
                    properties={"weight": holding.get("weight", 0)},
                    source_name="openbb",
                )
        
        return uri

    def _map_index_to_entity(self, data: dict[str, Any]) -> URIRef:
        """Map OpenBB index data to a KG entity."""
        symbol = data.get("symbol", "")
        name = data.get("name", symbol)
        
        properties: dict[str, Any] = {}
        if symbol:
            properties["hasTicker"] = symbol
        if data.get("exchange"):
            properties["exchange"] = data["exchange"]
        if data.get("currency"):
            properties["currency"] = data["currency"]
        if data.get("num_constituents"):
            properties["numConstituents"] = data["num_constituents"]
        
        uri = self.kg.add_entity(
            label=name,
            entity_type="MarketIndex",
            properties=properties,
            namespace=OPENBB,
            source="openbb",
            timestamp=datetime.now(),
        )
        return uri

    def _map_financial_statement_to_entity(self, data: dict[str, Any]) -> URIRef:
        """Map OpenBB financial statement to a KG entity."""
        ticker = data.get("ticker", "")
        statement_type = data.get("statement_type", "income_statement")
        fiscal_year = data.get("fiscal_year", "")
        fiscal_period = data.get("fiscal_period", "")
        
        label = f"{ticker} {statement_type.replace('_', ' ').title()} {fiscal_year} {fiscal_period}"
        
        type_mapping = {
            "income_statement": "IncomeStatement",
            "balance_sheet": "BalanceSheet",
            "cash_flow": "CashFlowStatement",
        }
        entity_type = type_mapping.get(statement_type, "FinancialStatement")
        
        properties: dict[str, Any] = {}
        if data.get("report_date"):
            properties["reportDate"] = data["report_date"]
        if data.get("fiscal_year"):
            properties["fiscalYear"] = data["fiscal_year"]
        if data.get("fiscal_period"):
            properties["fiscalPeriod"] = data["fiscal_period"]
        
        # Add statement items
        for item in data.get("items", []):
            label_key = item.get("label", "").lower().replace(" ", "_")[:40]
            if label_key and item.get("value") is not None:
                properties[label_key] = item["value"]
        
        uri = self.kg.add_entity(
            label=label,
            entity_type=entity_type,
            properties=properties,
            namespace=OPENBB,
            source="openbb",
            timestamp=datetime.now(),
        )
        
        # Link to company
        if ticker in self._company_map:
            self.kg.add_relation(
                self._company_map[ticker],
                uri,
                "hasFinancialStatement",
                source_name="openbb",
            )
        
        return uri

    def _map_earnings_to_entity(self, data: dict[str, Any]) -> URIRef:
        """Map OpenBB earnings data to a KG entity."""
        ticker = data.get("ticker", "")
        fiscal_period = data.get("fiscal_period", "")
        report_date = data.get("report_date", "")
        
        label = f"{ticker} Earnings {fiscal_period} {report_date}"
        
        properties: dict[str, Any] = {}
        if data.get("eps_actual"):
            properties["epsActual"] = data["eps_actual"]
        if data.get("eps_estimate"):
            properties["epsEstimate"] = data["eps_estimate"]
        if data.get("revenue_actual"):
            properties["revenueActual"] = data["revenue_actual"]
        if data.get("revenue_estimate"):
            properties["revenueEstimate"] = data["revenue_estimate"]
        if data.get("report_date"):
            properties["reportDate"] = data["report_date"]
        if data.get("fiscal_period"):
            properties["fiscalPeriod"] = data["fiscal_period"]
        
        uri = self.kg.add_entity(
            label=label,
            entity_type="EarningsReport",
            properties=properties,
            namespace=OPENBB,
            source="openbb",
            timestamp=datetime.now(),
        )
        
        # Link to company
        if ticker in self._company_map:
            self.kg.add_relation(
                self._company_map[ticker],
                uri,
                "hasEarningsReport",
                source_name="openbb",
            )
        
        return uri

    def _map_news_to_entity(self, data: dict[str, Any]) -> URIRef:
        """Map OpenBB news data to a KG entity."""
        title = data.get("title", "News Article")
        source = data.get("source", "")
        
        properties: dict[str, Any] = {}
        if source:
            properties["source"] = source
        if data.get("date"):
            properties["date"] = data["date"]
        if data.get("url"):
            properties["url"] = data["url"]
        if data.get("summary"):
            properties["summary"] = data["summary"]
        if data.get("sentiment"):
            properties["sentiment"] = data["sentiment"]
        
        uri = self.kg.add_entity(
            label=title,
            entity_type="NewsArticle",
            properties=properties,
            namespace=OPENBB,
            source="openbb",
            timestamp=datetime.now(),
        )
        
        # Link to mentioned companies
        for ticker in data.get("tickers", []):
            if ticker in self._company_map:
                self.kg.add_relation(
                    uri,
                    self._company_map[ticker],
                    "mentions",
                    source_name="openbb",
                )
        
        return uri

    def _map_company_to_entity(self, data: dict[str, Any]) -> URIRef:
        """Map OpenBB company profile to a KG entity."""
        ticker = data.get("ticker", "")
        name = data.get("name", ticker)
        
        properties: dict[str, Any] = {}
        if ticker:
            properties["hasTicker"] = ticker
        if data.get("sector"):
            properties["sector"] = data["sector"]
        if data.get("industry"):
            properties["industry"] = data["industry"]
        if data.get("market_cap"):
            properties["hasMarketCap"] = data["market_cap"]
        if data.get("pe_ratio"):
            properties["peRatio"] = data["pe_ratio"]
        if data.get("dividend_yield"):
            properties["dividendYield"] = data["dividend_yield"]
        if data.get("beta"):
            properties["beta"] = data["beta"]
        if data.get("eps"):
            properties["eps"] = data["eps"]
        if data.get("revenue"):
            properties["hasRevenue"] = data["revenue"]
        if data.get("employees"):
            properties["hasEmployeeCount"] = data["employees"]
        if data.get("country"):
            properties["country"] = data["country"]
        if data.get("exchange"):
            properties["exchange"] = data["exchange"]
        
        uri = self.kg.add_entity(
            label=name,
            entity_type="Corporation",
            properties=properties,
            namespace=OPENBB,
            source="openbb",
            timestamp=datetime.now(),
        )
        
        if ticker:
            self._company_map[ticker] = uri
        return uri

    # ---- Sample Data Generators (for PoC) ----

    @staticmethod
    def generate_sample_equities() -> list[dict[str, Any]]:
        """Generate sample OpenBB equity data for testing."""
        return [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "market_cap": 3000000000000.0,
                "exchange": "NASDAQ",
                "cik": "0000320193",
                "isin": "US0378331005",
                "description": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories.",
                "website": "https://www.apple.com",
                "employees": 164000,
                "country": "United States",
            },
            {
                "symbol": "MSFT",
                "name": "Microsoft Corporation",
                "sector": "Technology",
                "industry": "Software",
                "market_cap": 2800000000000.0,
                "exchange": "NASDAQ",
                "cik": "0000789019",
                "isin": "US5949181045",
                "description": "Microsoft Corporation develops and supports software, services, devices, and solutions.",
                "website": "https://www.microsoft.com",
                "employees": 221000,
                "country": "United States",
            },
            {
                "symbol": "GOOGL",
                "name": "Alphabet Inc.",
                "sector": "Technology",
                "industry": "Internet Services",
                "market_cap": 1700000000000.0,
                "exchange": "NASDAQ",
                "cik": "0001652044",
                "isin": "US02079K3059",
                "description": "Alphabet Inc. provides online advertising services in the United States and internationally.",
                "website": "https://www.abc.xyz",
                "employees": 182000,
                "country": "United States",
            },
        ]

    @staticmethod
    def generate_sample_etfs() -> list[dict[str, Any]]:
        """Generate sample OpenBB ETF data for testing."""
        return [
            {
                "symbol": "SPY",
                "name": "SPDR S&P 500 ETF Trust",
                "aum": 400000000000.0,
                "issuer": "State Street Global Advisors",
                "sector_weights": {
                    "Technology": 0.28,
                    "Healthcare": 0.13,
                    "Financials": 0.11,
                    "Consumer Discretionary": 0.10,
                },
                "top_holdings": [
                    {"symbol": "AAPL", "weight": 0.07},
                    {"symbol": "MSFT", "weight": 0.06},
                    {"symbol": "GOOGL", "weight": 0.04},
                ],
            },
        ]

    @staticmethod
    def generate_sample_indices() -> list[dict[str, Any]]:
        """Generate sample OpenBB index data for testing."""
        return [
            {
                "symbol": "SPX",
                "name": "S&P 500",
                "exchange": "NYSE",
                "currency": "USD",
                "num_constituents": 500,
            },
            {
                "symbol": "NDX",
                "name": "NASDAQ-100",
                "exchange": "NASDAQ",
                "currency": "USD",
                "num_constituents": 100,
            },
        ]

    @staticmethod
    def generate_sample_financial_statements() -> list[dict[str, Any]]:
        """Generate sample OpenBB financial statement data for testing."""
        return [
            {
                "ticker": "AAPL",
                "statement_type": "income_statement",
                "period": "annual",
                "fiscal_year": 2023,
                "fiscal_period": "FY",
                "report_date": "2023-10-01",
                "items": [
                    {"label": "Total Revenue", "value": 383285000000, "unit": "USD"},
                    {"label": "Net Income", "value": 96995000000, "unit": "USD"},
                    {"label": "EPS", "value": 6.16, "unit": "USD"},
                    {"label": "Gross Profit", "value": 170782000000, "unit": "USD"},
                ],
            },
            {
                "ticker": "AAPL",
                "statement_type": "balance_sheet",
                "period": "annual",
                "fiscal_year": 2023,
                "fiscal_period": "FY",
                "report_date": "2023-10-01",
                "items": [
                    {"label": "Total Assets", "value": 352583000000, "unit": "USD"},
                    {"label": "Total Liabilities", "value": 290437000000, "unit": "USD"},
                    {"label": "Total Equity", "value": 62146000000, "unit": "USD"},
                    {"label": "Cash and Equivalents", "value": 29965000000, "unit": "USD"},
                ],
            },
        ]

    @staticmethod
    def generate_sample_earnings() -> list[dict[str, Any]]:
        """Generate sample OpenBB earnings data for testing."""
        return [
            {
                "ticker": "AAPL",
                "report_date": "2023-10-27",
                "fiscal_period": "Q4 2023",
                "eps_actual": 1.46,
                "eps_estimate": 1.39,
                "revenue_actual": 89498000000,
                "revenue_estimate": 89280000000,
            },
        ]

    @staticmethod
    def generate_sample_news() -> list[dict[str, Any]]:
        """Generate sample OpenBB news data for testing."""
        return [
            {
                "title": "Apple Reports Record Q4 Revenue",
                "source": "Reuters",
                "date": "2023-10-27T16:30:00",
                "url": "https://reuters.com/article/apple-earnings",
                "summary": "Apple Inc. reported record fourth-quarter revenue, beating analyst expectations.",
                "tickers": ["AAPL"],
                "sentiment": "positive",
            },
            {
                "title": "Microsoft Cloud Revenue Surges 29%",
                "source": "Bloomberg",
                "date": "2023-10-24T14:00:00",
                "url": "https://bloomberg.com/article/msft-cloud",
                "summary": "Microsoft's Azure cloud platform drove a 29% increase in overall revenue.",
                "tickers": ["MSFT"],
                "sentiment": "positive",
            },
        ]
