# AI/ML Risk Assessment Matrix

## Methodology

Risk = Likelihood × Impact (scale 1-5 each)

| Score | Likelihood | Impact |
|-------|-----------|--------|
| 1 | Rare (<5% probability) | Negligible — minor inconvenience |
| 2 | Unlikely (5-20%) | Minor — temporary operational impact |
| 3 | Possible (20-50%) | Moderate — significant but recoverable |
| 4 | Likely (50-80%) | Major — regulatory/financial exposure |
| 5 | Almost Certain (>80%) | Severe — safety, legal, existential risk |

## Risk Matrix by AI System Category

### 1. High-Risk Systems (EU AI Act)

| Category | Likelihood | Impact | Risk Score | Mitigation |
|----------|-----------|--------|------------|------------|
| Facial recognition | 4 | 5 | 20 | Consent, accuracy audit, human override |
| Credit scoring | 3 | 5 | 15 | Fairness testing, explainability, appeal process |
| Hiring/recruitment | 3 | 5 | 15 | Bias audit, human review, transparency |
| Healthcare diagnosis | 4 | 5 | 20 | Clinical validation, regulatory approval |
| Autonomous vehicles | 4 | 5 | 20 | Redundant safety, rigorous testing, OTA updates |
| Legal document analysis | 3 | 4 | 12 | Accuracy thresholds, lawyer review, version control |

### 2. Medium-Risk Systems

| Category | Likelihood | Impact | Risk Score | Mitigation |
|----------|-----------|--------|------------|------------|
| Customer service chatbot | 3 | 3 | 9 | Guardrails, escalation to human, satisfaction monitoring |
| Recommendation engine | 3 | 3 | 9 | Diversity controls, feedback loop, A/B testing |
| Fraud detection | 3 | 4 | 12 | Precision/recall monitoring, false positive review |
| Sentiment analysis | 2 | 3 | 6 | Context validation, bias monitoring |
| Demand forecasting | 2 | 3 | 6 | Model drift detection, fallback to heuristic |

### 3. Low-Risk Systems

| Category | Likelihood | Impact | Risk Score | Mitigation |
|----------|-----------|--------|------------|------------|
| Email classification | 2 | 2 | 4 | Accuracy monitoring |
| Document summarization | 2 | 2 | 4 | Human review for critical docs |
| Internal knowledge search | 2 | 2 | 4 | Result quality checks |
| Meeting transcription | 1 | 2 | 2 | Privacy controls, accuracy validation |

## Risk Heat Map

```
Impact →    1       2       3       4       5
           ┌───────┬───────┬───────┬───────┬───────┐
Likelihood │       │       │       │       │       │
  5        │   5   │  10   │  15   │  20   │  25   │ HIGH
           ├───────┼───────┼───────┼───────┼───────┤
  4        │   4   │   8   │  12   │  16   │  20   │ HIGH
           ├───────┼───────┼───────┼───────┼───────┤
  3        │   3   │   6   │   9   │  12   │  15   │ MED
           ├───────┼───────┼───────┼───────┼───────┤
  2        │   2   │   4   │   6   │   8   │  10   │ LOW
           ├───────┼───────┼───────┼───────┼───────┤
  1        │   1   │   2   │   3   │   4   │   5   │ LOW
           └───────┴───────┴───────┴───────┴───────┘
```

## Review Cadence

- **Weekly**: High-risk systems (>15 score)
- **Monthly**: Medium-risk systems (9-15 score)
- **Quarterly**: Low-risk systems (<9 score)
- **Per release**: All systems with model updates

## Escalation Triggers

- Risk score increase ≥ 3 points → immediate review
- New regulatory requirement → reassess within 2 weeks
- Incident involving AI decision → full risk review within 48 hours