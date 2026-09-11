#!/usr/bin/env python3
"""Engineering Metrics Calculation Scripts."""

import json
import csv
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict, Any


class DORAMetrics:
    """Calculate DORA metrics from deployment and incident data."""

    def __init__(self, deploys: List[Dict], incidents: List[Dict]):
        self.deploys = sorted(deploys, key=lambda d: d['timestamp'])
        self.incidents = sorted(incidents, key=lambda i: i['detected_at'])

    def deployment_frequency(self, period_weeks: int = 4) -> float:
        """Deployments per week."""
        if not self.deploys:
            return 0.0
        cutoff = datetime.now() - timedelta(weeks=period_weeks)
        recent = [d for d in self.deploys if d['timestamp'] >= cutoff]
        return len(recent) / period_weeks

    def lead_time_for_changes(self, commit_timestamp: datetime, deploy_timestamp: datetime) -> float:
        """Time from commit to production in days."""
        delta = deploy_timestamp - commit_timestamp
        return delta.total_seconds() / 86400

    def change_failure_rate(self, period_deploys: List[Dict] = None) -> float:
        """Percentage of deployments that failed."""
        deploys = period_deploys or self.deploys
        if not deploys:
            return 0.0
        failed = sum(1 for d in deploys if d.get('rollback') or d.get('incident'))
        return (failed / len(deploys)) * 100

    def mttr(self, period_incidents: List[Dict] = None) -> float:
        """Mean Time To Recovery in hours."""
        incidents = period_incidents or self.incidents
        if not incidents:
            return 0.0
        total_recovery = sum(
            (i['resolved_at'] - i['detected_at']).total_seconds() / 3600
            for i in incidents
            if i.get('resolved_at') and i.get('detected_at')
        )
        return total_recovery / len(incidents)

    def report(self) -> Dict[str, Any]:
        return {
            'deployment_frequency_per_week': round(self.deployment_frequency(), 2),
            'change_failure_rate_pct': round(self.change_failure_rate(), 2),
            'mttr_hours': round(self.mttr(), 2),
            'total_deploys': len(self.deploys),
            'total_incidents': len(self.incidents),
        }


class FlowMetrics:
    """Calculate flow efficiency metrics."""

    def __init__(self, work_items: List[Dict]):
        self.work_items = work_items

    def cycle_time(self) -> float:
        """Average cycle time in days."""
        if not self.work_items:
            return 0.0
        times = []
        for item in self.work_items:
            if item.get('completed_at') and item.get('started_at'):
                delta = item['completed_at'] - item['started_at']
                times.append(delta.total_seconds() / 86400)
        return sum(times) / len(times) if times else 0.0

    def work_in_progress(self) -> int:
        """Current WIP count."""
        return sum(1 for item in self.work_items if item.get('status') == 'in_progress')

    def throughput(self, period_days: int = 14) -> float:
        """Items completed per period."""
        cutoff = datetime.now() - timedelta(days=period_days)
        completed = [
            item for item in self.work_items
            if item.get('completed_at') and item['completed_at'] >= cutoff
        ]
        return len(completed) / (period_days / 7)  # per week

    def bottleneck_index(self) -> float:
        """Percentage of cycle time spent waiting."""
        if not self.work_items:
            return 0.0
        wait_times = []
        for item in self.work_items:
            if item.get('wait_time_hours'):
                wait_times.append(item['wait_time_hours'])
        if not wait_times:
            return 0.0
        avg_wait = sum(wait_times) / len(wait_times)
        avg_cycle = self.cycle_time() * 24  # convert to hours
        return (avg_wait / avg_cycle * 100) if avg_cycle > 0 else 0.0

    def report(self) -> Dict[str, Any]:
        return {
            'avg_cycle_time_days': round(self.cycle_time(), 2),
            'current_wip': self.work_in_progress(),
            'throughput_per_week': round(self.throughput(), 2),
            'bottleneck_index_pct': round(self.bottleneck_index(), 2),
        }


class TeamHealthMetrics:
    """Calculate team health indicators."""

    def __init__(self, surveys: List[Dict], hours_data: List[Dict]):
        self.surveys = surveys
        self.hours_data = hours_data

    def enps(self) -> float:
        """Employee Net Promoter Score."""
        if not self.surveys:
            return 0.0
        promoters = sum(1 for s in self.surveys if s['score'] >= 9)
        detractors = sum(1 for s in self.surveys if s['score'] <= 6)
        total = len(self.surveys)
        return ((promoters - detractors) / total * 100) if total > 0 else 0.0

    def burnout_rate(self, threshold_hours: float = 50.0) -> float:
        """Percentage of team exceeding threshold hours."""
        if not self.hours_data:
            return 0.0
        over = sum(1 for h in self.hours_data if h['hours_per_week'] > threshold_hours)
        return (over / len(self.hours_data)) * 100

    def growth_hours(self) -> float:
        """Average training hours per person per month."""
        if not self.surveys:
            return 0.0
        total = sum(s.get('training_hours', 0) for s in self.surveys)
        return total / len(self.surveys)

    def report(self) -> Dict[str, Any]:
        return {
            'enps': round(self.enps(), 1),
            'burnout_rate_pct': round(self.burnout_rate(), 2),
            'avg_training_hours_per_month': round(self.growth_hours(), 1),
        }


def load_json(path: str) -> List[Dict]:
    with open(path) as f:
        return json.load(f)


def main():
    # Example usage with simulated data
    deploys = [
        {'timestamp': datetime.now() - timedelta(days=i), 'rollback': i % 5 == 0}
        for i in range(0, 30)
    ]
    incidents = [
        {'detected_at': datetime.now() - timedelta(days=i), 'resolved_at': datetime.now() - timedelta(days=i, hours=2)}
        for i in range(0, 10)
    ]

    dora = DORAMetrics(deploys, incidents)
    print("DORA Report:", json.dumps(dora.report(), indent=2, default=str))


if __name__ == '__main__':
    main()