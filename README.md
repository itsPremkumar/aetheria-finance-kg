# Engineering Metrics System — README

## Overview

Production-grade engineering metrics system tracking DORA, Flow, and Team Health indicators.

## Quick Start

```bash
python scripts/metrics_calc.py
```

## Metrics Tracked

### DORA (4 Key Metrics)
- Deployment Frequency
- Lead Time for Changes
- Change Failure Rate
- Mean Time to Recovery (MTTR)

### Flow Efficiency
- Cycle Time
- Work in Progress (WIP)
- Throughput
- Bottleneck Index

### Team Health
- eNPS (Employee Net Promoter Score)
- Burnout Rate
- Training Hours
- Collaboration Index

## Data Sources

- Git commit history
- CI/CD pipeline logs
- Issue tracker data
- Incident reports
- Team surveys

## Output

- JSON for Grafana dashboard import
- CSV for spreadsheet analysis
- PDF weekly reports
- Threshold-based alerts

## Targets

| Metric | Elite | Medium | Low |
|--------|-------|--------|-----|
| Deploy Frequency | On-demand | Weekly | Monthly |
| Lead Time | < 1 day | < 1 week | > 1 month |
| Failure Rate | < 5% | 15% | > 45% |
| MTTR | < 1 hour | < 1 day | > 1 week |

## Architecture

- Python 3.11+
- No external dependencies (stdlib only)
- Pluggable data adapters
- Extensible metric definitions