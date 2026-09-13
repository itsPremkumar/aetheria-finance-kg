"""
ontology/__init__.py
"""

from .fibo import FIBOOntology
from .namespaces import (
    FIBO, FIBO_FBC, FIBO_SEC, FINANCE,
    FINERACT, OPENBB, SEC as SEC_NS,
    DEFAULT_PREFIXES,
)

__all__ = [
    "FIBOOntology",
    "FIBO", "FIBO_FBC", "FIBO_SEC", "FINANCE",
    "FINERACT", "OPENBB", "SEC_NS",
    "DEFAULT_PREFIXES",
]
