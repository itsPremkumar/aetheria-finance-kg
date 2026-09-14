"""
tests/test_reasoning.py - Financial Reasoning Engine tests.
"""
import pytest
from rdflib import URIRef

from src.finance_kg.graph.knowledge_graph import FinanceKnowledgeGraph
from src.finance_kg.reasoning.engine import FinancialReasoningEngine, ReasoningResult
from src.finance_kg.ontology.namespaces import FINANCE


@pytest.fixture
def kg():
    """Create a knowledge graph with sample data."""
    kg = FinanceKnowledgeGraph()
    
    # Add companies
    apple = kg.add_entity("Apple Inc.", "Corporation", {"hasTicker": "AAPL"})
    msft = kg.add_entity("Microsoft Corp.", "Corporation", {"hasTicker": "MSFT"})
    googl = kg.add_entity("Alphabet Inc.", "Corporation", {"hasTicker": "GOOGL"})
    
    # Add relations
    kg.add_relation(apple, msft, "competesWith")
    kg.add_relation(msft, googl, "competesWith")
    
    # Add financial data
    kg.add_entity(
        "Apple Financial Statement 2023",
        "FinancialStatement",
        {
            "hasRevenue": 383285000000,
            "hasNetIncome": 96995000000,
            "hasTotalAssets": 352583000000,
            "hasTotalLiabilities": 290437000000,
        },
        uri=URIRef("https://aetheria.finance/kg/finance/apple_fs_2023"),
    )
    
    return kg


@pytest.fixture
def engine(kg):
    return FinancialReasoningEngine(kg)


class TestFinancialReasoningEngine:
    def test_create(self, engine):
        assert engine is not None

    def test_find_peers(self, engine):
        result = engine.find_peers("AAPL")
        assert isinstance(result, ReasoningResult)
        assert result.result_type == "peer_analysis"
        assert result.query == "peers of AAPL"

    def test_find_peers_not_found(self, engine):
        result = engine.find_peers("INVALID")
        assert isinstance(result, ReasoningResult)
        assert result.confidence == 0.0
        assert "not found" in result.explanation.lower()

    def test_analyze_financials(self, engine):
        result = engine.analyze_financials("AAPL")
        assert isinstance(result, ReasoningResult)
        assert result.result_type == "financial_analysis"

    def test_analyze_financials_not_found(self, engine):
        result = engine.analyze_financials("INVALID")
        assert isinstance(result, ReasoningResult)
        assert result.confidence == 0.0

    def test_investment_flows(self, engine):
        result = engine.investment_flows("AAPL")
        assert isinstance(result, ReasoningResult)
        assert result.result_type == "investment_analysis"
        assert "num_investors" in result.metrics

    def test_investment_flows_not_found(self, engine):
        result = engine.investment_flows("INVALID")
        assert isinstance(result, ReasoningResult)
        assert result.confidence == 0.0

    def test_find_relationship_path(self, engine):
        result = engine.find_relationship_path("AAPL", "MSFT")
        assert isinstance(result, ReasoningResult)
        assert result.result_type == "relationship_path"

    def test_find_relationship_path_same_company(self, engine):
        result = engine.find_relationship_path("AAPL", "AAPL")
        assert isinstance(result, ReasoningResult)
        assert result.confidence == 0.9  # Same company = path length 0

    def test_find_relationship_path_not_found(self, engine):
        result = engine.find_relationship_path("INVALID", "MSFT")
        assert isinstance(result, ReasoningResult)
        assert result.confidence == 0.0

    def test_temporal_analysis(self, engine):
        result = engine.temporal_analysis("AAPL")
        assert isinstance(result, ReasoningResult)
        assert result.result_type == "temporal_analysis"
        assert "num_data_points" in result.metrics

    def test_temporal_analysis_not_found(self, engine):
        result = engine.temporal_analysis("INVALID")
        assert isinstance(result, ReasoningResult)
        assert result.confidence == 0.0

    def test_risk_analysis(self, engine):
        result = engine.risk_analysis("AAPL")
        assert isinstance(result, ReasoningResult)
        assert result.result_type == "risk_analysis"
        assert "risk_level" in result.metrics

    def test_risk_analysis_not_found(self, engine):
        result = engine.risk_analysis("INVALID")
        assert isinstance(result, ReasoningResult)
        assert result.confidence == 0.0

    def test_reasoning_result_to_dict(self, engine):
        result = engine.find_peers("AAPL")
        d = result.to_dict()
        assert "query" in d
        assert "result_type" in d
        assert "entities" in d
        assert "relations" in d
        assert "metrics" in d
        assert "explanation" in d
        assert "confidence" in d
