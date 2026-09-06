"""SEC filing parser for entity and relation extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .models import Entity, EntityType, Relation, RelationType, Triple


# Common patterns for SEC filing extraction
TICKER_PATTERN = re.compile(
    r"\b([A-Z]{1,5})\s*\(\s*(?:NASDAQ|NYSE|AMEX|OTC)\s*\)"
    r"|\b(?:ticker|symbol)\s*[:=]\s*([A-Z]{1,5})\b",
    re.IGNORECASE,
)

AMOUNT_PATTERN = re.compile(
    r"\$\s*[\d,]+(?:\.\d{2})?"
    r"|[\d,]+(?:\.\d{2})?\s*(?:million|billion|thousand)",
    re.IGNORECASE,
)

DATE_PATTERN = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b"
    r"|\b\d{4}-\d{2}-\d{2}\b"
    r"|\b\d{1,2}/\d{1,2}/\d{4}\b"
)

CIK_PATTERN = re.compile(r"\bCIK\s*[:#]?\s*(\d{10})\b", re.IGNORECASE)

COMPANY_NAME_PATTERN = re.compile(
    r"\b([A-Z][A-Za-z\s&.,]+(?:Inc\.|Corp\.|Corporation|Ltd\.|LLC|Company|Co\.|Group|Holdings|International|Technologies|Enterprises))\b"
)

ACQUISITION_PATTERN = re.compile(
    r"([A-Z][A-Za-z\s&.]+)\s+(?:acquired|purchased|bought)\s+([A-Z][A-Za-z\s&.]+)",
    re.IGNORECASE,
)

INVESTMENT_PATTERN = re.compile(
    r"([A-Z][A-Za-z\s&.]+)\s+(?:invested|funded|financed)\s+(?:in\s+)?([A-Z][A-Za-z\s&.]+)",
    re.IGNORECASE,
)

MERGER_PATTERN = re.compile(
    r"([A-Z][A-Za-z\s&.]+)\s+(?:merged with|combination with)\s+([A-Z][A-Za-z\s&.]+)",
    re.IGNORECASE,
)


@dataclass
class ParsedFiling:
    """Result of parsing an SEC filing."""

    cik: Optional[str] = None
    company_names: list[str] = field(default_factory=list)
    tickers: list[str] = field(default_factory=list)
    amounts: list[str] = field(default_factory=list)
    dates: list[str] = field(default_factory=list)
    acquisitions: list[tuple[str, str]] = field(default_factory=list)
    investments: list[tuple[str, str]] = field(default_factory=list)
    mergers: list[tuple[str, str]] = field(default_factory=list)
    form_type: str = ""
    filing_date: Optional[datetime] = None
    raw_text: str = ""


class SECFilingParser:
    """Parse SEC filings and extract structured entities and relations."""

    def __init__(self):
        self._entity_counter = 0
        self._relation_counter = 0

    def _next_entity_id(self) -> str:
        self._entity_counter += 1
        return f"ent_{self._entity_counter:06d}"

    def _next_relation_id(self) -> str:
        self._relation_counter += 1
        return f"rel_{self._relation_counter:06d}"

    def parse(self, text: str, form_type: str = "10-K") -> ParsedFiling:
        """Parse raw filing text and extract entities."""
        result = ParsedFiling(raw_text=text, form_type=form_type)

        # Extract CIK
        cik_match = CIK_PATTERN.search(text)
        if cik_match:
            result.cik = cik_match.group(1)

        # Extract company names
        result.company_names = list(set(COMPANY_NAME_PATTERN.findall(text)))

        # Extract tickers
        ticker_matches = TICKER_PATTERN.findall(text)
        for match in ticker_matches:
            ticker = match[0] or match[1] if isinstance(match, tuple) else match
            if ticker:
                result.tickers.append(ticker.upper())

        # Extract amounts
        result.amounts = AMOUNT_PATTERN.findall(text)

        # Extract dates
        result.dates = DATE_PATTERN.findall(text)

        # Extract acquisitions
        result.acquisitions = ACQUISITION_PATTERN.findall(text)

        # Extract investments
        result.investments = INVESTMENT_PATTERN.findall(text)

        # Extract mergers
        result.mergers = MERGER_PATTERN.findall(text)

        return result

    def extract_triples(self, parsed: ParsedFiling) -> list[Triple]:
        """Convert parsed filing into knowledge graph triples."""
        triples: list[Triple] = []

        # Create company entities
        company_entities: dict[str, Entity] = {}
        for name in parsed.company_names:
            entity = Entity(
                id=self._next_entity_id(),
                type=EntityType.COMPANY,
                name=name.strip(),
                source="SEC",
                properties={"cik": parsed.cik} if parsed.cik else {},
            )
            company_entities[name.strip()] = entity

        # Create filing entity
        filing_entity = Entity(
            id=self._next_entity_id(),
            type=EntityType.FILING,
            name=f"{parsed.form_type} Filing",
            source="SEC",
            properties={
                "form_type": parsed.form_type,
                "cik": parsed.cik,
            },
        )

        # Link companies to filing
        for company in company_entities.values():
            relation = Relation(
                id=self._next_relation_id(),
                type=RelationType.FILED,
                source_id=company.id,
                target_id=filing_entity.id,
                source="SEC",
            )
            triples.append(
                Triple(
                    subject=company,
                    predicate=RelationType.FILED,
                    object=filing_entity,
                    source="SEC",
                )
            )

        # Extract acquisition relations
        for acquirer, target in parsed.acquisitions:
            acquirer = acquirer.strip()
            target = target.strip()
            if acquirer not in company_entities:
                company_entities[acquirer] = Entity(
                    id=self._next_entity_id(),
                    type=EntityType.COMPANY,
                    name=acquirer,
                    source="SEC",
                )
            if target not in company_entities:
                company_entities[target] = Entity(
                    id=self._next_entity_id(),
                    type=EntityType.COMPANY,
                    name=target,
                    source="SEC",
                )
            triples.append(
                Triple(
                    subject=company_entities[acquirer],
                    predicate=RelationType.ACQUIRED,
                    object=company_entities[target],
                    source="SEC",
                )
            )

        # Extract investment relations
        for investor, target in parsed.investments:
            investor = investor.strip()
            target = target.strip()
            if investor not in company_entities:
                company_entities[investor] = Entity(
                    id=self._next_entity_id(),
                    type=EntityType.COMPANY,
                    name=investor,
                    source="SEC",
                )
            if target not in company_entities:
                company_entities[target] = Entity(
                    id=self._next_entity_id(),
                    type=EntityType.COMPANY,
                    name=target,
                    source="SEC",
                )
            triples.append(
                Triple(
                    subject=company_entities[investor],
                    predicate=RelationType.INVESTED_IN,
                    object=company_entities[target],
                    source="SEC",
                )
            )

        # Extract merger relations
        for company_a, company_b in parsed.mergers:
            company_a = company_a.strip()
            company_b = company_b.strip()
            if company_a not in company_entities:
                company_entities[company_a] = Entity(
                    id=self._next_entity_id(),
                    type=EntityType.COMPANY,
                    name=company_a,
                    source="SEC",
                )
            if company_b not in company_entities:
                company_entities[company_b] = Entity(
                    id=self._next_entity_id(),
                    type=EntityType.COMPANY,
                    name=company_b,
                    source="SEC",
                )
            triples.append(
                Triple(
                    subject=company_entities[company_a],
                    predicate=RelationType.MERGED_WITH,
                    object=company_entities[company_b],
                    source="SEC",
                )
            )

        return triples
