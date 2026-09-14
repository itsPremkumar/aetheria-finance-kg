"""
tests/test_sec_patterns.py - SEC filing parser tests (old finance_kg package).
"""
import pytest

from finance_kg.sec_patterns import SECFilingParser


class TestSECFilingParser:
    def test_create(self):
        parser = SECFilingParser()
        assert parser is not None

    def test_parse_10k_filing(self, tmp_path):
        filing_file = tmp_path / "filing.txt"
        filing_file.write_text("This is a 10-K filing for Apple Inc.")
        parser = SECFilingParser()
        result = parser.parse(str(filing_file))
        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0]["form_type"] == "10-K"

    def test_parse_10q_filing(self, tmp_path):
        filing_file = tmp_path / "filing.txt"
        filing_file.write_text("This is a 10-Q filing.")
        parser = SECFilingParser()
        result = parser.parse(str(filing_file))
        assert result[0]["form_type"] == "10-Q"

    def test_parse_8k_filing(self, tmp_path):
        filing_file = tmp_path / "filing.txt"
        filing_file.write_text("This is an 8-K filing.")
        parser = SECFilingParser()
        result = parser.parse(str(filing_file))
        assert result[0]["form_type"] == "8-K"

    def test_parse_file_not_found(self):
        parser = SECFilingParser()
        result = parser.parse("/nonexistent/path.txt")
        assert isinstance(result, list)
        assert result[0]["section"] == "file_not_found"

    def test_detect_form_type_10k(self):
        parser = SECFilingParser()
        form_type = parser._detect_form_type("This is a 10-K filing.")
        assert form_type == "10-K"

    def test_detect_form_type_10q(self):
        parser = SECFilingParser()
        form_type = parser._detect_form_type("This is a 10-Q filing.")
        assert form_type == "10-Q"

    def test_detect_form_type_unknown(self):
        parser = SECFilingParser()
        form_type = parser._detect_form_type("Random content without form type.")
        assert form_type == "unknown"

    def test_split_sections_10k(self):
        parser = SECFilingParser()
        content = """
        Item 1. Business
        Apple designs smartphones.
        
        Item 1A. Risk Factors
        Competition is intense.
        
        Item 2. Properties
        Office locations.
        """
        sections = parser._split_sections(content, "10-K")
        assert len(sections) >= 1
        assert any(s["section"] == "business" for s in sections)

    def test_split_sections_full_content(self):
        parser = SECFilingParser()
        content = "This is just text without sections."
        sections = parser._split_sections(content, "unknown")
        assert len(sections) == 1
        assert sections[0]["section"] == "full"

    def test_form_types(self):
        parser = SECFilingParser()
        assert "10-K" in parser.FORM_TYPES
        assert "10-Q" in parser.FORM_TYPES
        assert "8-K" in parser.FORM_TYPES

    def test_sections_10k(self):
        parser = SECFilingParser()
        assert len(parser.SECTIONS_10K) >= 4
        section_names = [s[0] for s in parser.SECTIONS_10K]
        assert "business" in section_names
        assert "risk_factors" in section_names
