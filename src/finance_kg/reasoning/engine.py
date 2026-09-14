"""
reasoning/engine.py - Financial reasoning engine.

Provides reasoning capabilities over the Finance Knowledge Graph:
- Company relationship reasoning (peers, subsidiaries, supply chain)
- Financial metric reasoning (trends, ratios, comparisons)
- Temporal reasoning (quarterly/yearly changes)
- Risk propagation reasoning
- Investment reasoning (who invests in whom, portfolio analysis)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Optional

from rdflib import URIRef

from ..graph.knowledge_graph import FinanceKnowledgeGraph
from ..ontology.namespaces import FINANCE

logger = logging.getLogger(__name__)


@dataclass
class ReasoningResult:
    """Result of a reasoning query."""
    query: str
    result_type: str
    entities: list[dict[str, Any]] = field(default_factory=list)
    relations: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    explanation: str = ""
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "result_type": self.result_type,
            "entities": self.entities,
            "relations": self.relations,
            "metrics": self.metrics,
            "explanation": self.explanation,
            "confidence": self.confidence,
        }


class FinancialReasoningEngine:
    """
    Reasoning engine for financial analysis.
    
    Provides:
    - Peer analysis (find similar companies)
    - Relationship path finding (who owns whom)
    - Financial ratio computation (PE, ROE, debt-to-equity)
    - Temporal trend analysis
    - Risk scoring
    - Investment flow analysis
    
    Usage:
        kg = FinanceKnowledgeGraph()
        engine = FinancialReasoningEngine(kg)
        
        result = engine.find_peers("AAPL")
        result = engine.analyze_financials("MSFT")
        result = engine.investment_flows("GOOGL")
    """

    def __init__(self, kg: FinanceKnowledgeGraph) -> None:
        self.kg = kg

    def find_peers(self, ticker: str) -> ReasoningResult:
        """
        Find peer companies for a given ticker.
        
        Peers are companies in the same sector that compete with
        the given company or are similar in market cap.
        """
        # Find the entity URI for the ticker
        entity_uri = self._find_entity_by_ticker(ticker)
        if entity_uri is None:
            return ReasoningResult(
                query=f"peers of {ticker}",
                result_type="peer_analysis",
                explanation=f"Company with ticker {ticker} not found in knowledge graph.",
                confidence=0.0,
            )
        
        # Get direct competitors
        peer_uris = self.kg.find_peers(entity_uri)
        
        # Get sector from entity
        sector = ""
        for _, _, val in self.kg.graph.triples((entity_uri, FINANCE.sector, None)):
            sector = str(val)
            break
        
        # If no direct competitors, find companies in same sector
        if not peer_uris and sector:
            peer_uris = self._find_companies_by_sector(sector, exclude=entity_uri)
        
        entities = []
        for uri in peer_uris:
            entity = self.kg.get_entity(uri)
            if entity:
                entities.append(entity.to_dict())
        
        return ReasoningResult(
            query=f"peers of {ticker}",
            result_type="peer_analysis",
            entities=entities,
            explanation=f"Found {len(entities)} peer companies"
            + (f" in {sector} sector" if sector else "") + ".",
            confidence=0.8 if entities else 0.3,
        )

    def analyze_financials(self, ticker: str) -> ReasoningResult:
        """
        Analyze financial metrics for a company.
        
        Computes key financial ratios from available data:
        - ROE (Return on Equity)
        - ROA (Return on Assets)
        - Debt-to-Equity Ratio
        - Net Profit Margin
        """
        entity_uri = self._find_entity_by_ticker(ticker)
        if entity_uri is None:
            return ReasoningResult(
                query=f"financial analysis of {ticker}",
                result_type="financial_analysis",
                explanation=f"Company with ticker {ticker} not found.",
                confidence=0.0,
            )
        
        # Gather financial data from all related statements
        financial_data: dict[str, float] = {}
        for rel in self.kg.get_relations(entity_uri, direction="outgoing"):
            if "financial" in rel.relation_type.lower() or "statement" in rel.relation_type.lower():
                stmt = self.kg.get_entity(rel.target_uri)
                if stmt:
                    for k, v in stmt.properties.items():
                        try:
                            financial_data[k] = float(v)
                        except (ValueError, TypeError):
                            pass
        
        # Also get direct properties
        entity = self.kg.get_entity(entity_uri)
        if entity:
            for k, v in entity.properties.items():
                if k in ("hasRevenue", "hasNetIncome", "hasTotalAssets", "hasTotalLiabilities"):
                    try:
                        financial_data[k] = float(v)
                    except (ValueError, TypeError):
                        pass
        
        # Compute ratios
        metrics: dict[str, Any] = {}
        net_income = financial_data.get("net_income") or financial_data.get("hasNetIncome", 0)
        total_assets = financial_data.get("total_assets") or financial_data.get("hasTotalAssets", 0)
        total_liabilities = financial_data.get("total_liabilities") or financial_data.get("hasTotalLiabilities", 0)
        total_equity = financial_data.get("total_equity") or (total_assets - total_liabilities if total_assets else 0)
        revenue = financial_data.get("total_revenue") or financial_data.get("hasRevenue", 0)
        
        if net_income and total_equity:
            metrics["roe"] = round(net_income / total_equity * 100, 2)
        if net_income and total_assets:
            metrics["roa"] = round(net_income / total_assets * 100, 2)
        if total_liabilities and total_equity:
            metrics["debt_to_equity"] = round(total_liabilities / total_equity, 2)
        if net_income and revenue:
            metrics["net_profit_margin"] = round(net_income / revenue * 100, 2)
        
        # Add raw data
        for k, v in financial_data.items():
            metrics[f"raw_{k}"] = v
        
        return ReasoningResult(
            query=f"financial analysis of {ticker}",
            result_type="financial_analysis",
            entities=[entity.to_dict()] if entity else [],
            metrics=metrics,
            explanation=f"Computed {len([k for k in metrics if not k.startswith('raw_')])} financial ratios.",
            confidence=0.7 if metrics else 0.2,
        )

    def investment_flows(self, ticker: str) -> ReasoningResult:
        """
        Analyze investment flows into a company.
        
        Identifies:
        - Direct investors
        - Parent companies (who owns whom)
        - Insider trading activity
        - Institutional holdings
        """
        entity_uri = self._find_entity_by_ticker(ticker)
        if entity_uri is None:
            return ReasoningResult(
                query=f"investment flows for {ticker}",
                result_type="investment_analysis",
                explanation=f"Company with ticker {ticker} not found.",
                confidence=0.0,
            )
        
        # Find investors
        investors = self.kg.find_investors(entity_uri)
        investor_entities = []
        for uri in investors:
            entity = self.kg.get_entity(uri)
            if entity:
                investor_entities.append(entity.to_dict())
        
        # Find parent/subsidiary relationships
        parents = []
        for _, prop, target in self.kg.graph.triples((entity_uri, FINANCE.subsidiaryOf, None)):
            parent = self.kg.get_entity(target)
            if parent:
                parents.append(parent.to_dict())
        
        subsidiaries = self.kg.find_subsidiaries(entity_uri)
        subsidiary_entities = []
        for uri in subsidiaries:
            entity = self.kg.get_entity(uri)
            if entity:
                subsidiary_entities.append(entity.to_dict())
        
        # Insider transactions
        insider_txs = []
        for rel in self.kg.get_relations(entity_uri, direction="incoming"):
            if "insider" in rel.relation_type.lower():
                tx = self.kg.get_entity(rel.source_uri)
                if tx:
                    insider_txs.append(tx.to_dict())
        
        relations_data = (
            [{"type": "investor", "entity": e} for e in investor_entities]
            + [{"type": "parent", "entity": e} for e in parents]
            + [{"type": "subsidiary", "entity": e} for e in subsidiary_entities]
            + [{"type": "insider_transaction", "entity": e} for e in insider_txs]
        )
        
        entity = self.kg.get_entity(entity_uri)
        return ReasoningResult(
            query=f"investment flows for {ticker}",
            result_type="investment_analysis",
            entities=investor_entities + ([entity.to_dict()] if entity else []),
            relations=relations_data,
            metrics={
                "num_investors": len(investors),
                "num_parents": len(parents),
                "num_subsidiaries": len(subsidiaries),
                "num_insider_transactions": len(insider_txs),
            },
            explanation=(f"Found {len(investors)} investors, {len(parents)} parent companies, "
                         f"{len(subsidiaries)} subsidiaries, {len(insider_txs)} insider transactions."),
            confidence=0.75,
        )

    def find_relationship_path(
        self, source_ticker: str, target_ticker: str, max_depth: int = 4
    ) -> ReasoningResult:
        """
        Find the relationship path between two companies.
        
        Uses BFS to find shortest path through the knowledge graph.
        """
        source_uri = self._find_entity_by_ticker(source_ticker)
        target_uri = self._find_entity_by_ticker(target_ticker)
        
        if source_uri is None or target_uri is None:
            return ReasoningResult(
                query=f"path from {source_ticker} to {target_ticker}",
                result_type="relationship_path",
                explanation=f"One or both companies not found.",
                confidence=0.0,
            )
        
        # BFS
        visited: set[str] = set()
        queue: list[tuple[URIRef, list[dict[str, Any]]]] = [(source_uri, [])]
        
        while queue:
            current, path = queue.pop(0)
            current_str = str(current)
            
            if current_str in visited:
                continue
            visited.add(current_str)
            
            if current == target_uri:
                return ReasoningResult(
                    query=f"path from {source_ticker} to {target_ticker}",
                    result_type="relationship_path",
                    relations=path,
                    explanation=f"Found path of length {len(path)}.",
                    confidence=0.9,
                )
            
            if len(path) >= max_depth:
                continue
            
            # Traverse relations
            for rel in self.kg.get_relations(current, direction="outgoing"):
                target_str = str(rel.target_uri)
                if target_str not in visited:
                    new_path = path + [{
                        "from": str(rel.source_uri),
                        "relation": rel.relation_type,
                        "to": str(rel.target_uri),
                    }]
                    queue.append((rel.target_uri, new_path))
        
        return ReasoningResult(
            query=f"path from {source_ticker} to {target_ticker}",
            result_type="relationship_path",
            explanation=f"No path found within {max_depth} hops.",
            confidence=0.1,
        )

    def temporal_analysis(self, ticker: str, years: int = 5) -> ReasoningResult:
        """
        Perform temporal analysis of financial metrics over time.
        
        Analyzes how key metrics have changed over the specified period.
        """
        entity_uri = self._find_entity_by_ticker(ticker)
        if entity_uri is None:
            return ReasoningResult(
                query=f"temporal analysis of {ticker}",
                result_type="temporal_analysis",
                explanation=f"Company with ticker {ticker} not found.",
                confidence=0.0,
            )
        
        # Get all financial statements
        statements = []
        for rel in self.kg.get_relations(entity_uri, direction="outgoing"):
            if "statement" in rel.relation_type.lower() or "earnings" in rel.relation_type.lower():
                stmt = self.kg.get_entity(rel.target_uri)
                if stmt:
                    statements.append(stmt)
        
        # Sort by date if available
        statements.sort(key=lambda s: s.timestamp or datetime.min, reverse=True)
        
        # Extract metrics over time
        temporal_data: list[dict[str, Any]] = []
        for stmt in statements[:years*4]:  # Up to 4 quarters per year
            data_point: dict[str, Any] = {
                "label": stmt.label,
                "timestamp": stmt.timestamp.isoformat() if stmt.timestamp else None,
            }
            for k, v in stmt.properties.items():
                try:
                    data_point[k] = float(v)
                except (ValueError, TypeError):
                    data_point[k] = v
            temporal_data.append(data_point)
        
        return ReasoningResult(
            query=f"temporal analysis of {ticker}",
            result_type="temporal_analysis",
            metrics={
                "num_data_points": len(temporal_data),
                "period_years": years,
                "data": temporal_data,
            },
            explanation=f"Found {len(temporal_data)} financial data points over {years} years.",
            confidence=0.7,
        )

    def risk_analysis(self, ticker: str) -> ReasoningResult:
        """
        Analyze risk factors for a company.
        
        Extracts and scores risk disclosures from SEC filings.
        """
        entity_uri = self._find_entity_by_ticker(ticker)
        if entity_uri is None:
            return ReasoningResult(
                query=f"risk analysis of {ticker}",
                result_type="risk_analysis",
                explanation=f"Company with ticker {ticker} not found.",
                confidence=0.0,
            )
        
        # Find risk disclosures
        risk_disclosures = []
        for rel in self.kg.get_relations(entity_uri, direction="outgoing"):
            if "risk" in rel.relation_type.lower():
                risk = self.kg.get_entity(rel.target_uri)
                if risk:
                    risk_disclosures.append(risk)
        
        # Score risks
        risk_scores: dict[str, Any] = {}
        total_risks = 0
        for disclosure in risk_disclosures:
            risk_count = disclosure.properties.get("riskCount", 0)
            total_risks += int(risk_count) if risk_count else 0
        
        risk_scores["total_risk_factors"] = total_risks
        risk_scores["num_disclosures"] = len(risk_disclosures)
        risk_scores["risk_level"] = (
            "HIGH" if total_risks > 50 else
            "MEDIUM" if total_risks > 20 else
            "LOW"
        )
        
        return ReasoningResult(
            query=f"risk analysis of {ticker}",
            result_type="risk_analysis",
            entities=[d.to_dict() for d in risk_disclosures],
            metrics=risk_scores,
            explanation=f"Found {len(risk_disclosures)} risk disclosures with {total_risks} total risk factors.",
            confidence=0.6,
        )

    # ---- Helper Methods ----

    def _find_entity_by_ticker(self, ticker: str) -> Optional[URIRef]:
        """Find an entity URI by its ticker symbol."""
        for s, p, o in self.kg.graph.triples((None, FINANCE.hasTicker, None)):
            if str(o).upper() == ticker.upper():
                return s
        return None

    def _find_companies_by_sector(self, sector: str, exclude: Optional[URIRef] = None) -> list[URIRef]:
        """Find all companies in a given sector."""
        companies: list[URIRef] = []
        for s, p, o in self.kg.graph.triples((None, FINANCE.sector, None)):
            if str(o).lower() == sector.lower() and s != exclude:
                companies.append(s)
        return companies
