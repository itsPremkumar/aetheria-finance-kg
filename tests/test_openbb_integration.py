"""
tests/test_openbb_integration.py - OpenBB Platform integration tests.
"""
import pytest
from src.finance_kg.graph.knowledge_graph import FinanceKnowledgeGraph
from src.finance_kg.integrations.openbb import OpenBBIntegration


@pytest.fixture
def kg():
    return FinanceKnowledgeGraph()


@pytest.fixture
def integration(kg):
    return OpenBBIntegration(kg)


class TestOpenBBIntegration:
    def test_create(self, integration):
        assert integration is not None
        assert integration.kg is not None

    def test_load_equity_from_data(self, integration):
        equity = OpenBBIntegration.generate_sample_equities()[0]
        uri = integration.load_equity_from_data(equity)
        assert uri is not None
        entity = integration.kg.get_entity(uri)
        assert entity is not None
        assert entity.entity_type == "Corporation"

    def test_load_etf_from_data(self, integration):
        # First load equities so ETF can link to them
        equities = OpenBBIntegration.generate_sample_equities()
        for eq in equities:
            integration.load_equity_from_data(eq)
        etf = OpenBBIntegration.generate_sample_etfs()[0]
        uri = integration.load_etf_from_data(etf)
        assert uri is not None
        entity = integration.kg.get_entity(uri)
        assert entity.entity_type == "ExchangeTradedFund"

    def test_load_index_from_data(self, integration):
        index = OpenBBIntegration.generate_sample_indices()[0]
        uri = integration.load_index_from_data(index)
        assert uri is not None
        entity = integration.kg.get_entity(uri)
        assert entity.entity_type == "MarketIndex"

    def test_load_financial_statement_from_data(self, integration):
        # First load equity
        equity = OpenBBIntegration.generate_sample_equities()[0]
        integration.load_equity_from_data(equity)
        statement = OpenBBIntegration.generate_sample_financial_statements()[0]
        uri = integration.load_financial_statement_from_data(statement)
        assert uri is not None
        entity = integration.kg.get_entity(uri)
        assert entity.entity_type == "IncomeStatement"

    def test_load_earnings_from_data(self, integration):
        equity = OpenBBIntegration.generate_sample_equities()[0]
        integration.load_equity_from_data(equity)
        earnings = OpenBBIntegration.generate_sample_earnings()[0]
        uri = integration.load_earnings_from_data(earnings)
        assert uri is not None
        entity = integration.kg.get_entity(uri)
        assert entity.entity_type == "EarningsReport"

    def test_load_news_from_data(self, integration):
        equity = OpenBBIntegration.generate_sample_equities()[0]
        integration.load_equity_from_data(equity)
        news = OpenBBIntegration.generate_sample_news()[0]
        uri = integration.load_news_from_data(news)
        assert uri is not None
        entity = integration.kg.get_entity(uri)
        assert entity.entity_type == "NewsArticle"

    def test_load_company_from_data(self, integration):
        company = {
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "sector": "Technology",
            "market_cap": 3000000000000.0,
        }
        uri = integration.load_company_from_data(company)
        assert uri is not None
        entity = integration.kg.get_entity(uri)
        assert entity.entity_type == "Corporation"

    def test_company_map_populated(self, integration):
        equity = OpenBBIntegration.generate_sample_equities()[0]
        integration.load_equity_from_data(equity)
        assert "AAPL" in integration._company_map

    def test_generate_sample_equities(self):
        equities = OpenBBIntegration.generate_sample_equities()
        assert len(equities) == 3
        assert equities[0]["symbol"] == "AAPL"

    def test_generate_sample_etfs(self):
        etfs = OpenBBIntegration.generate_sample_etfs()
        assert len(etfs) == 1
        assert etfs[0]["symbol"] == "SPY"

    def test_generate_sample_indices(self):
        indices = OpenBBIntegration.generate_sample_indices()
        assert len(indices) == 2

    def test_generate_sample_financial_statements(self):
        statements = OpenBBIntegration.generate_sample_financial_statements()
        assert len(statements) == 2

    def test_generate_sample_earnings(self):
        earnings = OpenBBIntegration.generate_sample_earnings()
        assert len(earnings) == 1

    def test_generate_sample_news(self):
        news = OpenBBIntegration.generate_sample_news()
        assert len(news) == 2
