"""
tests/test_models.py - Entity and relation model tests.
"""
import pytest
from pydantic import ValidationError

from src.finance_kg.models import EntityType, RelationType, Entity, Relation, Triple


class TestEntityType:
    def test_values(self):
        assert EntityType.COMPANY.value == "Company"
        assert EntityType.PERSON.value == "Person"
        assert EntityType.LOAN.value == "Loan"
        assert EntityType.ACCOUNT.value == "Account"
        assert EntityType.SECURITY.value == "Security"
        assert EntityType.TRANSACTION.value == "Transaction"
        assert EntityType.FILING.value == "Filing"

    def test_from_value(self):
        assert EntityType("Company") == EntityType.COMPANY
        assert EntityType("Person") == EntityType.PERSON


class TestRelationType:
    def test_values(self):
        assert RelationType.HAS_LOAN.value == "HAS_LOAN"
        assert RelationType.ACQUIRED.value == "ACQUIRED"
        assert RelationType.MERGED_WITH.value == "MERGED_WITH"
        assert RelationType.COMPETES_WITH.value == "COMPETES_WITH"
        assert RelationType.FILED.value == "FILED"

    def test_from_value(self):
        assert RelationType("HAS_LOAN") == RelationType.HAS_LOAN
        assert RelationType("ACQUIRED") == RelationType.ACQUIRED


class TestEntity:
    def test_create(self):
        entity = Entity(id="e1", type=EntityType.COMPANY, name="Apple Inc.")
        assert entity.id == "e1"
        assert entity.type == EntityType.COMPANY
        assert entity.name == "Apple Inc."

    def test_create_with_properties(self):
        entity = Entity(
            id="e1",
            type=EntityType.COMPANY,
            name="Apple Inc.",
            properties={"hasTicker": "AAPL"},
        )
        assert entity.properties["hasTicker"] == "AAPL"

    def test_create_with_defaults(self):
        entity = Entity(id="e1", type=EntityType.COMPANY, name="Apple")
        assert entity.properties == {}
        assert entity.valid_from is None
        assert entity.valid_to is None
        assert entity.source == ""
        assert entity.confidence == 1.0

    def test_hash(self):
        entity = Entity(id="e1", type=EntityType.COMPANY, name="Apple")
        assert hash(entity) == hash("e1")

    def test_equality(self):
        e1 = Entity(id="e1", type=EntityType.COMPANY, name="Apple")
        e2 = Entity(id="e1", type=EntityType.COMPANY, name="Apple Inc.")
        assert e1 == e2  # Same ID

    def test_inequality(self):
        e1 = Entity(id="e1", type=EntityType.COMPANY, name="Apple")
        e2 = Entity(id="e2", type=EntityType.COMPANY, name="Microsoft")
        assert e1 != e2

    def test_inequality_different_type(self):
        e1 = Entity(id="e1", type=EntityType.COMPANY, name="Apple")
        assert e1 != "not_an_entity"


class TestRelation:
    def test_create(self):
        rel = Relation(
            id="r1",
            type=RelationType.ACQUIRED,
            source_id="e1",
            target_id="e2",
        )
        assert rel.id == "r1"
        assert rel.type == RelationType.ACQUIRED
        assert rel.source_id == "e1"
        assert rel.target_id == "e2"

    def test_create_with_defaults(self):
        rel = Relation(
            id="r1",
            type=RelationType.HAS_LOAN,
            source_id="e1",
            target_id="e2",
        )
        assert rel.properties == {}
        assert rel.valid_from is None
        assert rel.valid_to is None
        assert rel.source == ""
        assert rel.confidence == 1.0

    def test_create_with_properties(self):
        rel = Relation(
            id="r1",
            type=RelationType.ACQUIRED,
            source_id="e1",
            target_id="e2",
            properties={"amount": 3000000000},
        )
        assert rel.properties["amount"] == 3000000000


class TestTriple:
    def test_create(self):
        subject = Entity(id="e1", type=EntityType.COMPANY, name="Apple")
        obj = Entity(id="e2", type=EntityType.COMPANY, name="Beats")
        triple = Triple(subject=subject, predicate=RelationType.ACQUIRED, object=obj)
        assert triple.subject.id == "e1"
        assert triple.predicate == RelationType.ACQUIRED
        assert triple.object.id == "e2"

    def test_create_with_defaults(self):
        subject = Entity(id="e1", type=EntityType.COMPANY, name="Apple")
        obj = Entity(id="e2", type=EntityType.COMPANY, name="Beats")
        triple = Triple(subject=subject, predicate=RelationType.ACQUIRED, object=obj)
        assert triple.properties == {}
        assert triple.source == ""
        assert triple.confidence == 1.0

    def test_create_with_properties(self):
        subject = Entity(id="e1", type=EntityType.COMPANY, name="Apple")
        obj = Entity(id="e2", type=EntityType.COMPANY, name="Beats")
        triple = Triple(
            subject=subject,
            predicate=RelationType.ACQUIRED,
            object=obj,
            properties={"amount": 3000000000, "date": "2014-08-01"},
        )
        assert triple.properties["amount"] == 3000000000
