"""
tests/test_knowledge_graph.py - RDF Knowledge Graph tests.
"""
import pytest
from rdflib import URIRef

from src.finance_kg.graph.knowledge_graph import FinanceKnowledgeGraph, Entity, Relation
from src.finance_kg.ontology.namespaces import FINANCE


class TestFinanceKnowledgeGraph:
    def test_create(self):
        kg = FinanceKnowledgeGraph()
        assert kg is not None
        assert len(kg) > 0  # FIBO ontology loaded

    def test_add_entity(self):
        kg = FinanceKnowledgeGraph()
        uri = kg.add_entity("Apple Inc.", "Corporation", {"hasTicker": "AAPL"})
        assert uri is not None
        assert isinstance(uri, URIRef)

    def test_add_entity_with_properties(self):
        kg = FinanceKnowledgeGraph()
        uri = kg.add_entity(
            "Test Corp",
            "Corporation",
            {"hasTicker": "TEST", "hasMarketCap": 1000000},
            source="test",
        )
        entity = kg.get_entity(uri)
        assert entity is not None
        assert entity.label == "Test Corp"
        assert entity.entity_type == "Corporation"

    def test_add_relation(self):
        kg = FinanceKnowledgeGraph()
        apple = kg.add_entity("Apple", "Corporation")
        microsoft = kg.add_entity("Microsoft", "Corporation")
        kg.add_relation(apple, microsoft, "competesWith")
        relations = kg.get_relations(apple)
        assert len(relations) >= 1

    def test_find_entities_by_type(self):
        kg = FinanceKnowledgeGraph()
        kg.add_entity("Apple", "Corporation")
        kg.add_entity("Microsoft", "Corporation")
        kg.add_entity("John Doe", "Person")
        corporations = kg.find_entities_by_type("Corporation")
        assert len(corporations) >= 2

    def test_find_entities_by_name(self):
        kg = FinanceKnowledgeGraph()
        kg.add_entity("Apple Inc.", "Corporation")
        kg.add_entity("Apple Bank", "Corporation")
        results = kg.find_entities_by_name("Apple")
        assert len(results) >= 2

    def test_find_relations(self):
        kg = FinanceKnowledgeGraph()
        apple = kg.add_entity("Apple", "Corporation")
        beats = kg.add_entity("Beats", "Corporation")
        kg.add_relation(apple, beats, "acquired")
        relations = kg.find_relations(entity_id=apple)
        assert len(relations) >= 1

    def test_query_sparql(self):
        kg = FinanceKnowledgeGraph()
        kg.add_entity("Apple", "Corporation", {"hasTicker": "AAPL"})
        results = kg.query("SELECT ?x WHERE { ?x <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://aetheria.finance/kg/finance/Corporation> }")
        assert isinstance(results, list)

    def test_stats(self):
        kg = FinanceKnowledgeGraph()
        kg.add_entity("Apple", "Corporation")
        stats = kg.get_statistics()
        assert "total_triples" in stats
        assert "entities" in stats
        assert stats["total_triples"] > 0

    def test_export_import(self):
        kg = FinanceKnowledgeGraph()
        apple = kg.add_entity("Apple", "Corporation", {"hasTicker": "AAPL"})
        ttl = kg.export(format="turtle")
        assert len(ttl) > 0
        assert "Apple" in ttl or "finance" in ttl

    def test_export_to_file(self, tmp_path):
        kg = FinanceKnowledgeGraph()
        kg.add_entity("Apple", "Corporation")
        path = tmp_path / "graph.ttl"
        kg.save(str(path))
        assert path.exists()

    def test_load_from_file(self, tmp_path):
        kg = FinanceKnowledgeGraph()
        kg.add_entity("Apple", "Corporation")
        path = tmp_path / "graph.ttl"
        kg.save(str(path))
        kg2 = FinanceKnowledgeGraph.load(str(path))
        assert kg2 is not None

    def test_merge(self):
        kg1 = FinanceKnowledgeGraph()
        kg1.add_entity("Apple", "Corporation")
        kg2 = FinanceKnowledgeGraph()
        kg2.add_entity("Microsoft", "Corporation")
        kg1.merge(kg2)
        stats = kg1.get_statistics()
        assert stats["entities"] >= 2

    def test_find_peers(self):
        kg = FinanceKnowledgeGraph()
        apple = kg.add_entity("Apple", "Corporation")
        samsung = kg.add_entity("Samsung", "Corporation")
        kg.add_relation(apple, samsung, "competesWith")
        peers = kg.find_peers(apple)
        assert len(peers) >= 1

    def test_find_investors(self):
        kg = FinanceKnowledgeGraph()
        apple = kg.add_entity("Apple", "Corporation")
        investor = kg.add_entity("Berkshire Hathaway", "Corporation")
        kg.add_relation(investor, apple, "investedIn")
        investors = kg.find_investors(apple)
        assert len(investors) >= 1

    def test_find_subsidiaries(self):
        kg = FinanceKnowledgeGraph()
        parent = kg.add_entity("Alphabet", "Corporation")
        sub = kg.add_entity("Google", "Corporation")
        kg.add_relation(parent, sub, "parentOf")
        subs = kg.find_subsidiaries(parent)
        assert len(subs) >= 1

    def test_temporal_query(self):
        kg = FinanceKnowledgeGraph()
        uri = kg.add_entity("Apple", "Corporation", {"hasRevenue": 100000})
        results = kg.temporal_query(uri)
        assert isinstance(results, list)

    def test_repr(self):
        kg = FinanceKnowledgeGraph()
        repr_str = repr(kg)
        assert "FinanceKnowledgeGraph" in repr_str
