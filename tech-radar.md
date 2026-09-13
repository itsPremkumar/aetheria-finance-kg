# Technology Radar

## Quadrant Legend

| Quadrant | Description |
|----------|-------------|
| **Adopt** | Proven, widely adopted, low risk |
| **Trial** | Promising but needs validation |
| **Assess** | Emerging, potential but unproven at scale |
| **Hold** | Legacy or problematic; avoid for new work |

## Current Radar

### Adopt
- PostgreSQL — primary OLTP database
- Redis — caching and session store
- Kubernetes — container orchestration
- Terraform — infrastructure as code
- React — frontend framework
- Node.js/TypeScript — backend runtime
- GitHub Actions — CI/CD
- GraphQL — API layer for complex queries
- OpenTelemetry — observability instrumentation
- Grafana — metrics dashboards

### Trial
- Turso — edge SQLite for read-heavy workloads
- Bun — fast JavaScript runtime for tooling
- Tailwind CSS — utility-first styling
- WebAssembly — performance-critical computations
- Dagger — CI pipeline as code
- pglite — PostgreSQL in the browser for demos

### Assess
- Dapr — portable application runtime
- eBPF — kernel-level observability and networking
- Tetragon — eBPF-based security observability
- Cloudflare Workers — edge compute
- LiteFS — distributed SQLite replication
- Polar — open-source payment infrastructure

### Hold
- AngularJS — legacy frontend framework
- SOAP-based services — replace with REST/gRPC
- Oracle DB — migrate to PostgreSQL where feasible
- Custom build system — switch to Nix or Bazel

## Ring Movement History

| Technology | Previous | Current | Movement | Reason |
|------------|----------|---------|----------|--------|
| WebAssembly | Assess | Trial | ↑ | Performance gains validated in 2 pilot services |
| Tailwind CSS | Assess | Trial | ↑ | Consistent adoption across 3 teams |
| Dapr | Assess | Assess | → | Needs more production evidence |
| eBPF | Assess | Assess | → | Evaluating security use cases |
| Turso | Trial | Trial | → | Scaling tests pending |

## Review Cadence

- **Monthly**: Review trial/assess items
- **Quarterly**: Full radar refresh with Architecture Review Board
- **Ad-hoc**: Emergency review for critical new technology

## Entry Template

```
## Technology: <Name>
- **Quadrant**: Adopt / Trial / Assess / Hold
- **Ring Movement**: → (stable) / ↑ (adopt) / ↓ (hold) / ⚠️ (new)
- **Use Cases**: Where it fits in our stack
- **Risks**: Known limitations, vendor lock-in, maturity
- **Try This**: First step for evaluation
- **Last Reviewed**: <date>
```
