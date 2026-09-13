# Finance KG

Finance Reasoning Knowledge Graph with Apache Fineract and OpenBB integration.

## Data Sources

### Apache Fineract
- Core banking system providing loans, clients, savings, accounting data
- REST API with batch operations
- https://fineract.apache.org/

### OpenBB Platform
- Open-source investment research platform
- Equities, ETFs, indices, fundamentals, news
- https://openbb.co/

### SEC EDGAR
- Public filings: 10-K, 10-Q, 8-K, DEF-14A
- Entity and relation extraction via regex patterns
- https://www.sec.gov/edgar

## Integration Architecture

See [architecture.md](architecture.md) for full design.

## API Reference

### FineractClient

```python
from finance_kg.fineract_client import FineractClient

client = FineractClient(
    base_url="https://demo.mifos.io",
    username="mifos",
    password="password",
)
await client.authenticate()
clients = await client.get_clients()
loans = await client.get_loans()
```

### OpenBBClient

```python
from finance_kg.openbb_client import OpenBBClient

client = OpenBBClient()
prices = client.get_historical_prices("AAPL")
fundamentals = client.get_fundamentals("AAPL")
```

### SECFilingParser

```python
from finance_kg.sec_parser import SECFilingParser

parser = SECFilingParser()
parsed = parser.parse(filing_text, form_type="10-K")
triples = parser.extract_triples(parsed)
```

### KnowledgeGraph

```python
from finance_kg.knowledge_graph import KnowledgeGraph

kg = KnowledgeGraph()
kg.add_triples(triples)
results = kg.query(name_contains="Acme", relation_type="ACQUIRED")
kg.export_json("graph.json")
```

## Testing

```bash
pytest tests/ -v --cov=finance_kg
```

## Output Format

The knowledge graph exports to JSON:

```json
{
  "entities": [
    {
      "id": "ent_000001",
      "type": "Company",
      "name": "Acme Corp",
      "properties": {"cik": "0000123456"},
      "source": "SEC",
      "confidence": 1.0
    }
  ],
  "relations": [
    {
      "source_id": "ent_000001",
      "target_id": "ent_000002",
      "type": "ACQUIRED",
      "properties": {},
      "source": "SEC",
      "confidence": 1.0
    }
  ]
}
```
