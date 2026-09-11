"""
Finance KG - SEC filing parser.

Regex-based extraction from SEC filings (10-K, 10-Q, 8-K, S-1, 13F, DEF 14A).
"""

from __future__ import annotations
from typing import Optional
import re


class SECFilingParser:
    """Parser for SEC filing documents."""

    # Form type patterns
    FORM_TYPES = ["10-K", "10-Q", "8-K", "S-1", "13F", "DEF 14A"]

    # Section patterns for 10-K
    SECTIONS_10K = [
        ("business", r"Item\s*1\.?\s*Business"),
        ("risk_factors", r"Item\s*1A\.?\s*Risk\s*Factors"),
        ("properties", r"Item\s*2\.?\s*Properties"),
        ("legal", r"Item\s*3\.?\s*Legal\s*Proceedings"),
        ("financials", r"Item\s*7\.?.*Financial"),
        ("controls", r"Item\s*9A\.?\s*Controls"),
    ]

    def parse(self, filing_path: str) -> list[dict]:
        """Parse an SEC filing and return sections."""
        try:
            with open(filing_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except FileNotFoundError:
            return [{"text": "", "section": "file_not_found", "form_type": "unknown"}]

        # Detect form type
        form_type = self._detect_form_type(content)

        # Split into sections
        sections = self._split_sections(content, form_type)

        return sections

    def _detect_form_type(self, content: str) -> str:
        """Detect the SEC form type from content."""
        for form_type in self.FORM_TYPES:
            if form_type in content:
                return form_type
        return "unknown"

    def _split_sections(self, content: str, form_type: str) -> list[dict]:
        """Split filing into sections based on form type."""
        sections = []

        if form_type == "10-K":
            for section_name, pattern in self.SECTIONS_10K:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    # Extract text from this section to the next
                    start = match.start()
                    # Find next section start
                    end = len(content)
                    for _, next_pattern in self.SECTIONS_10K:
                        next_match = re.search(next_pattern, content[start+1:], re.IGNORECASE)
                        if next_match and next_match.start() + start + 1 > start:
                            potential_end = next_match.start() + start + 1
                            if potential_end < end:
                                end = potential_end

                    section_text = content[start:end].strip()
                    sections.append({
                        "text": section_text,
                        "section": section_name,
                        "form_type": form_type,
                    })

        if not sections:
            # Return the whole content as one section
            sections.append({
                "text": content,
                "section": "full",
                "form_type": form_type,
            })

        return sections
