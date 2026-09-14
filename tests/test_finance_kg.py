<<<<<<< HEAD
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
=======
"""
Tests for Finance KG — Open-Source Integration.
Test count: 24
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'src'))

from finance_kg.entities import EntityExtractor, Entity, EntityType
from finance_kg.relations import RelationExtractor, Relation, RelationType
from finance_kg.graph import KnowledgeGraph, GraphConfig
from finance_kg.reasoning import ReasoningEngine, QueryResult
from finance_kg.sec_patterns import SECFilingParser
from finance_kg.cache import RawCache


# ──────────────────── Entity Tests ────────────────────────────────────


class TestEntityExtractor:
    def test_create(self):
        extractor = EntityExtractor()
        assert extractor is not None

    def test_extract_companies(self):
        extractor = EntityExtractor()
        text = "Apple Inc. acquired Beats Electronics for $3 billion."
        entities = extractor.extract(text)
        company_entities = [e for e in entities if e.entity_type == EntityType.COMPANY]
        assert len(company_entities) >= 1

    def test_extract_amounts(self):
        extractor = EntityExtractor()
        text = "The acquisition was valued at $3 billion in cash."
        entities = extractor.extract(text)
        amount_entities = [e for e in entities if e.entity_type == EntityType.AMOUNT]
        assert len(amount_entities) >= 1

    def test_extract_dates(self):
        extractor = EntityExtractor()
        text = "The deal closed in Q2 2014 and was announced in FY2014."
        entities = extractor.extract(text)
        date_entities = [e for e in entities if e.entity_type == EntityType.DATE]
        assert len(date_entities) >= 1


# ──────────────────── Relation Tests ─────────────────────────────────


class TestRelationExtractor:
    def test_create(self):
        extractor = RelationExtractor()
        assert extractor is not None

    def test_extract_acquired(self):
        extractor = RelationExtractor()
        text = "Apple Inc. acquired Beats Electronics for $3 billion."
        relations = extractor.extract(text)
        assert len(relations) >= 1
        assert relations[0].relation_type == RelationType.ACQUIRED

    def test_extract_merged_with(self):
        extractor = RelationExtractor()
        text = "Company A merged with Company B to form a new entity."
        relations = extractor.extract(text)
        merged = [r for r in relations if r.relation_type == RelationType.MERGED_WITH]
        assert len(merged) >= 1


# ──────────────────── Graph Tests ─────────────────────────────────────


class TestKnowledgeGraph:
    def test_create(self):
        graph = KnowledgeGraph()
        assert graph is not None

    def test_add_entities(self):
        graph = KnowledgeGraph()
        entities = [
            Entity(id="e1", entity_type=EntityType.COMPANY, label="Apple"),
            Entity(id="e2", entity_type=EntityType.COMPANY, label="Beats"),
        ]
        graph.add_entities(entities)
        assert len(graph.search("Apple")) == 1

    def test_add_relations(self):
        graph = KnowledgeGraph()
        entities = [
            Entity(id="e1", entity_type=EntityType.COMPANY, label="Apple"),
            Entity(id="e2", entity_type=EntityType.COMPANY, label="Beats"),
        ]
        graph.add_entities(entities)
        relations = [
            Relation(id="r1", relation_type=RelationType.ACQUIRED, source_id="e1", target_id="e2"),
        ]
        graph.add_relations(relations)
        assert len(graph.get_relations("e1")) == 1

    def test_search(self):
        graph = KnowledgeGraph()
        entities = [
            Entity(id="e1", entity_type=EntityType.COMPANY, label="Apple Inc."),
            Entity(id="e2", entity_type=EntityType.COMPANY, label="Microsoft Corp."),
        ]
        graph.add_entities(entities)
        results = graph.search("Apple")
        assert len(results) == 1

    def test_get_network(self):
        graph = KnowledgeGraph()
        entities = [
            Entity(id="e1", entity_type=EntityType.COMPANY, label="Apple"),
            Entity(id="e2", entity_type=EntityType.COMPANY, label="Beats"),
            Entity(id="e3", entity_type=EntityType.COMPANY, label="Samsung"),
        ]
        graph.add_entities(entities)
        relations = [
            Relation(id="r1", relation_type=RelationType.ACQUIRED, source_id="e1", target_id="e2"),
            Relation(id="r2", relation_type=RelationType.COMPETES_WITH, source_id="e1", target_id="e3"),
        ]
        graph.add_relations(relations)
        network = graph.get_network("e1", depth=2)
        assert len(network["nodes"]) == 3
        assert len(network["edges"]) == 2

    def test_export_import_json(self):
        graph = KnowledgeGraph()
        entities = [
            Entity(id="e1", entity_type=EntityType.COMPANY, label="Apple"),
        ]
        graph.add_entities(entities)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name

        try:
            graph.export_json(path)
            graph2 = KnowledgeGraph()
            graph2.import_json(path)
            stats = graph2.get_stats()
            assert stats["entities"] == 1
        finally:
            os.unlink(path)


# ──────────────────── Reasoning Tests ─────────────────────────────────


class TestReasoningEngine:
    def test_create(self):
        graph = KnowledgeGraph()
        engine = ReasoningEngine(graph)
        assert engine is not None

    def test_query(self):
        graph = KnowledgeGraph()
        entities = [Entity(id="e1", entity_type=EntityType.COMPANY, label="Apple")]
        graph.add_entities(entities)
        engine = ReasoningEngine(graph)
        results = engine.query("Apple")
        assert len(results) == 1

    def test_analyze_company(self):
        graph = KnowledgeGraph()
        entities = [Entity(id="e1", entity_type=EntityType.COMPANY, label="Apple")]
        graph.add_entities(entities)
        engine = ReasoningEngine(graph)
        analysis = engine.analyze_company("Apple")
        assert "company" in analysis
        assert "relations" in analysis
        assert "network" in analysis


# ──────────────────── SEC Parser Tests ────────────────────────────────


class TestSECFilingParser:
    def test_create(self):
        parser = SECFilingParser()
        assert parser is not None

    def test_detect_form_type(self):
        parser = SECFilingParser()
        content = "This is a 10-K filing for Apple Inc."
        form_type = parser._detect_form_type(content)
        assert form_type == "10-K"

    def test_parse_filing(self):
        parser = SECFilingParser()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Item 1. Business\nApple Inc. designs and manufactures smartphones.\n\nItem 1A. Risk Factors\nCompetition in the technology sector is intense.\n")
            path = f.name

        try:
            sections = parser.parse(path)
            assert len(sections) >= 1
        finally:
            os.unlink(path)


# ──────────────────── Cache Tests ─────────────────────────────────────


class TestRawCache:
    def test_create(self):
        cache = RawCache()
        assert cache is not None

    def test_set_get(self):
        cache = RawCache()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_delete(self):
        cache = RawCache()
        cache.set("key1", "value1")
        cache.delete("key1")
        assert cache.get("key1") is None

    def test_clear(self):
        cache = RawCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.size() == 0
>>>>>>> f961630c1bd97e199d6937e8871139eb1bc3abc1
