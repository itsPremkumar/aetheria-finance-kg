"""Tests for Finance KG."""

import pytest
from finance_kg import (
    FinanceKG, Entity, Relation,
    RiskLevel, AssetType
)


class TestFinanceKG:
    def test_create(self):
        kg = FinanceKG()
        assert kg.entity_count() == 0
        assert kg.relation_count() == 0

    def test_entity_types(self):
        kg = FinanceKG()
        assert len(kg.ENTITY_TYPES) == 10
        assert "Company" in kg.ENTITY_TYPES
        assert "RiskFactor" in kg.ENTITY_TYPES

    def test_relation_types(self):
        kg = FinanceKG()
        assert len(kg.RELATION_TYPES) == 12

    def test_add_entity(self):
        kg = FinanceKG()
        kg.add_entity(Entity(id="c1", type="Company"))
        assert kg.entity_count() == 1

    def test_get_entity(self):
        kg = FinanceKG()
        kg.add_entity(Entity(id="c1", type="Company"))
        result = kg.get_entity("c1")
        assert result is not None
        assert result.type == "Company"

    def test_find_by_type(self):
        kg = FinanceKG()
        kg.add_entity(Entity(id="c1", type="Company"))
        kg.add_entity(Entity(id="c2", type="Company"))
        kg.add_entity(Entity(id="t1", type="Ticker"))
        results = kg.find_by_type("Company")
        assert len(results) == 2

    def test_find_by_property(self):
        kg = FinanceKG()
        kg.add_entity(Entity(id="c1", type="Company", properties={"name": "Apple"}))
        kg.add_entity(Entity(id="c2", type="Company", properties={"name": "Google"}))
        results = kg.find_by_property("name", "Apple")
        assert len(results) == 1

    def test_add_relation(self):
        kg = FinanceKG()
        kg.add_relation(Relation("c1", "HAS_TICKER", "t1"))
        assert kg.relation_count() == 1

    def test_get_relations_by_entity(self):
        kg = FinanceKG()
        kg.add_entity(Entity(id="c1", type="Company"))
        kg.add_entity(Entity(id="t1", type="Ticker"))
        kg.add_entity(Entity(id="m1", type="Metric"))
        kg.add_relation(Relation("c1", "HAS_TICKER", "t1"))
        kg.add_relation(Relation("c1", "HAS_METRIC", "m1"))
        results = kg.get_relations("c1")
        assert len(results) == 2

    def test_get_relations_by_type(self):
        kg = FinanceKG()
        kg.add_relation(Relation("c1", "HAS_TICKER", "t1"))
        kg.add_relation(Relation("c2", "HAS_TICKER", "t2"))
        kg.add_relation(Relation("c3", "BELONGS_TO_SECTOR", "s1"))
        results = kg.get_relations(relation_type="HAS_TICKER")
        assert len(results) == 2

    def test_get_company_ticker(self):
        kg = FinanceKG()
        kg.add_entity(Entity(id="c1", type="Company"))
        kg.add_entity(Entity(id="t1", type="Ticker"))
        kg.add_relation(Relation("c1", "HAS_TICKER", "t1"))
        ticker = kg.get_company_ticker("c1")
        assert ticker is not None
        assert ticker.id == "t1"

    def test_get_sector_companies(self):
        kg = FinanceKG()
        kg.add_entity(Entity(id="s1", type="Sector"))
        kg.add_entity(Entity(id="c1", type="Company"))
        kg.add_entity(Entity(id="c2", type="Company"))
        kg.add_relation(Relation("c1", "BELONGS_TO_SECTOR", "s1"))
        kg.add_relation(Relation("c2", "BELONGS_TO_SECTOR", "s1"))
        companies = kg.get_sector_companies("s1")
        assert len(companies) == 2

    def test_get_company_metrics(self):
        kg = FinanceKG()
        kg.add_entity(Entity(id="c1", type="Company"))
        kg.add_entity(Entity(id="m1", type="Metric"))
        kg.add_entity(Entity(id="m2", type="Metric"))
        kg.add_relation(Relation("c1", "HAS_METRIC", "m1"))
        kg.add_relation(Relation("c1", "HAS_METRIC", "m2"))
        metrics = kg.get_company_metrics("c1")
        assert len(metrics) == 2

    def test_calculate_risk_score(self):
        kg = FinanceKG()
        kg.add_entity(Entity(id="c1", type="Company"))
        kg.add_entity(Entity(id="r1", type="RiskFactor", properties={"severity": 8}))
        kg.add_relation(Relation("c1", "HAS_RISK", "r1"))
        result = kg.calculate_risk_score("c1")
        assert result["score"] > 0
        assert result["level"] in [RiskLevel.LOW.value, RiskLevel.MEDIUM.value, RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]

    def test_calculate_risk_score_no_factors(self):
        kg = FinanceKG()
        kg.add_entity(Entity(id="c1", type="Company"))
        result = kg.calculate_risk_score("c1")
        assert result["score"] == 0
        assert result["level"] == RiskLevel.LOW.value

    def test_portfolio_optimization(self):
        kg = FinanceKG()
        kg.add_entity(Entity(id="p1", type="Portfolio"))
        kg.add_entity(Entity(id="i1", type="Instrument", properties={"asset_type": "equity"}))
        kg.add_entity(Entity(id="i2", type="Instrument", properties={"asset_type": "bond"}))
        kg.add_relation(Relation("p1", "CONTAINS", "i1"))
        kg.add_relation(Relation("p1", "CONTAINS", "i2"))
        result = kg.portfolio_optimization("p1")
        assert result["diversification_score"] > 0

    def test_portfolio_optimization_empty(self):
        kg = FinanceKG()
        kg.add_entity(Entity(id="p1", type="Portfolio"))
        result = kg.portfolio_optimization("p1")
        assert result["diversification_score"] == 0

    def test_fraud_detection(self):
        kg = FinanceKG()
        kg.add_entity(Entity(id="t1", type="Transaction", properties={"amount": 2000000, "cross_border": True}))
        result = kg.fraud_detection("t1")
        assert result["fraud_risk"] == "high"

    def test_fraud_detection_safe(self):
        kg = FinanceKG()
        kg.add_entity(Entity(id="t1", type="Transaction", properties={"amount": 100}))
        result = kg.fraud_detection("t1")
        assert result["fraud_risk"] == "low"

    def test_fraud_detection_missing(self):
        kg = FinanceKG()
        result = kg.fraud_detection("missing")
        assert result["fraud_risk"] == "unknown"

    def test_credit_risk_scoring(self):
        kg = FinanceKG()
        kg.add_entity(Entity(id="c1", type="Company"))
        kg.add_entity(Entity(id="m1", type="Metric", properties={"name": "debt_to_equity", "value": 3.0}))
        kg.add_entity(Entity(id="m2", type="Metric", properties={"name": "current_ratio", "value": 0.8}))
        kg.add_relation(Relation("c1", "HAS_METRIC", "m1"))
        kg.add_relation(Relation("c1", "HAS_METRIC", "m2"))
        result = kg.credit_risk_scoring("c1")
        assert result["credit_score"] < 100
        assert result["rating"] in ["AAA", "AA", "A", "BBB", "BB", "B"]

    def test_credit_risk_scoring_no_metrics(self):
        kg = FinanceKG()
        kg.add_entity(Entity(id="c1", type="Company"))
        result = kg.credit_risk_scoring("c1")
        assert result["rating"] == "N/A"

    def test_market_trend_prediction(self):
        kg = FinanceKG()
        kg.add_entity(Entity(id="s1", type="Sector"))
        kg.add_entity(Entity(id="c1", type="Company"))
        kg.add_entity(Entity(id="m1", type="Metric"))
        kg.add_relation(Relation("c1", "BELONGS_TO_SECTOR", "s1"))
        kg.add_relation(Relation("c1", "HAS_METRIC", "m1"))
        result = kg.market_trend_prediction("s1")
        assert result["confidence"] > 0

    def test_market_trend_prediction_empty(self):
        kg = FinanceKG()
        kg.add_entity(Entity(id="s1", type="Sector"))
        result = kg.market_trend_prediction("s1")
        assert result["trend"] == "unknown"

    def test_clear(self):
        kg = FinanceKG()
        kg.add_entity(Entity(id="c1", type="Company"))
        kg.add_relation(Relation("c1", "HAS_TICKER", "t1"))
        kg.clear()
        assert kg.entity_count() == 0
        assert kg.relation_count() == 0
