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
