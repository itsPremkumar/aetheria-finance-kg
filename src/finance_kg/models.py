"""Entity and relation models for the Finance Knowledge Graph."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class EntityType(str, Enum):
    """Types of entities in the finance KG."""

    COMPANY = "Company"
    PERSON = "Person"
    LOAN = "Loan"
    ACCOUNT = "Account"
    SECURITY = "Security"
    TRANSACTION = "Transaction"
    FILING = "Filing"


class RelationType(str, Enum):
    """Types of relations in the finance KG."""

    HAS_LOAN = "HAS_LOAN"
    HAS_ACCOUNT = "HAS_ACCOUNT"
    OWNS_SECURITY = "OWNS_SECURITY"
    ACQUIRED = "ACQUIRED"
    MERGED_WITH = "MERGED_WITH"
    INVESTED_IN = "INVESTED_IN"
    COMPETES_WITH = "COMPETES_WITH"
    SUPPLIES = "SUPPLIES"
    HAS_SUBSIDIARY = "HAS_SUBSIDIARY"
    FILED = "FILED"


class Entity(BaseModel):
    """A node in the knowledge graph."""

    id: str
    type: EntityType
    name: str
    properties: dict[str, Any] = Field(default_factory=dict)
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    source: str = ""
    confidence: float = 1.0

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        return self.id == other.id


class Relation(BaseModel):
    """An edge in the knowledge graph."""

    id: str
    type: RelationType
    source_id: str
    target_id: str
    properties: dict[str, Any] = Field(default_factory=dict)
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    source: str = ""
    confidence: float = 1.0


class Triple(BaseModel):
    """A subject-predicate-object triple extracted from data."""

    subject: Entity
    predicate: RelationType
    object: Entity
    properties: dict[str, Any] = Field(default_factory=dict)
    source: str = ""
    confidence: float = 1.0
