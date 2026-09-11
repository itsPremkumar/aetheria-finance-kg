# Finance KG — Open-Source Integration

Integration architecture for connecting **Apache Fineract** (core banking API) and **OpenBB** (financial data platform) into the Finance Reasoning Knowledge Graph.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Finance Reasoning KG                       │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  Entity      │  │  Relation    │  │  Reasoning        │  │
│  │  Extractor   │  │  Extractor   │  │  Engine           │  │
│  └──────┬──────┘  └──────┬───────┘  └────────┬──────────┘  │
│         │                │                    │              │
│  ┌──────┴────────────────┴────────────────────┴──────────┐  │
│  │              Knowledge Graph (NetworkX + SQLite)        │  │
│  └──────┬────────────────┬────────────────────┬──────────┘  │
│         │                │                    │              │
│  ┌──────┴──────┐  ┌──────┴───────┐  ┌────────┴──────────┐  │
│  │  Fineract   │  │  OpenBB      │  │  SEC Filing       │  │
│  │  Client     │  │  Client      │  │  Parser           │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Data Sources

### Apache Fineract
- **Role**: Core banking system — loans, clients, savings, accounting
- **API**: REST/JSON over HTTPS (OpenAPI 3.0)
- **Key endpoints**:
  - `/clients` — Client entities (individuals, groups, companies)
  - `/loans` — Loan accounts with balances, status, history
  - `/savingsaccounts` — Savings products and balances
  - `/glaccounts` — General ledger / chart of accounts
  - `/journalentries` — Accounting transactions
  - `/reports` — Financial reports (balance sheet, P&L)
- **Offline strategy**: Batch API → cache in SQLite → periodic sync

### OpenBB Platform
- **Role**: Market data — equities, ETFs, indices, fundamentals
- **API**: Python SDK (`obb` object) + REST API
- **Key capabilities**:
  - `obb.equity.price.historical()` — OHLCV price history
  - `obb.equity.fundamental()` — Financial statements, ratios
  - `obb.etf.holdings()` — ETF composition
  - `obb.index.constituents()` — Index membership
  - `obb.news.company()` — Company news sentiment
- **Offline strategy**: Fetch → serialize to Parquet → local query layer

### SEC Filing Parser
- **Role**: Extract entities and relations from 10-K, 10-Q, 8-K filings
- **Patterns**: Regex-based extraction for tickers, amounts, dates, parties
- **Output**: Structured triples (subject, predicate, object) for KG

## Entity Model

| Entity Type | Source | Properties |
|-------------|--------|------------|
| Company | Fineract, OpenBB, SEC | name, ticker, sector, country, founded_date |
| Person | Fineract, SEC | name, role, affiliation |
| Loan | Fineract | amount, currency, status, interest_rate, term |
| Account | Fineract | type, balance, currency, open_date |
| Security | OpenBB | ticker, exchange, asset_class, isin |
| Transaction | Fineract, SEC | amount, date, currency, type |
| Filing | SEC | form_type, filing_date, period, cik |

## Relation Model

| Relation | Source | Properties |
|----------|--------|------------|
| `HAS_LOAN` | Fineract | since, status |
| `HAS_ACCOUNT` | Fineract | since, type |
| `OWNS_SECURITY` | OpenBB | shares, value, date |
| `ACQUIRED` | SEC, News | date, amount, currency |
| `MERGED_WITH` | SEC | date, terms |
| `INVESTED_IN` | SEC, News | amount, round, date |
| `COMPETES_WITH` | OpenBB | sector, market |
| `SUPPLIES` | SEC | since, value |
| `HAS_SUBSIDIARY` | SEC | since, ownership_pct |
| `FILED` | SEC | date, form_type |

## Temporal Reasoning

- All entities carry `valid_from` / `valid_to` timestamps
- Financial metrics are period-aware (quarterly, yearly, trailing)
- KG supports time-slice queries: "Show all acquisitions in Q3 2024"
- Versioned facts: corrections create new versions, old versions retained

## Offline-First Strategy

1. **Fetch**: Pull from Fineract/OpenBB APIs on schedule
2. **Cache**: Store raw responses in SQLite with TTL
3. **Extract**: Run entity/relation extractors on cached data
4. **Build**: Populate NetworkX graph from extracted triples
5. **Query**: Serve reads from local graph; refresh on demand

## Integration Points

```
Fineract API ──► FineractClient ──► RawCache ──► KGBuilder ──► KnowledgeGraph
OpenBB SDK  ──► OpenBBClient  ──► RawCache ──► KGBuilder ──► KnowledgeGraph
SEC EDGAR   ──► SECParser     ──► RawCache ──► KGBuilder ──► KnowledgeGraph
```

## Tech Stack

- **Language**: Python 3.11+
- **Graph**: NetworkX (in-memory) + SQLite (persistent cache)
- **HTTP**: httpx (async, with retry)
- **Data**: pydantic (models), pandas (transforms)
- **Testing**: pytest, pytest-asyncio, respx (mock httpx)
- **Packaging**: pyproject.toml (PEP 621)
