"""
tests/test_sec_parser.py - SEC filing parser tests.
"""
import pytest

from src.finance_kg.sec_parser import (
    SECFilingParser,
    ParsedFiling,
    TICKER_PATTERN,
    AMOUNT_PATTERN,
    DATE_PATTERN,
    CIK_PATTERN,
    COMPANY_NAME_PATTERN,
    ACQUISITION_PATTERN,
    INVESTMENT_PATTERN,
    MERGER_PATTERN,
)
from src.finance_kg.models import EntityType, RelationType


class TestSECFilingParser:
    def test_create(self):
        parser = SECFilingParser()
        assert parser is not None

    def test_parse_10k_filing(self):
        parser = SECFilingParser()
        text = """
        Apple Inc. (NASDAQ: AAPL) filed its annual report on Form 10-K.
        Total net sales were $383,285,000,000 for the fiscal year ending September 30, 2023.
        CIK: 0000320193
        """
        result = parser.parse(text, form_type="10-K")
        assert isinstance(result, ParsedFiling)
        assert result.form_type == "10-K"
        assert result.cik == "0000320193"

    def test_parse_extracts_company_names(self):
        parser = SECFilingParser()
        text = "Apple Inc. designs smartphones. Microsoft Corp. develops software."
        result = parser.parse(text)
        assert len(result.company_names) >= 1

    def test_parse_extracts_tickers(self):
        parser = SECFilingParser()
        text = "Apple (AAPL) and Microsoft (MSFT) are competitors."
        result = parser.parse(text)
        assert len(result.tickers) >= 1

    def test_parse_extracts_amounts(self):
        parser = SECFilingParser()
        text = "Revenue was $100,000,000 and profit was $25,000,000."
        result = parser.parse(text)
        assert len(result.amounts) >= 1

    def test_parse_extracts_dates(self):
        parser = SECFilingParser()
        text = "Filing date is January 15, 2024. Fiscal year ended 2023-09-30."
        result = parser.parse(text)
        assert len(result.dates) >= 1

    def test_parse_extracts_cik(self):
        parser = SECFilingParser()
        text = "The company's CIK is 0000320193."
        result = parser.parse(text)
        assert result.cik == "0000320193"

    def test_extract_triples(self):
        parser = SECFilingParser()
        text = "Apple Inc. acquired Beats Electronics for $3 billion."
        parsed = parser.parse(text)
        triples = parser.extract_triples(parsed)
        assert len(triples) >= 1
        assert triples[0].subject.type == EntityType.COMPANY

    def test_extract_triples_with_acquisitions(self):
        parser = SECFilingParser()
        text = "Microsoft Corp. acquired Activision Blizzard for $69 billion."
        parsed = parser.parse(text)
        triples = parser.extract_triples(parsed)
        assert any(t.predicate == RelationType.ACQUIRED for t in triples)

    def test_extract_triples_with_investments(self):
        parser = SECFilingParser()
        text = "Google LLC invested in artificial intelligence research."
        parsed = parser.parse(text)
        triples = parser.extract_triples(parsed)
        assert len(triples) >= 1

    def test_extract_triples_with_mergers(self):
        parser = SECFilingParser()
        text = "Exxon Corp. merged with Mobil Corp. to form ExxonMobil."
        parsed = parser.parse(text)
        triples = parser.extract_triples(parsed)
        assert any(t.predicate == RelationType.MERGED_WITH for t in triples)

    def test_parse_empty_text(self):
        parser = SECFilingParser()
        result = parser.parse("")
        assert isinstance(result, ParsedFiling)
        assert result.form_type == "10-K"

    def test_parse_8k_filing(self):
        parser = SECFilingParser()
        text = "Form 8-K filed by Apple Inc. CIK: 0000320193"
        result = parser.parse(text, form_type="8-K")
        assert result.form_type == "8-K"

    def test_parse_10q_filing(self):
        parser = SECFilingParser()
        text = "Form 10-Q filed for Q1 2024. Revenue was $100,000."
        result = parser.parse(text, form_type="10-Q")
        assert result.form_type == "10-Q"


class TestRegexPatterns:
    def test_ticker_pattern_parentheses(self):
        match = TICKER_PATTERN.search("Apple (AAPL)")
        assert match is not None

    def test_amount_pattern_dollars(self):
        match = AMOUNT_PATTERN.search("Revenue was $1,000,000")
        assert match is not None

    def test_amount_pattern_words(self):
        match = AMOUNT_PATTERN.search("The deal was worth 3 billion")
        assert match is not None

    def test_date_pattern_long(self):
        match = DATE_PATTERN.search("January 15, 2024")
        assert match is not None

    def test_date_pattern_iso(self):
        match = DATE_PATTERN.search("2024-01-15")
        assert match is not None

    def test_cik_pattern(self):
        match = CIK_PATTERN.search("CIK: 0000320193")
        assert match is not None
        assert match.group(1) == "0000320193"

    def test_company_name_pattern(self):
        match = COMPANY_NAME_PATTERN.search("Apple Inc. filed today")
        assert match is not None

    def test_acquisition_pattern(self):
        match = ACQUISITION_PATTERN.search("Apple Inc. acquired Beats Electronics")
        assert match is not None

    def test_investment_pattern(self):
        match = INVESTMENT_PATTERN.search("Google invested in AI startup")
        assert match is not None

    def test_merger_pattern(self):
        match = MERGER_PATTERN.search("Exxon merged with Mobil")
        assert match is not None
