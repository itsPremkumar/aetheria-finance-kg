# Architecture Review Template

## Review Trigger

- New service design
- Major refactor (> 3 services affected)
- Security-sensitive change
- Cross-team dependency introduction

## Review Checklist

### System Overview
- [ ] System context diagram included
- [ ] Scope and boundaries clearly defined
- [ ] Non-functional requirements documented

### Data Architecture
- [ ] Data flow diagram provided
- [ ] Storage strategy justified
- [ ] Data retention and GDPR compliance addressed
- [ ] Backup and recovery plan in place

### API Design
- [ ] API contracts defined (OpenAPI/GraphQL schema)
- [ ] Versioning strategy documented
- [ ] Error handling and retry logic specified
- [ ] Rate limiting and auth model defined

### Security
- [ ] Threat model completed (STRIDE)
- [ ] Authentication/authorization design
- [ ] Data encryption at rest and in transit
- [ ] Secrets management approach

### Scalability & Performance
- [ ] Load estimates provided
- [ ] Horizontal scaling strategy
- [ ] Caching strategy documented
- [ ] Performance benchmarks/targets

### Observability
- [ ] Logging format and aggregation plan
- [ ] Metrics and alerting thresholds
- [ ] Distributed tracing strategy
- [ ] Runbook for on-call

### Operational Readiness
- [ ] Deployment strategy (blue/green, canary, etc.)
- [ ] Rollback plan documented
- [ ] Configuration management
- [ ] Disaster recovery test scheduled

### Cost
- [ ] Infrastructure cost estimate
- [ ] License cost analysis
- [ ] Expected ROI within 6 months

## Review Outcome

| Outcome | Action |
|---------|--------|
| Approved | Proceed to implementation |
| Conditional | Address feedback within 1 sprint |
| Rejected | Document rationale; reconsider in 3 months |
| Deferred | Schedule follow-up review with specific criteria |

## Sign-Off

| Role | Name | Date | Decision |
|------|------|------|----------|
| Architecture Lead | | | |
| Engineering Manager | | | |
| Security Reviewer | | | |
| Product Owner | | | |
