# Engineering Metrics System — DORA, Flow & Team Health Dashboard

## 1. DORA Metrics Implementation

### 1.1 Deployment Frequency
Tracks how often code is deployed to production.

```python
from datetime import datetime, timedelta
from typing import List, Dict

def deployment_frequency(deploys: List[Dict], period_weeks: int = 4) -> float:
    cutoff = datetime.now() - timedelta(weeks=period_weeks)
    recent = [d for d in deploys if d['timestamp'] >= cutoff]
    return len(recent) / period_weeks
```

### 1.2 Lead Time for Changes
Time from commit to production deployment.

```python
def lead_time_for_changes(commit_ts: datetime, deploy_ts: datetime) -> float:
    delta = deploy_ts - commit_ts
    return delta.total_seconds() / 86400  # days
```

### 1.3 Change Failure Rate
Percentage of deployments causing failures or rollbacks.

```python
def change_failure_rate(deploys: List[Dict]) -> float:
    if not deploys:
        return 0.0
    failed = sum(1 for d in deploys if d.get('rollback') or d.get('incident'))
    return (failed / len(deploys)) * 100
```

### 1.4 Mean Time to Recovery (MTTR)
Average time to restore service after an incident.

```python
def mttr(incidents: List[Dict]) -> float:
    if not incidents:
        return 0.0
    total = sum(
        (i['resolved_at'] - i['detected_at']).total_seconds() / 3600
        for i in incidents
        if i.get('resolved_at') and i.get('detected_at')
    )
    return total / len(incidents)
```

## 2. Flow Metrics

### 2.1 Cycle Time
Average time from work start to delivery.

```python
def cycle_time(work_items: List[Dict]) -> float:
    times = []
    for item in work_items:
        if item.get('completed_at') and item.get('started_at'):
            delta = item['completed_at'] - item['started_at']
            times.append(delta.total_seconds() / 86400)
    return sum(times) / len(times) if times else 0.0
```

### 2.2 Work in Progress (WIP)
Current active items per team.

```python
def work_in_progress(work_items: List[Dict]) -> int:
    return sum(1 for item in work_items if item.get('status') == 'in_progress')
```

### 2.3 Throughput
Items completed per sprint/period.

```python
def throughput(work_items: List[Dict], period_days: int = 14) -> float:
    cutoff = datetime.now() - timedelta(days=period_days)
    completed = [item for item in work_items
                 if item.get('completed_at') and item['completed_at'] >= cutoff]
    return len(completed) / (period_days / 7)  # per week
```

### 2.4 Bottleneck Index
Percentage of cycle time spent waiting/blocked.

```python
def bottleneck_index(work_items: List[Dict]) -> float:
    wait_times = [item['wait_time_hours'] for item in work_items
                  if item.get('wait_time_hours')]
    if not wait_times:
        return 0.0
    avg_wait = sum(wait_times) / len(wait_times)
    avg_cycle = cycle_time(work_items) * 24  # hours
    return (avg_wait / avg_cycle * 100) if avg_cycle > 0 else 0.0
```

## 3. Team Health Dashboard

### 3.1 Employee Net Promoter Score (eNPS)

```python
def enps(surveys: List[Dict]) -> float:
    if not surveys:
        return 0.0
    promoters = sum(1 for s in surveys if s['score'] >= 9)
    detractors = sum(1 for s in surveys if s['score'] <= 6)
    return ((promoters - detractors) / len(surveys)) * 100
```

### 3.2 Burnout Rate

```python
def burnout_rate(hours_data: List[Dict], threshold: float = 50.0) -> float:
    if not hours_data:
        return 0.0
    over = sum(1 for h in hours_data if h['hours_per_week'] > threshold)
    return (over / len(hours_data)) * 100
```

### 3.3 Growth & Collaboration

```python
def training_hours(surveys: List[Dict]) -> float:
    if not surveys:
        return 0.0
    return sum(s.get('training_hours', 0) for s in surveys) / len(surveys)

def collaboration_index(prs: List[Dict]) -> float:
    cross_team = sum(1 for pr in prs if pr.get('cross_team'))
    return (cross_team / len(prs) * 100) if prs else 0.0
```

## 4. Dashboard Design

### 4.1 Layout

```
┌─────────────────────────────────────────────────────┐
│  Engineering Metrics Dashboard                      │
├──────────────┬──────────────┬───────────────────────┤
│  DORA        │  Flow        │  Team Health          │
│  ┌──────────┐│  ┌──────────┐│  ┌─────────────────┐  │
│  │ Deploy F ││  │ Cycle    ││  │  eNPS:   42     │  │
│  │ 8.2/wk   ││  │ Time 1.2d││  │  Burnout: 8%   │  │
│  │ Lead 0.5d││  │ WIP:  12 ││  │  Growth: 6hrs  │  │
│  │ FR 12%   ││  │ Through  ││  │  Collab: 65%   │  │
│  │ MTTR 2h  ││  │  8.5/wk  ││  └─────────────────┘  │
│  └──────────┘│  │ Bottleneck││                       │
│              │  │  15%     ││                       │
│              │  └──────────┘│                       │
└──────────────┴──────────────┴───────────────────────┘
```

### 4.2 Data Sources

- Git commits (author, timestamp, branch, files changed)
- CI/CD pipeline logs (build time, test results, deployment status)
- Issue tracker (created, assigned, resolved, closed)
- Incident reports (detected, acknowledged, resolved)
- Team surveys (eNPS quarterly, training hours monthly)

### 4.3 Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Deployment Frequency | < 1/week | < 1/month |
| Lead Time | > 3 days | > 1 week |
| Change Failure Rate | > 15% | > 30% |
| MTTR | > 4 hours | > 24 hours |
| Burnout Rate | > 15% | > 25% |
| eNPS | < 20 | < 0 |

## 5. Implementation

### 5.1 Project Structure

```
engineering-metrics/
├── scripts/
│   ├── metrics_calc.py       # Core metric calculations
│   ├── dora_report.py        # DORA aggregation
│   ├── flow_analysis.py      # Flow efficiency
│   └── team_health.py        # Team health scoring
├── data/
│   ├── deploys.json          # Deployment history
│   ├── incidents.json        # Incident records
│   ├── work_items.json       # Task tracking data
│   └── surveys.json          # Team survey results
├── output/
│   ├── dashboard.json        # JSON for Grafana
│   ├── weekly_report.csv     # CSV export
│   └── weekly_report.pdf     # PDF report
├── config.yaml               # Metric thresholds & targets
└── README.md                 # This file
```

### 5.2 Usage

```bash
# Calculate all metrics
python scripts/metrics_calc.py

# Generate DORA report
python scripts/dora_report.py --period 4w

# Flow analysis
python scripts/flow_analysis.py --team platform

# Team health check
python scripts/team_health.py --quarter Q3
```

## 6. Targets (Elite vs Medium vs Low)

| Metric | Elite | Medium | Low |
|--------|-------|--------|-----|
| Deployment Frequency | On-demand (multiple/day) | Weekly | Monthly |
| Lead Time for Changes | < 1 day | < 1 week | > 1 month |
| Change Failure Rate | < 5% | 15% | > 45% |
| MTTR | < 1 hour | < 1 day | > 1 week |
| Cycle Time | < 1 day | < 3 days | > 2 weeks |
| WIP | < 2/person | < 4/person | > 6/person |
| eNPS | > 70 | > 30 | < 0 |
| Burnout | < 5% | < 15% | > 25% |
