"""DORA Metrics Calculator — production implementation."""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum


class DeploymentStatus(Enum):
    SUCCESS = "success"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"
    INCIDENT = "incident"


@dataclass
class Deployment:
    id: str
    timestamp: datetime
    status: DeploymentStatus
    service: str
    version: str
    author: str
    commit_hash: str
    rollback_reason: Optional[str] = None


@dataclass
class Incident:
    id: str
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    severity: str = "medium"
    description: str = ""
    deployment_id: Optional[str] = None


@dataclass
class WorkItem:
    id: str
    title: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    wait_time_hours: float = 0.0
    assignee: str = ""
    team: str = ""
    type: str = "feature"


@dataclass
class Survey:
    employee_id: str
    score: int
    training_hours: float = 0.0
    satisfaction: int = 0
    period: str = ""


@dataclass
class HoursData:
    employee_id: str
    hours_per_week: float
    overtime_hours: float = 0.0
    week_start: str = ""


class DORACalculator:
    """Calculate all 4 DORA metrics."""

    def __init__(self, deployments: List[Deployment], incidents: List[Incident]):
        self.deployments = sorted(deployments, key=lambda d: d.timestamp)
        self.incidents = sorted(incidents, key=lambda i: i.detected_at)

    def deployment_frequency(self, period_weeks: int = 4) -> Dict[str, Any]:
        cutoff = datetime.now() - timedelta(weeks=period_weeks)
        recent = [d for d in self.deployments if d.timestamp >= cutoff]
        total_freq = len(recent) / period_weeks
        service_counts: Dict[str, int] = {}
        for d in recent:
            service_counts[d.service] = service_counts.get(d.service, 0) + 1
        per_service = {s: round(c / period_weeks, 2) for s, c in service_counts.items()}
        return {"total_per_week": round(total_freq, 2), "per_service": per_service, "total_deploys": len(recent)}

    def lead_time_for_changes(self, commit_timestamps: Dict[str, datetime]) -> Dict[str, float]:
        results = {}
        for deploy in self.deployments:
            if deploy.commit_hash in commit_timestamps:
                lead = (deploy.timestamp - commit_timestamps[deploy.commit_hash]).total_seconds() / 86400
                results[deploy.id] = round(lead, 2)
        if not results:
            return {"avg_days": 0.0, "max_days": 0.0, "min_days": 0.0}
        values = list(results.values())
        return {"avg_days": round(sum(values) / len(values), 2), "max_days": round(max(values), 2), "min_days": round(min(values), 2)}

    def change_failure_rate(self, period_weeks: int = 4) -> Dict[str, Any]:
        cutoff = datetime.now() - timedelta(weeks=period_weeks)
        recent = [d for d in self.deployments if d.timestamp >= cutoff]
        if not recent:
            return {"rate_pct": 0.0, "failed": 0, "total": 0}
        failed = sum(1 for d in recent if d.status in (DeploymentStatus.ROLLED_BACK, DeploymentStatus.FAILED, DeploymentStatus.INCIDENT))
        return {"rate_pct": round((failed / len(recent)) * 100, 2), "failed": failed, "total": len(recent)}

    def mttr(self, period_weeks: int = 4) -> Dict[str, Any]:
        cutoff = datetime.now() - timedelta(weeks=period_weeks)
        recent = [i for i in self.incidents if i.detected_at >= cutoff and i.resolved_at]
        if not recent:
            return {"avg_hours": 0.0, "total_incidents": 0}
        total_recovery = sum((i.resolved_at - i.detected_at).total_seconds() / 3600 for i in recent)
        return {"avg_hours": round(total_recovery / len(recent), 2), "total_incidents": len(recent)}

    def report(self) -> Dict[str, Any]:
        return {"deployment_frequency": self.deployment_frequency(), "change_failure_rate": self.change_failure_rate(), "mttr": self.mttr()}


