"""Finance KG — Vertical AI Knowledge Graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AssetType(Enum):
    EQUITY = "equity"
    BOND = "bond"
    ETF = "etf"
    MUTUAL_FUND = "mutual_fund"
    COMMODITY = "commodity"
    CRYPTO = "crypto"
    DERIVATIVE = "derivative"


@dataclass
class Entity:
    id: str
    type: str
    properties: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Relation:
    source_id: str
    relation_type: str
    target_id: str
    properties: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


class FinanceKG:
    """Finance Knowledge Graph with reasoning engine."""

    ENTITY_TYPES = ["Company", "Ticker", "Filing", "Instrument", "Metric", "Sector", "Portfolio", "Transaction", "RiskFactor", "Regulation"]
    RELATION_TYPES = [
        "HAS_TICKER", "ISSUED_BY", "BELONGS_TO_SECTOR", "HAS_METRIC",
        "ACQUIRED", "MERGED_WITH", "COMPETES_WITH", "SUPPLIES",
        "REGULATED_BY", "HAS_RISK", "CONTAINS", "VALUED_AT"
    ]

    def __init__(self):
        self._entities: dict[str, Entity] = {}
        self._relations: list[Relation] = []

    def add_entity(self, entity: Entity) -> None:
        self._entities[entity.id] = entity

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        return self._entities.get(entity_id)

    def find_by_type(self, entity_type: str) -> list[Entity]:
        return [e for e in self._entities.values() if e.type == entity_type]

    def find_by_property(self, key: str, value: Any) -> list[Entity]:
        return [e for e in self._entities.values() if e.properties.get(key) == value]

    def add_relation(self, relation: Relation) -> None:
        self._relations.append(relation)

    def get_relations(self, entity_id: str | None = None, relation_type: str | None = None) -> list[Relation]:
        results = []
        for r in self._relations:
            if (entity_id is None or r.source_id == entity_id or r.target_id == entity_id) and \
               (relation_type is None or r.relation_type == relation_type):
                results.append(r)
        return results

    def entity_count(self) -> int:
        return len(self._entities)

    def relation_count(self) -> int:
        return len(self._relations)

    def get_company_ticker(self, company_id: str) -> Optional[Entity]:
        for r in self._relations:
            if r.source_id == company_id and r.relation_type == "HAS_TICKER":
                return self._entities.get(r.target_id)
        return None

    def get_sector_companies(self, sector_id: str) -> list[Entity]:
        companies = []
        for r in self._relations:
            if r.target_id == sector_id and r.relation_type == "BELONGS_TO_SECTOR":
                company = self._entities.get(r.source_id)
                if company:
                    companies.append(company)
        return companies

    def get_company_metrics(self, company_id: str) -> list[Entity]:
        metrics = []
        for r in self._relations:
            if r.source_id == company_id and r.relation_type == "HAS_METRIC":
                metric = self._entities.get(r.target_id)
                if metric:
                    metrics.append(metric)
        return metrics

    def calculate_risk_score(self, company_id: str) -> dict[str, Any]:
        risk_factors = []
        for r in self._relations:
            if r.source_id == company_id and r.relation_type == "HAS_RISK":
                risk = self._entities.get(r.target_id)
                if risk:
                    risk_factors.append(risk)
        if not risk_factors:
            return {"score": 0, "level": RiskLevel.LOW.value, "factors": []}
        total = sum(r.properties.get("severity", 0) for r in risk_factors)
        avg = total / len(risk_factors)
        level = RiskLevel.LOW.value
        if avg > 7:
            level = RiskLevel.CRITICAL.value
        elif avg > 5:
            level = RiskLevel.HIGH.value
        elif avg > 3:
            level = RiskLevel.MEDIUM.value
        return {"score": avg, "level": level, "factors": [r.id for r in risk_factors]}

    def portfolio_optimization(self, portfolio_id: str) -> dict[str, Any]:
        holdings = []
        for r in self._relations:
            if r.source_id == portfolio_id and r.relation_type == "CONTAINS":
                instrument = self._entities.get(r.target_id)
                if instrument:
                    holdings.append(instrument)
        if not holdings:
            return {"diversification_score": 0, "recommendations": []}
        types = set(h.properties.get("asset_type", "unknown") for h in holdings)
        diversification = len(types) / len(AssetType)
        recommendations = []
        if diversification < 0.5:
            recommendations.append("Consider diversifying across more asset types")
        return {"diversification_score": diversification, "recommendations": recommendations}

    def fraud_detection(self, transaction_id: str) -> dict[str, Any]:
        txn = self._entities.get(transaction_id)
        if not txn:
            return {"fraud_risk": "unknown", "reasons": ["Transaction not found"]}
        amount = txn.properties.get("amount", 0)
        reasons = []
        if amount > 1000000:
            reasons.append("Large transaction amount")
        if txn.properties.get("unusual_timing"):
            reasons.append("Unusual timing pattern")
        if txn.properties.get("cross_border"):
            reasons.append("Cross-border transaction")
        risk = "high" if len(reasons) >= 2 else "medium" if len(reasons) == 1 else "low"
        return {"fraud_risk": risk, "reasons": reasons}

    def credit_risk_scoring(self, company_id: str) -> dict[str, Any]:
        metrics = self.get_company_metrics(company_id)
        if not metrics:
            return {"credit_score": 0, "rating": "N/A"}
        debt_to_equity = next((m.properties.get("value", 0) for m in metrics if m.properties.get("name") == "debt_to_equity"), 0)
        current_ratio = next((m.properties.get("value", 0) for m in metrics if m.properties.get("name") == "current_ratio"), 0)
        score = 100
        if debt_to_equity > 2:
            score -= 30
        elif debt_to_equity > 1:
            score -= 15
        if current_ratio < 1:
            score -= 20
        elif current_ratio < 1.5:
            score -= 10
        rating = "AAA" if score >= 90 else "AA" if score >= 80 else "A" if score >= 70 else "BBB" if score >= 60 else "BB" if score >= 50 else "B"
        return {"credit_score": score, "rating": rating}

    def market_trend_prediction(self, sector_id: str) -> dict[str, Any]:
        companies = self.get_sector_companies(sector_id)
        if not companies:
            return {"trend": "unknown", "confidence": 0}
        metrics_count = sum(len(self.get_company_metrics(c.id)) for c in companies)
        confidence = min(1.0, metrics_count / (len(companies) * 5))
        return {"trend": "bullish", "confidence": confidence, "sample_size": len(companies)}

    def clear(self) -> None:
        self._entities.clear()
        self._relations.clear()
