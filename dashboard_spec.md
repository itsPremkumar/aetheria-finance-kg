# Engineering Metrics System — DORA, Flow & Team Health Dashboard

## 1. Dashboard Design Specification

### 1.1 DORA Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| Deployment Frequency | How often code is deployed to production | Multiple deployments per day |
| Lead Time for Changes | Time from commit to production | < 1 day |
| Change Failure Rate | % of deployments causing failure | < 15% |
| Mean Time to Recovery (MTTR) | Time to restore service after failure | < 1 hour |

### 1.2 Flow Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| Cycle Time | Time from work start to delivery | < 3 days |
| Work in Progress | Active items per team | < 3 per person |
| Throughput | Items completed per sprint | Trend upward |
| Bottleneck Index | Where work stalls longest | < 20% of cycle time |

### 1.3 Team Health Indicators

| Indicator | Measurement | Target |
|-----------|-------------|--------|
| Satisfaction | eNPS survey quarterly | > 50 |
| Burnout | Hours/week > 50 | < 10% of team |
| Growth | Training hours/month | > 4 hrs/person |
| Collaboration | Cross-team PRs/week | > 5 per team |

## 2. Metrics Calculation Scripts

See `scripts/metrics_calc.py` for implementation.

### 2.1 Data Sources

- Git commits (author, timestamp, branch, files changed)
- CI/CD pipeline logs (build time, test results, deployment status)
- Issue tracker (created, assigned, resolved, closed)
- Incident reports (detected, acknowledged, resolved)

### 2.2 Calculations

```python
# DORA: Deployment Frequency
def deployment_frequency(deploys):
    return len(deploys) / weeks_in_period

# DORA: Lead Time for Changes
def lead_time(commits, deploys):
    commit_time = commits[0].timestamp
    deploy_time = deploys[-1].timestamp
    return (deploy_time - commit_time).total_seconds() / 86400  # days

# DORA: Change Failure Rate
def change_failure_rate(deploys, incidents):
    failed = sum(1 for d in deploys if d.rollback or d.incident)
    return failed / len(deploys) * 100

# DORA: MTTR
def mttr(incidents):
    total_recovery = sum(i.resolved_at - i.detected_at for i in incidents)
    return total_recovery / len(incidents)
```

## 3. Scorecard Template

```yaml
team: <team-name>
period: <sprint/quarter>
dora:
  deployment_frequency: <value>
  lead_time_for_changes: <value> days
  change_failure_rate: <value>%
  mttr: <value> hours
flow:
  cycle_time: <value> days
  work_in_progress: <value>
  throughput: <value>
  bottleneck_index: <value>%
team_health:
  satisfaction_enps: <value>
  burnout_rate: <value>%
  growth_hours: <value> hrs/person
  collaboration_prs: <value> /week
actions:
  - <improvement action 1>
  - <improvement action 2>
```

## 4. Implementation

Scripts located in `scripts/` directory:
- `metrics_calc.py` — Core metric calculations
- `dora_report.py` — DORA metrics aggregation
- `flow_analysis.py` — Flow efficiency analysis
- `team_health.py` — Team health scoring

## 5. Dashboard Integration

- Export: JSON/CSV for Grafana import
- Alerts: Threshold-based notifications
- Historical: 90-day rolling window
- Export: Weekly PDF report generation