class FlowCalculator:
    """Flow efficiency metrics."""

    def __init__(self, work_items: List[WorkItem]):
        self.work_items = work_items

    def cycle_time(self, team: Optional[str] = None) -> Dict[str, Any]:
        items = self.work_items if not team else [w for w in self.work_items if w.team == team]
        times = []
        for item in items:
            if item.completed_at and item.started_at:
                times.append((item.completed_at - item.started_at).total_seconds() / 86400)
        if not times:
            return {"avg_days": 0.0, "p95_days": 0.0, "count": 0}
        times.sort()
        p95_idx = int(len(times) * 0.95)
        return {"avg_days": round(sum(times) / len(times), 2), "p95_days": round(times[min(p95_idx, len(times) - 1)], 2), "count": len(times)}

    def work_in_progress(self, team: Optional[str] = None) -> Dict[str, Any]:
        items = self.work_items if not team else [w for w in self.work_items if w.team == team]
        in_progress = [w for w in items if w.status == "in_progress"]
        by_type: Dict[str, int] = {}
        for w in in_progress:
            by_type[w.type] = by_type.get(w.type, 0) + 1
        return {"total": len(in_progress), "by_type": by_type}

    def throughput(self, period_days: int = 14, team: Optional[str] = None) -> Dict[str, Any]:
        cutoff = datetime.now() - timedelta(days=period_days)
        items = self.work_items if not team else [w for w in self.work_items if w.team == team]
        completed = [w for w in items if w.completed_at and w.completed_at >= cutoff]
        return {"per_week": round(len(completed) / (period_days / 7), 2), "count": len(completed)}

    def bottleneck_index(self, team: Optional[str] = None) -> Dict[str, Any]:
        items = self.work_items if not team else [w for w in self.work_items if w.team == team]
        wait_hours = [w.wait_time_hours for w in items if w.wait_time_hours > 0]
        if not wait_hours:
            return {"index_pct": 0.0, "avg_wait_hours": 0.0}
        avg_wait = sum(wait_hours) / len(wait_hours)
        cyc = self.cycle_time(team)
        avg_cycle_hours = cyc["avg_days"] * 24
        return {"index_pct": round((avg_wait / avg_cycle_hours * 100) if avg_cycle_hours > 0 else 0, 2), "avg_wait_hours": round(avg_wait, 2)}


class TeamHealthCalculator:
    """Team health indicators."""

    def __init__(self, surveys: List[Survey], hours_data: List[HoursData]):
        self.surveys = surveys
        self.hours_data = hours_data

    def enps(self, period: Optional[str] = None) -> Dict[str, Any]:
        surveys = self.surveys if not period else [s for s in self.surveys if s.period == period]
        if not surveys:
            return {"score": 0.0, "promoters": 0, "detractors": 0, "total": 0}
        promoters = sum(1 for s in surveys if s.score >= 9)
        detractors = sum(1 for s in surveys if s.score <= 6)
        total = len(surveys)
        score = ((promoters - detractors) / total * 100) if total > 0 else 0.0
        return {"score": round(score, 1), "promoters": promoters, "detractors": detractors, "total": total}

    def burnout_rate(self, threshold: float = 50.0, period: Optional[str] = None) -> Dict[str, Any]:
        data = self.hours_data if not period else [h for h in self.hours_data if h.week_start >= period]
        if not data:
            return {"rate_pct": 0.0, "over_threshold": 0, "total": 0}
        over = sum(1 for h in data if h.hours_per_week > threshold)
        return {"rate_pct": round((over / len(data)) * 100, 2), "over_threshold": over, "total": len(data)}

    def growth_metrics(self, period: Optional[str] = None) -> Dict[str, Any]:
        surveys = self.surveys if not period else [s for s in self.surveys if s.period == period]
        if not surveys:
            return {"avg_hours": 0.0, "total_hours": 0.0, "participants": 0}
        total = sum(s.training_hours for s in surveys)
        return {"avg_hours": round(total / len(surveys), 1), "total_hours": total, "participants": len(surveys)}

    def collaboration_index(self, cross_team_prs: List[Dict]) -> Dict[str, Any]:
        if not cross_team_prs:
            return {"index_pct": 0.0, "cross_team": 0, "total": 0}
        cross = sum(1 for pr in cross_team_prs if pr.get("cross_team"))
        return {"index_pct": round((cross / len(cross_team_prs)) * 100, 2), "cross_team": cross, "total": len(cross_team_prs)}


def main():
    """CLI entry point."""
    print("Engineering Metrics System v1.0")
    print("Usage: python metrics_calc.py [dora|flow|health|all]")


if __name__ == "__main__":
    main()