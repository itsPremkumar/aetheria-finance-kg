"""
graph/knowledge_graph.py - Core Finance Knowledge Graph.

The central RDF-backed knowledge graph that integrates data from:
- Apache Fineract (core banking: clients, loans, savings, accounting)
- OpenBB (market data: equities, ETFs, indices, fundamentals)
- SEC EDGAR filings (10-K, 10-Q, 8-K structured data)
- FIBO ontology (semantic backbone)

All data is stored locally in an RDF graph (rdflib).
Supports SPARQL queries, temporal reasoning, and graph traversal.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional, Union

from rdflib import Graph, Literal, URIRef, BNode
from rdflib.namespace import RDF, RDFS, XSD

from ..ontology.fibo import FIBOOntology
from ..ontology.namespaces import (
    FINANCE, FINERACT, OPENBB, SEC as SEC_NS, FIBO,
)


@dataclass
class Entity:
    """A financial entity in the knowledge graph."""
    uri: URIRef
    label: str
    entity_type: str
    properties: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    timestamp: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "uri": str(self.uri),
            "label": self.label,
            "type": self.entity_type,
            "properties": self.properties,
            "source": self.source,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


@dataclass
class Relation:
    """A relationship between two financial entities."""
    source_uri: URIRef
    target_uri: URIRef
    relation_type: str
    properties: dict[str, Any] = field(default_factory=dict)
    source_name: str = ""
    confidence: float = 1.0
    timestamp: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": str(self.source_uri),
            "target": str(self.target_uri),
            "relation": self.relation_type,
            "properties": self.properties,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class FinanceKnowledgeGraph:
    """
    Finance Reasoning Knowledge Graph.
    
    Integrates data from Fineract, OpenBB, and SEC filings
    into a single RDF-backed knowledge graph using FIBO as the
    semantic backbone.
    
    Usage:
        kg = FinanceKnowledgeGraph()
        
        # Add a company
        apple = kg.add_entity("Apple Inc.", "Corporation", 
                              {"hasTicker": "AAPL", "hasISIN": "037833100"})
        
        # Add a relation
        kg.add_relation(apple, microsoft, "competesWith")
        
        # Query
        results = kg.query("SELECT ?x WHERE { ?x rdf:type finance:Corporation }")
        
        # Reasoning
        peers = kg.find_peers(apple)
    """

    def __init__(self, ontology: Optional[FIBOOntology] = None) -> None:
        """Initialize the knowledge graph."""
        self.graph = Graph()
        self.ontology = ontology or FIBOOntology()
        self.ontology.merge_to_graph(self.graph)
        self._entity_count = 0
        self._relation_count = 0

    def _generate_uri(self, namespace: URIRef, label: str) -> URIRef:
        """Generate a unique URI for an entity."""
        safe_label = label.lower().replace(" ", "_").replace(".", "")[:40]
        unique_id = uuid.uuid4().hex[:8]
        return namespace[f"{safe_label}_{unique_id}"]

    def add_entity(
        self,
        label: str,
        entity_type: str,
        properties: Optional[dict[str, Any]] = None,
        namespace: Optional[URIRef] = None,
        source: str = "",
        timestamp: Optional[datetime] = None,
        uri: Optional[URIRef] = None,
    ) -> URIRef:
        """
        Add a financial entity to the graph.
        
        Args:
            label: Human-readable name
            entity_type: FIBO class name (e.g., "Corporation", "Loan")
            properties: Dict of property name -> value
            namespace: Custom namespace (defaults to FINANCE)
            source: Data source identifier
            timestamp: When this data was recorded
            uri: Optional explicit URI (auto-generated if None)
            
        Returns:
            The URI of the created entity
        """
        if namespace is None:
            namespace = FINANCE
        
        if uri is None:
            uri = self._generate_uri(namespace, label)
        
        # Add type triple
        type_uri = FINANCE[entity_type]
        self.graph.add((uri, RDF.type, type_uri))
        
        # Add label
        self.graph.add((uri, RDFS.label, Literal(label)))
        
        # Add properties
        if properties:
            for prop_name, value in properties.items():
                prop_uri = FINANCE[prop_name]
                if isinstance(value, (int, float)):
                    self.graph.add((uri, prop_uri, Literal(value)))
                elif isinstance(value, date):
                    self.graph.add((uri, prop_uri, Literal(value.isoformat(), datatype=XSD.date)))
                elif isinstance(value, datetime):
                    self.graph.add((uri, prop_uri, Literal(value.isoformat(), datatype=XSD.dateTime)))
                else:
                    self.graph.add((uri, prop_uri, Literal(str(value))))
        
        # Add provenance
        if source:
            self.graph.add((uri, FINANCE["source"], Literal(source)))
        if timestamp:
            self.graph.add(
                (uri, FINANCE["timestamp"], Literal(timestamp.isoformat(), datatype=XSD.dateTime))
            )
        
        self._entity_count += 1
        return uri

    def add_relation(
        self,
        source_uri: URIRef,
        target_uri: URIRef,
        relation_type: str,
        properties: Optional[dict[str, Any]] = None,
        confidence: float = 1.0,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Add a relationship between two entities.
        
        Args:
            source_uri: Source entity URI
            target_uri: Target entity URI
            relation_type: Property name (e.g., "acquired", "investedIn")
            properties: Optional relation properties
            confidence: Confidence score (0.0 to 1.0)
            timestamp: When this relation was established
        """
        rel_uri = FINANCE[relation_type]
        self.graph.add((source_uri, rel_uri, target_uri))
        
        if properties or confidence < 1.0 or timestamp:
            # Create a relation node for rich relations
            rel_node = BNode()
            self.graph.add((rel_node, RDF.type, FINANCE["Relation"]))
            self.graph.add((rel_node, FINANCE["relationSource"], source_uri))
            self.graph.add((rel_node, FINANCE["relationTarget"], target_uri))
            self.graph.add((rel_node, FINANCE["relationType"], Literal(relation_type)))
            
            if confidence < 1.0:
                self.graph.add((rel_node, FINANCE["confidence"], Literal(confidence)))
            if timestamp:
                self.graph.add(
                    (rel_node, FINANCE["timestamp"], Literal(timestamp.isoformat(), datatype=XSD.dateTime))
                )
            if properties:
                for k, v in properties.items():
                    self.graph.add((rel_node, FINANCE[k], Literal(str(v))))
        
        self._relation_count += 1

    def query(self, sparql: str) -> list[dict[str, Any]]:
        """
        Execute a SPARQL query against the knowledge graph.
        
        Args:
            sparql: SPARQL query string
            
        Returns:
            List of result bindings as dicts
        """
        results = []
        try:
            qres = self.graph.query(sparql)
            for row in qres:
                binding = {}
                for var in qres.vars:
                    val = row[var]
                    if isinstance(val, Literal):
                        binding[str(var)] = str(val)
                    else:
                        binding[str(var)] = str(val)
                results.append(binding)
        except Exception as e:
            results.append({"error": str(e)})
        return results

    def get_entity(self, uri: Union[str, URIRef]) -> Optional[Entity]:
        """Get a full entity by URI."""
        if isinstance(uri, str):
            uri = URIRef(uri)
        
        label = str(self.graph.value(uri, RDFS.label) or "")
        if not label:
            return None
        
        entity_type = ""
        for _, _, type_uri in self.graph.triples((uri, RDF.type, None)):
            type_name = str(type_uri).split("/")[-1]
            if type_name not in ("Class", "NamedIndividual"):
                entity_type = type_name
                break
        
        properties: dict[str, Any] = {}
        for _, prop_uri, val in self.graph.triples((uri, None, None)):
            if prop_uri not in (RDF.type, RDFS.label):
                prop_name = str(prop_uri).split("/")[-1]
                properties[prop_name] = str(val)
        
        source = str(self.graph.value(uri, FINANCE.source) or "")
        ts_str = str(self.graph.value(uri, FINANCE.timestamp) or "")
        timestamp = datetime.fromisoformat(ts_str) if ts_str else None
        
        return Entity(
            uri=uri, label=label, entity_type=entity_type,
            properties=properties, source=source, timestamp=timestamp,
        )

    def get_relations(
        self, uri: Union[str, URIRef], direction: str = "both"
    ) -> list[Relation]:
        """Get all relations for an entity."""
        if isinstance(uri, str):
            uri = URIRef(uri)
        
        relations: list[Relation] = []
        
        if direction in ("outgoing", "both"):
            for _, prop, target in self.graph.triples((uri, None, None)):
                if prop not in (RDF.type, RDFS.label, FINANCE.source, FINANCE.timestamp):
                    relations.append(Relation(
                        source_uri=uri,
                        target_uri=target,
                        relation_type=str(prop).split("/")[-1],
                    ))
        
        if direction in ("incoming", "both"):
            for source, prop, _ in self.graph.triples((None, None, uri)):
                if prop not in (RDF.type, RDFS.label, FINANCE.source, FINANCE.timestamp):
                    relations.append(Relation(
                        source_uri=source,
                        target_uri=uri,
                        relation_type=str(prop).split("/")[-1],
                    ))
        
        return relations

    def find_peers(self, uri: Union[str, URIRef]) -> list[URIRef]:
        """Find peer companies (direct competitors)."""
        if isinstance(uri, str):
            uri = URIRef(uri)
        
        peers: list[URIRef] = []
        for _, _, target in self.graph.triples((uri, FINANCE.competesWith, None)):
            peers.append(target)
        for source, _, _ in self.graph.triples((None, FINANCE.competesWith, uri)):
            peers.append(source)
        return peers

    def find_investors(self, uri: Union[str, URIRef]) -> list[URIRef]:
        """Find all investors in a given entity."""
        if isinstance(uri, str):
            uri = URIRef(uri)
        
        investors: list[URIRef] = []
        for source, _, _ in self.graph.triples((None, FINANCE.investedIn, uri)):
            investors.append(source)
        for source, _, _ in self.graph.triples((None, FINANCE.holdsStake, uri)):
            investors.append(source)
        return investors

    def find_subsidiaries(self, uri: Union[str, URIRef]) -> list[URIRef]:
        """Find all subsidiaries of a given entity."""
        if isinstance(uri, str):
            uri = URIRef(uri)
        
        subs: list[URIRef] = []
        for _, _, target in self.graph.triples((uri, FINANCE.parentOf, None)):
            subs.append(target)
        for _, _, target in self.graph.triples((None, FINANCE.subsidiaryOf, uri)):
            subs.append(target)
        return subs

    def temporal_query(
        self,
        entity_uri: Union[str, URIRef],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[dict[str, Any]]:
        """
        Query entity data within a time range.
        
        Args:
            entity_uri: Entity to query
            start_date: Start of time range (inclusive)
            end_date: End of time range (inclusive)
            
        Returns:
            List of temporal data points
        """
        if isinstance(entity_uri, str):
            entity_uri = URIRef(entity_uri)
        
        results: list[dict[str, Any]] = []
        for _, prop, val in self.graph.triples((entity_uri, None, None)):
            if prop in (RDF.type, RDFS.label, FINANCE.source, FINANCE.timestamp):
                continue
            ts = self.graph.value(entity_uri, FINESTAMP)
            if ts:
                try:
                    ts_date = date.fromisoformat(str(ts))
                    if start_date and ts_date < start_date:
                        continue
                    if end_date and ts_date > end_date:
                        continue
                except ValueError:
                    pass
            results.append({
                "property": str(prop).split("/")[-1],
                "value": str(val),
            })
        return results

    def get_statistics(self) -> dict[str, int]:
        """Get graph statistics."""
        entity_count = len(set(self.graph.subjects(RDF.type, None)) - 
                          set([FINANCE[c] for c in self.ontology.CORE_CLASSES]))
        relation_count = len(list(self.graph.objects(None, None))) - entity_count * 2
        return {
            "total_triples": len(self.graph),
            "entities": max(0, entity_count),
            "relations": max(0, self._relation_count),
            "classes": len(self.ontology.get_all_classes()),
            "properties": len(self.ontology.get_all_properties()),
        }

    def export(self, format: str = "turtle") -> str:
        """Export the knowledge graph as RDF."""
        return self.graph.serialize(format=format)

    def export_to_file(self, path: Union[str, Path], format: str = "turtle") -> None:
        """Export knowledge graph to a file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.export(format=format))

    def save(self, path: Union[str, Path]) -> None:
        """Save the knowledge graph to a file (Turtle format)."""
        self.export_to_file(path, format="turtle")

    @classmethod
    def load(cls, path: Union[str, Path]) -> "FinanceKnowledgeGraph":
        """Load a knowledge graph from a file."""
        kg = cls()
        kg.graph.parse(str(path), format="turtle")
        return kg

    def merge(self, other: "FinanceKnowledgeGraph") -> None:
        """Merge another knowledge graph into this one."""
        self.graph += other.graph
        self._entity_count += other._entity_count
        self._relation_count += other._relation_count

    def __len__(self) -> int:
        return len(self.graph)

    def __repr__(self) -> str:
        stats = self.get_statistics()
        return (f"FinanceKnowledgeGraph(entities={stats['entities']}, "
                f"relations={stats['relations']}, triples={stats['total_triples']})")
