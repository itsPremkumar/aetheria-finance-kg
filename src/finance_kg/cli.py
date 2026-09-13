"""CLI for the Finance Knowledge Graph."""

from __future__ import annotations

import json
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from .knowledge_graph import KnowledgeGraph
from .models import Entity, EntityType, RelationType, Triple
from .sec_parser import SECFilingParser

console = Console()


@click.group()
@click.version_option()
def main() -> None:
    """Finance KG — Finance Reasoning Knowledge Graph."""


@main.command()
@click.argument("filing_path", type=click.Path(exists=True))
@click.option("--form-type", default="10-K", help="SEC form type")
@click.option("--output", type=click.Path(), help="Output JSON path")
def parse_filing(filing_path: str, form_type: str, output: Optional[str]) -> None:
    """Parse an SEC filing and extract entities/relations."""
    text = click.format_filename(filing_path)
    with open(text) as f:
        content = f.read()

    parser = SECFilingParser()
    parsed = parser.parse(content, form_type=form_type)
    triples = parser.extract_triples(parsed)

    console.print(f"[bold green]Parsed {parsed.form_type} filing[/bold green]")
    console.print(f"  Companies found: {len(parsed.company_names)}")
    console.print(f"  Tickers found: {len(parsed.tickers)}")
    console.print(f"  Amounts found: {len(parsed.amounts)}")
    console.print(f"  Dates found: {len(parsed.dates)}")
    console.print(f"  Triples extracted: {len(triples)}")

    if output:
        kg = KnowledgeGraph()
        kg.add_triples(triples)
        kg.export_json(output)
        console.print(f"  Exported to: {output}")


@main.command()
@click.option("--filing", type=click.Path(exists=True), help="SEC filing to ingest")
@click.option("--form-type", default="10-K", help="SEC form type")
@click.option("--output", type=click.Path(), help="Output graph JSON path")
def build(filing: Optional[str], form_type: str, output: Optional[str]) -> None:
    """Build the knowledge graph from data sources."""
    kg = KnowledgeGraph()

    if filing:
        with open(filing) as f:
            content = f.read()
        parser = SECFilingParser()
        parsed = parser.parse(content, form_type=form_type)
        triples = parser.extract_triples(parsed)
        kg.add_triples(triples)

    stats = kg.stats()
    console.print(f"[bold]Knowledge Graph Built[/bold]")
    console.print(f"  Entities: {stats['entities']}")
    console.print(f"  Relations: {stats['relations']}")

    if output:
        kg.export_json(output)
        console.print(f"  Exported to: {output}")


@main.command()
@click.argument("query_string")
@click.option("--entity-type", help="Filter by entity type")
@click.option("--relation-type", help="Filter by relation type")
@click.option("--graph", type=click.Path(exists=True), help="Graph JSON to query")
def query(
    query_string: str,
    entity_type: Optional[str],
    relation_type: Optional[str],
    graph: Optional[str],
) -> None:
    """Query the knowledge graph."""
    kg = KnowledgeGraph()

    if graph:
        kg.import_json(graph)

    results = kg.query(
        entity_type=entity_type,
        relation_type=relation_type,
        name_contains=query_string,
    )

    table = Table(title=f"Query Results: {query_string}")
    table.add_column("Subject", style="cyan")
    table.add_column("Relation", style="magenta")
    table.add_column("Object", style="green")
    table.add_column("Source", style="yellow")

    for triple in results:
        table.add_row(
            triple.subject.name,
            triple.predicate.value,
            triple.object.name,
            triple.source,
        )

    console.print(table)


@main.command()
def stats() -> None:
    """Show graph statistics."""
    console.print("[bold]Finance KG Statistics[/bold]")
    console.print("  Use 'build' to construct a graph first.")


if __name__ == "__main__":
    main()
