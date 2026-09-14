"""
tests/test_cli.py - CLI tests for the old finance_kg package.
"""
import pytest
import os

from finance_kg.graph import KnowledgeGraph
from finance_kg.entities import Entity, EntityType
from finance_kg.relations import Relation, RelationType
from finance_kg.sec_patterns import SECFilingParser


class TestParseFilingCommand:
    def test_parse_filing(self, tmp_path):
        filing_file = tmp_path / "filing.txt"
        filing_file.write_text("This is a 10-K filing for Apple Inc.")
        parser = SECFilingParser()
        result = parser.parse(str(filing_file))
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_parse_filing_with_output(self, tmp_path):
        filing_file = tmp_path / "filing.txt"
        filing_file.write_text("This is a 10-K filing for Apple Inc.")
        parser = SECFilingParser()
        result = parser.parse(str(filing_file))
        assert isinstance(result, list)


class TestBuildCommand:
    def test_build_empty_graph(self):
        kg = KnowledgeGraph()
        stats = kg.get_stats()
        assert stats["entities"] == 0
        assert stats["relations"] == 0


class TestQueryCommand:
    def test_query_empty_graph(self):
        kg = KnowledgeGraph()
        results = kg.search("Apple")
        assert len(results) == 0

    def test_query_with_results(self):
        kg = KnowledgeGraph()
        entity = Entity(id="e1", entity_type=EntityType.COMPANY, label="Apple Inc.")
        kg.add_entities([entity])
        results = kg.search("Apple")
        assert len(results) == 1

    def test_query_case_insensitive(self):
        kg = KnowledgeGraph()
        entity = Entity(id="e1", entity_type=EntityType.COMPANY, label="Apple Inc.")
        kg.add_entities([entity])
        results = kg.search("apple")
        assert len(results) == 1

    def test_query_by_type(self):
        kg = KnowledgeGraph()
        entity1 = Entity(id="e1", entity_type=EntityType.COMPANY, label="Apple")
        entity2 = Entity(id="e2", entity_type=EntityType.PERSON, label="John")
        kg.add_entities([entity1, entity2])
        results = kg.search("A", entity_type="Company")
        assert len(results) == 1
