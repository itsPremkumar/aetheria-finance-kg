"""
Finance KG - Relation models and extractor.

Defines relation types and a rule-based relation extractor.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import re


class RelationType(Enum):
    ACQUIRED = "ACQUIRED"
    INVESTED_IN = "INVESTED_IN"
    MERGED_WITH = "MERGED_WITH"
    OWNS_SECURITY = "OWNS_SECURITY"
    HAS_LOAN = "HAS_LOAN"
    HAS_ACCOUNT = "HAS_ACCOUNT"
    FILED = "FILED"
    COMPETES_WITH = "COMPETES_WITH"
    SUPPLIES = "SUPPLIES"
    HAS_SUBSIDIARY = "HAS_SUBSIDIARY"
    EMPLOYS = "EMPLOYS"
    LOCATED_IN = "LOCATED_IN"


@dataclass
class Relation:
    """A relation between two entities."""
    id: str
    relation_type: RelationType
    source_id: str
    target_id: str
    properties: dict = field(default_factory=dict)
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.relation_type.value,
            "source": self.source_id,
            "target": self.target_id,
            "properties": self.properties,
            "confidence": self.confidence,
        }


class RelationExtractor:
    """Rule-based relation extraction using regex patterns."""

    # Relation patterns: (pattern, relation_type)
    PATTERNS = [
        (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+|\s+[A-Z])*(?:\s+(?:Inc\.|Corp\.|LLC|Ltd.))?)\s+acquired\s+(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+|\s+[A-Z])*(?:\s+(?:Inc\.|Corp\.|LLC|Ltd.))?)', RelationType.ACQUIRED),
        (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+|\s+[A-Z])*(?:\s+(?:Inc\.|Corp\.|LLC|Ltd.))?)\s+invested\s+in\s+(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+|\s+[A-Z])*(?:\s+(?:Inc\.|Corp\.|LLC|Ltd.))?)', RelationType.INVESTED_IN),
        (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+|\s+[A-Z])*(?:\s+(?:Inc\.|Corp\.|LLC|Ltd.))?)\s+merged\s+with\s+(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+|\s+[A-Z])*(?:\s+(?:Inc\.|Corp\.|LLC|Ltd.))?)', RelationType.MERGED_WITH),
        (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+|\s+[A-Z])*(?:\s+(?:Inc\.|Corp\.|LLC|Ltd.))?)\s+competes?\s+with\s+(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+|\s+[A-Z])*(?:\s+(?:Inc\.|Corp\.|LLC|Ltd.))?)', RelationType.COMPETES_WITH),
        (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+|\s+[A-Z])*(?:\s+(?:Inc\.|Corp\.|LLC|Ltd.))?)\s+supplies\s+(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+|\s+[A-Z])*(?:\s+(?:Inc\.|Corp\.|LLC|Ltd.))?)', RelationType.SUPPLIES),
        (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+|\s+[A-Z])*(?:\s+(?:Inc\.|Corp\.|LLC|Ltd.))?)\s+has\s+a?\s*subsidiary\s+(?:called\s+)?(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+|\s+[A-Z])*)', RelationType.HAS_SUBSIDIARY),
        (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+|\s+[A-Z])*(?:\s+(?:Inc\.|Corp\.|LLC|Ltd.))?)\s+filed\s+(a\s+)?(10-K|10-Q|8-K|S-1|13F|DEF\s*14A)', RelationType.FILED),
    ]

    def extract(self, text: str, entities: list = None) -> list[Relation]:
        """Extract relations from text."""
        relations = []

        for pattern, rel_type in self.PATTERNS:
            for match in re.finditer(pattern, text):
                source_label = match.group(1)
                target_label = match.group(2)

                # Find entity IDs from the provided entities list
                source_id = ""
                target_id = ""
                if entities:
                    for entity in entities:
                        if entity.label == source_label:
                            source_id = entity.id
                        if entity.label == target_label:
                            target_id = entity.id

                relations.append(Relation(
                    id=f"rel_{len(relations)}",
                    relation_type=rel_type,
                    source_id=source_id or source_label,
                    target_id=target_id or target_label,
                ))

        return relations
