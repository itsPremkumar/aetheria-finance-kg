"""
Finance KG - Reasoning engine.

Provides query and analysis capabilities over the knowledge graph.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class QueryResult:
    """A query result with entities and relations."""
    entity: Any
    relations: list
    score: float

    def to_dict(self) -> dict:
        return {
            "entity": self.entity.to_dict() if self.entity else None,
            "relations": [r.to_dict() for r in self.relations],
            "score": self.score,
        }


class ReasoningEngine:
    """Reasoning engine for the knowledge graph."""

    def __init__(self, graph):
        self.graph = graph

    def query(self, query: str) -> list[QueryResult]:
        """Query the knowledge graph."""
        entities = self.graph.search(query)
        results = []

        for entity in entities:
            relations = self.graph.get_relations(entity.id)
            results.append(QueryResult(
                entity=entity,
                relations=relations,
                score=1.0,
            ))

        return results

    def analyze_company(self, identifier: str) -> dict[str, Any]:
        """Analyze a company by name or ticker."""
        entities = self.graph.search(identifier)

        if not entities:
            return {"error": f"No entity found for: {identifier}"}

        # Find the company entity
        company = None
        for entity in entities:
            if entity.entity_type.value in ("Company", "Ticker"):
                company = entity
                break

        if not company:
            company = entities[0]

        relations = self.graph.get_relations(company.id)
        network = self.graph.get_network(company.id, depth=2)

        return {
            "company": company.to_dict(),
            "relations": [r.to_dict() for r in relations],
            "network": network,
            "stats": self.graph.get_stats(),
        }

    def temporal_query(
        self,
        query: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list[QueryResult]:
        """Query with temporal constraints."""
        results = self.query(query)

        if not start_date and not end_date:
            return results

        # Filter by temporal constraints (placeholder for actual date filtering)
        filtered = []
        for result in results:
            # In a full implementation, this would check entity/relation dates
            filtered.append(result)

        return filtered
