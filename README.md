# Finance KG — Open-Source Integration (Apache Fineract / OpenBB)

A vertical AI project for finance: extract structured knowledge from SEC filings,
core banking systems (Apache Fineract), and market data (OpenBB) into a
reasoning knowledge graph.

## Features

- **Entity Extraction**: Companies, persons, loans, accounts, securities, transactions
- **Relation Extraction**: Acquisitions, investments, mergers, ownership, filings
- **Knowledge Graph**: NetworkX-backed with temporal reasoning
- **SEC Filing Parser**: Regex-based extraction from 10-K, 10-Q, 8-K filings
- **Apache Fineract Client**: REST API client with offline caching
- **OpenBB Client**: Market data client with offline caching
- **CLI**: Build, parse, and query from the command line
- **100% Offline-First**: All data cached locally in SQLite

## Quick Start

```bash
# Install
pip install -e .

# Install with OpenBB support
pip install -e ".[openbb]"

# Parse an SEC filing
finance-kg parse-filing filing.txt --form-type 10-K --output graph.json

# Build knowledge graph
finance-kg build --filing filing.txt --output graph.json

# Query the graph
finance-kg query "Acme" --graph graph.json

# Show statistics
finance-kg stats
```

## Architecture

```
Fineract API ──► FineractClient ──► RawCache ──► KGBuilder ──► KnowledgeGraph
OpenBB SDK  ──► OpenBBClient  ──► RawCache ──► KGBuilder ──► KnowledgeGraph
SEC EDGAR   ──► SECParser     ──► RawCache ──► KGBuilder ──► KnowledgeGraph
```

## Entity Types

| Type | Description | Source |
|------|-------------|--------|
| Company | Business entity | Fineract, OpenBB, SEC |
| Person | Individual | Fineract, SEC |
| Loan | Loan account | Fineract |
| Account | Savings/checking | Fineract |
| Security | Stock/ETF/bond | OpenBB |
| Transaction | Financial tx | Fineract, SEC |
| Filing | SEC filing | SEC |

## Relation Types

| Relation | Meaning |
|----------|---------|
| `ACQUIRED` | Company bought another |
| `INVESTED_IN` | Company invested in another |
| `MERGED_WITH` | Companies merged |
| `OWNS_SECURITY` | Entity owns a security |
| `HAS_LOAN` | Entity has a loan |
| `HAS_ACCOUNT` | Entity has an account |
| `FILED` | Company filed a document |
| `COMPETES_WITH` | Companies compete |
| `SUPPLIES` | Supplier relationship |
| `HAS_SUBSIDIARY` | Parent-subsidiary |

## Development

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=finance_kg

# Lint
ruff check src/
```

## License

MIT
