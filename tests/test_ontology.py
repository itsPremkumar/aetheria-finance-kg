"""
tests/test_ontology.py - FIBO ontology tests.
"""
import pytest
from rdflib import URIRef

from src.finance_kg.ontology.fibo import FIBOOntology, FIBOClass, FIBOProperty
from src.finance_kg.ontology.namespaces import FINANCE, FIBO


class TestFIBOOntology:
    def test_create(self):
        ontology = FIBOOntology()
        assert ontology is not None

    def test_core_classes_loaded(self):
        ontology = FIBOOntology()
        classes = ontology.get_all_classes()
        assert len(classes) >= 30

    def test_core_properties_loaded(self):
        ontology = FIBOOntology()
        properties = ontology.get_all_properties()
        assert len(properties) >= 25

    def test_get_class(self):
        ontology = FIBOOntology()
        cls = ontology.get_class("Corporation")
        assert cls is not None
        assert isinstance(cls, FIBOClass)
        assert cls.label == "Corporation"

    def test_get_class_not_found(self):
        ontology = FIBOOntology()
        cls = ontology.get_class("NonExistentClass")
        assert cls is None

    def test_get_property(self):
        ontology = FIBOOntology()
        prop = ontology.get_property("hasTicker")
        assert prop is not None
        assert isinstance(prop, FIBOProperty)

    def test_get_property_not_found(self):
        ontology = FIBOOntology()
        prop = ontology.get_property("nonExistentProperty")
        assert prop is None

    def test_search_classes(self):
        ontology = FIBOOntology()
        results = ontology.search_classes("Corporation")
        assert len(results) >= 1

    def test_search_classes_by_definition(self):
        ontology = FIBOOntology()
        results = ontology.search_classes("financial services")
        assert len(results) >= 1

    def test_validate_entity(self):
        ontology = FIBOOntology()
        from rdflib import Graph, RDF
        g = Graph()
        uri = URIRef("https://example.com/test_entity")
        corporation_cls = ontology.get_class("Corporation")
        g.add((uri, RDF.type, corporation_cls.uri))
        # Merge into ontology graph
        ontology.graph += g
        result = ontology.validate_entity(uri, "Corporation")
        assert result is True

    def test_export(self):
        ontology = FIBOOntology()
        ttl = ontology.export(format="turtle")
        assert len(ttl) > 0

    def test_export_to_file(self, tmp_path):
        ontology = FIBOOntology()
        path = tmp_path / "ontology.ttl"
        ontology.export_to_file(path, format="turtle")
        assert path.exists()

    def test_merge_to_graph(self):
        ontology = FIBOOntology()
        from rdflib import Graph
        target = Graph()
        initial_len = len(target)
        ontology.merge_to_graph(target)
        assert len(target) > initial_len

    def test_len(self):
        ontology = FIBOOntology()
        assert len(ontology) > 0

    def test_repr(self):
        ontology = FIBOOntology()
        repr_str = repr(ontology)
        assert "FIBOOntology" in repr_str

    def test_has_organization_class(self):
        ontology = FIBOOntology()
        cls = ontology.get_class("Organization")
        assert cls is not None

    def test_has_corporation_class(self):
        ontology = FIBOOntology()
        cls = ontology.get_class("Corporation")
        assert cls is not None

    def test_has_loan_class(self):
        ontology = FIBOOntology()
        cls = ontology.get_class("Loan")
        assert cls is not None

    def test_has_security_class(self):
        ontology = FIBOOntology()
        cls = ontology.get_class("Security")
        assert cls is not None

    def test_has_person_class(self):
        ontology = FIBOOntology()
        cls = ontology.get_class("Person")
        assert cls is not None

    def test_has_asset_class(self):
        ontology = FIBOOntology()
        cls = ontology.get_class("Asset")
        assert cls is not None

    def test_has_liability_class(self):
        ontology = FIBOOntology()
        cls = ontology.get_class("Liability")
        assert cls is not None
