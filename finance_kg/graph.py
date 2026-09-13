"""
Finance KG - Knowledge graph module.

In-memory graph with adjacency indexes, search, and network traversal.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
import json


@dataclass
class GraphConfig:
    """Configuration for the knowledge graph."""
    directed: bool = True
    weighted: bool = False
    temporal: bool = True


class KnowledgeGraph:
    """In-memory knowledge graph with adjacency list representation."""

    def __init__(self, db_path: str = ":memory:", config: Optional[GraphConfig] = None):
        self.db_path = db_path
        self.config = config or GraphConfig()
        self._entities: dict[str, Any] = {}
        self._relations: dict[str, Any] = {}
        self._adjacency: dict[str, list[str]] = {}  # entity_id -> [relation_id]
        self._reverse_adjacency: dict[str, list[str]] = {}  # entity_id -> [relation_id]

    def add_entities(self, entities: list):
        """Add entities to the graph."""
        for entity in entities:
            self._entities[entity.id] = entity
            if entity.id not in self._adjacency:
                self._adjacency[entity.id] = []
            if entity.id not in self._reverse_adjacency:
                self._reverse_adjacency[entity.id] = []

    def add_relations(self, relations: list):
        """Add relations to the graph."""
        for relation in relations:
            self._relations[relation.id] = relation
            # Add to adjacency
            if relation.source_id in self._adjacency:
                self._adjacency[relation.source_id].append(relation.id)
            # Add to reverse adjacency
            if relation.target_id in self._reverse_adjacency:
                self._reverse_adjacency[relation.target_id].append(relation.id)

    def get_entity(self, entity_id: str) -> Optional[Any]:
        """Get an entity by ID."""
        return self._entities.get(entity_id)

    def get_relation(self, relation_id: str) -> Optional[Any]:
        """Get a relation by ID."""
        return self._relations.get(relation_id)

    def get_relations(self, entity_id: str) -> list:
        """Get all relations for an entity."""
        relation_ids = self._adjacency.get(entity_id, []) + self._reverse_adjacency.get(entity_id, [])
        return [self._relations[rid] for rid in relation_ids]

    def search(self, query: str, entity_type: Optional[str] = None) -> list:
        """Search entities by label or type."""
        results = []
        for entity in self._entities.values():
            if query.lower() in entity.label.lower():
                if entity_type and entity.entity_type.value != entity_type:
                    continue
                results.append(entity)
        return results

    def get_network(self, entity_id: str, depth: int = 2) -> dict[str, Any]:
        """Get the relationship network for an entity up to a given depth."""
        visited = set()
        nodes = []
        edges = []

        def _explore(eid: str, d: int):
            if d > depth or eid in visited:
                return
            visited.add(eid)
            entity = self._entities.get(eid)
            if entity:
                nodes.append(entity.to_dict())
            for relation in self.get_relations(eid):
                edges.append(relation.to_dict())
                next_id = relation.target_id if relation.source_id == eid else relation.source_id
                _explore(next_id, d + 1)

        _explore(entity_id, 0)
        return {"nodes": nodes, "edges": edges}

    def get_stats(self) -> dict[str, int]:
        """Get graph statistics."""
        return {
            "entities": len(self._entities),
            "relations": len(self._relations),
        }

    def export_json(self, output_path: str):
        """Export the graph to JSON."""
        data = {
            "entities": [e.to_dict() for e in self._entities.values()],
            "relations": [r.to_dict() for r in self._relations.values()],
        }
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

    def import_json(self, input_path: str):
        """Import the graph from JSON."""
        with open(input_path) as f:
            data = json.load(f)

        # Reconstruct entities
        for entity_data in data.get("entities", []):
            entity = Entity(
                id=entity_data["id"],
                entity_type=EntityType(entity_data["type"]),
                label=entity_data["label"],
                properties=entity_data.get("properties", {}),
                source=entity_data.get("source", ""),
                confidence=entity_data.get("confidence", 1.0),
            )
            self.add_entities([entity])

        # Reconstruct relations
        for relation_data in data.get("relations", []):
            relation = Relation(
                id=relation_data["id"],
                relation_type=RelationType(relation_data["type"]),
                source_id=relation_data["source"],
                target_id=relation_data["target"],
                properties=relation_data.get("properties", {}),
                confidence=relation_data.get("confidence", 1.0),
            )
            self.add_relations([relation])

    def close(self):
        """Close the graph (no-op for in-memory)."""
        pass


# Re-import for import_json usage
from .entities import Entity, EntityType
from .relations import Relation, RelationType
