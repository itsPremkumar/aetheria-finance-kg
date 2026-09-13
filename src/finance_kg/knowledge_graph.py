"""Knowledge Graph builder using NetworkX."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import networkx as nx

from .models import Entity, Relation, Triple


class KnowledgeGraph:
    """In-memory knowledge graph backed by NetworkX."""

    def __init__(self):
        self.graph = nx.DiGraph()
        self._entity_map: dict[str, Entity] = {}

    def add_entity(self, entity: Entity) -> None:
        """Add an entity as a node."""
        self._entity_map[entity.id] = entity
        self.graph.add_node(
            entity.id,
            **entity.model_dump(exclude={"id"}),
        )

    def add_relation(self, relation: Relation) -> None:
        """Add a relation as an edge."""
        self.graph.add_edge(
            relation.source_id,
            relation.target_id,
            **relation.model_dump(exclude={"id", "source_id", "target_id"}),
        )

    def add_triple(self, triple: Triple) -> None:
        """Add a triple (subject-predicate-object) to the graph."""
        self.add_entity(triple.subject)
        self.add_entity(triple.object)
        relation = Relation(
            id=f"rel_{triple.subject.id}_{triple.object.id}",
            type=triple.predicate,
            source_id=triple.subject.id,
            target_id=triple.object.id,
            properties=triple.properties,
            source=triple.source,
            confidence=triple.confidence,
        )
        self.add_relation(relation)

    def add_triples(self, triples: list[Triple]) -> None:
        """Add multiple triples."""
        for triple in triples:
            self.add_triple(triple)

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Retrieve an entity by ID."""
        return self._entity_map.get(entity_id)

    def find_entities_by_type(self, entity_type: str) -> list[Entity]:
        """Find all entities of a given type."""
        return [
            e for e in self._entity_map.values() if e.type.value == entity_type
        ]

    def find_entities_by_name(self, name: str) -> list[Entity]:
        """Find entities matching a name (case-insensitive)."""
        name_lower = name.lower()
        return [
            e for e in self._entity_map.values() if name_lower in e.name.lower()
        ]

    def find_relations(
        self,
        entity_id: Optional[str] = None,
        relation_type: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Find relations, optionally filtered by entity or type."""
        results = []
        for src, tgt, data in self.graph.edges(data=True):
            if entity_id and src != entity_id and tgt != entity_id:
                continue
            if relation_type and data.get("type") != relation_type:
                continue
            results.append(
                {
                    "source": self._entity_map.get(src),
                    "target": self._entity_map.get(tgt),
                    "relation": data,
                }
            )
        return results

    def query(
        self,
        entity_type: Optional[str] = None,
        relation_type: Optional[str] = None,
        name_contains: Optional[str] = None,
    ) -> list[Triple]:
        """Query the knowledge graph with filters."""
        results = []
        for src, tgt, data in self.graph.edges(data=True):
            source_entity = self._entity_map.get(src)
            target_entity = self._entity_map.get(tgt)
            if source_entity is None or target_entity is None:
                continue

            if entity_type:
                if (
                    source_entity.type.value != entity_type
                    and target_entity.type.value != entity_type
                ):
                    continue

            if relation_type and data.get("type") != relation_type:
                continue

            if name_contains:
                nc = name_contains.lower()
                if (
                    nc not in source_entity.name.lower()
                    and nc not in target_entity.name.lower()
                ):
                    continue

            results.append(
                Triple(
                    subject=source_entity,
                    predicate=RelationType(data.get("type", "FILED")),
                    object=target_entity,
                    properties=data.get("properties", {}),
                    source=data.get("source", ""),
                    confidence=data.get("confidence", 1.0),
                )
            )
        return results

    def stats(self) -> dict[str, int]:
        """Return graph statistics."""
        return {
            "entities": self.graph.number_of_nodes(),
            "relations": self.graph.number_of_edges(),
        }

    def export_json(self, path: str | Path) -> None:
        """Export the graph to JSON."""
        data = {
            "entities": [e.model_dump() for e in self._entity_map.values()],
            "relations": [
                {
                    "source_id": src,
                    "target_id": tgt,
                    **data,
                }
                for src, tgt, data in self.graph.edges(data=True)
            ],
        }
        Path(path).write_text(json.dumps(data, indent=2, default=str))

    def import_json(self, path: str | Path) -> None:
        """Import a graph from JSON."""
        data = json.loads(Path(path).read_text())
        for ent_data in data.get("entities", []):
            entity = Entity(**ent_data)
            self.add_entity(entity)
        for rel_data in data.get("relations", []):
            relation = Relation(
                id=f"rel_{rel_data['source_id']}_{rel_data['target_id']}",
                type=RelationType(rel_data["type"]),
                source_id=rel_data["source_id"],
                target_id=rel_data["target_id"],
                properties=rel_data.get("properties", {}),
                source=rel_data.get("source", ""),
                confidence=rel_data.get("confidence", 1.0),
            )
            self.add_relation(relation)
