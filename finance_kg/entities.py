"""
Finance KG - Entity models and extractor.

Defines entity types (Company, Person, Loan, Account, Security, Transaction, Filing)
and a rule-based extractor using regex patterns.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import re


class EntityType(Enum):
    COMPANY = "Company"
    PERSON = "Person"
    LOAN = "Loan"
    ACCOUNT = "Account"
    SECURITY = "Security"
    TRANSACTION = "Transaction"
    FILING = "Filing"
    TICKER = "Ticker"
    AMOUNT = "Amount"
    DATE = "Date"
    SECTOR = "Sector"


@dataclass
class Entity:
    """A financial entity extracted from text."""
    id: str
    entity_type: EntityType
    label: str
    properties: dict = field(default_factory=dict)
    source: str = "text"
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.entity_type.value,
            "label": self.label,
            "properties": self.properties,
            "source": self.source,
            "confidence": self.confidence,
        }


class EntityExtractor:
    """Rule-based entity extraction using regex patterns."""

    # Company patterns
    COMPANY_PATTERNS = [
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Inc\.|Corp\.|LLC|Ltd\.|Group|Company|Co\.|Holdings|International|Technologies|Enterprises))',
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Bank|Financial|Capital|Securities|Insurance|Trust|Investments))',
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b',
    ]

    # Ticker pattern (2-5 uppercase letters in parentheses or standalone)
    TICKER_PATTERNS = [
        r'\(([A-Z]{2,5})\)',
        r'\b([A-Z]{2,5})\b',
    ]

    # Amount patterns
    AMOUNT_PATTERNS = [
        r'\$[\d,]+(?:\.\d+)?(?:\s*(?:billion|million|trillion|B|M|T))?\b',
        r'\b\d+(?:\.\d+)?\s*(?:billion|million|trillion)\b',
        r'\b\d+(?:\.\d+)?\s*(?:USD|EUR|GBP)\b',
    ]

    # Date patterns
    DATE_PATTERNS = [
        r'\bQ[1-4]\s*\d{4}\b',
        r'\bFY\d{2,4}\b',
        r'\b\d{4}-\d{2}-\d{2}\b',
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
    ]

    # Person patterns (Name Name)
    PERSON_PATTERNS = [
        r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b',
    ]

    # Sector patterns
    SECTOR_PATTERNS = [
        r'\b(?:technology|healthcare|financial|energy|industrial|consumer|real\s+estate|materials|utilities|telecommunications)\b',
    ]

    # Loan patterns
    LOAN_PATTERNS = [
        r'\b[Ll]oan\s*#?\s*(\d+)\b',
        r'\b[Ll]oan\s+[Aa]ccount\s*#?\s*(\d+)\b',
    ]

    # Account patterns
    ACCOUNT_PATTERNS = [
        r'\b[Aa]ccount\s*#?\s*(\d+)\b',
        r'\b[Ss]avings\s+[Aa]ccount\s*#?\s*(\d+)\b',
        r'\b[Cc]hecking\s+[Aa]ccount\s*#?\s*(\d+)\b',
    ]

    # Security patterns
    SECURITY_PATTERNS = [
        r'\b([A-Z]{1,5})\s+(?:stock|shares|bond|ETF|fund)\b',
        r'\b(?:stock|shares|bond|ETF|fund)\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
    ]

    # Transaction patterns
    TRANSACTION_PATTERNS = [
        r'\b[Tt]ransaction\s*#?\s*(\d+)\b',
        r'\b[Pp]ayment\s+#?\s*(\d+)\b',
        r'\b[Tt]ransfer\s+#?\s*(\d+)\b',
    ]

    # Filing patterns
    FILING_PATTERNS = [
        r'\b(10-K|10-Q|8-K|S-1|13F|DEF\s*14A)\b',
    ]

    def extract(self, text: str) -> list[Entity]:
        """Extract all entities from text."""
        entities = []
        seen = set()

        for pattern in self.COMPANY_PATTERNS:
            for match in re.finditer(pattern, text):
                label = match.group(1)
                if label not in seen:
                    seen.add(label)
                    entities.append(Entity(
                        id=f"company_{len(entities)}",
                        entity_type=EntityType.COMPANY,
                        label=label,
                    ))

        for pattern in self.TICKER_PATTERNS:
            for match in re.finditer(pattern, text):
                label = match.group(1)
                if label not in seen and len(label) >= 2:
                    seen.add(label)
                    entities.append(Entity(
                        id=f"ticker_{len(entities)}",
                        entity_type=EntityType.TICKER,
                        label=label,
                    ))

        for pattern in self.AMOUNT_PATTERNS:
            for match in re.finditer(pattern, text):
                label = match.group(0)
                if label not in seen:
                    seen.add(label)
                    entities.append(Entity(
                        id=f"amount_{len(entities)}",
                        entity_type=EntityType.AMOUNT,
                        label=label,
                    ))

        for pattern in self.DATE_PATTERNS:
            for match in re.finditer(pattern, text):
                label = match.group(0)
                if label not in seen:
                    seen.add(label)
                    entities.append(Entity(
                        id=f"date_{len(entities)}",
                        entity_type=EntityType.DATE,
                        label=label,
                    ))

        for pattern in self.LOAN_PATTERNS:
            for match in re.finditer(pattern, text):
                label = match.group(0)
                if label not in seen:
                    seen.add(label)
                    entities.append(Entity(
                        id=f"loan_{len(entities)}",
                        entity_type=EntityType.LOAN,
                        label=label,
                        properties={"loan_id": match.group(1)},
                    ))

        for pattern in self.ACCOUNT_PATTERNS:
            for match in re.finditer(pattern, text):
                label = match.group(0)
                if label not in seen:
                    seen.add(label)
                    entities.append(Entity(
                        id=f"account_{len(entities)}",
                        entity_type=EntityType.ACCOUNT,
                        label=label,
                        properties={"account_id": match.group(1)},
                    ))

        for pattern in self.SECURITY_PATTERNS:
            for match in re.finditer(pattern, text):
                label = match.group(0)
                if label not in seen:
                    seen.add(label)
                    entities.append(Entity(
                        id=f"security_{len(entities)}",
                        entity_type=EntityType.SECURITY,
                        label=label,
                    ))

        for pattern in self.TRANSACTION_PATTERNS:
            for match in re.finditer(pattern, text):
                label = match.group(0)
                if label not in seen:
                    seen.add(label)
                    entities.append(Entity(
                        id=f"transaction_{len(entities)}",
                        entity_type=EntityType.TRANSACTION,
                        label=label,
                        properties={"transaction_id": match.group(1)},
                    ))

        for pattern in self.FILING_PATTERNS:
            for match in re.finditer(pattern, text):
                label = match.group(1)
                if label not in seen:
                    seen.add(label)
                    entities.append(Entity(
                        id=f"filing_{len(entities)}",
                        entity_type=EntityType.FILING,
                        label=label,
                    ))

        return entities
