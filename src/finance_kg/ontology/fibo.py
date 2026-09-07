"""
ontology/fibo.py - FIBO ontology wrapper.

Provides a Pythonic interface to the Financial Industry Business Ontology.
Loads FIBO classes relevant to financial knowledge graphs:
- Organizations and legal entities
- Financial instruments
- Loans and credit
- Securities and equities
- Accounting concepts
- Issuers and investors

Designed for 100% offline use — ships with a minimal embedded FIBO subset.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, RDFS, OWL

from .namespaces import FIBO, FIBO_FBC, FIBO_SEC, FINANCE, DEFAULT_PREFIXES


@dataclass
class FIBOClass:
    """Represents a FIBO ontology class."""
    uri: URIRef
    label: str
    definition: str = ""
    parent: Optional[URIRef] = None


@dataclass
class FIBOProperty:
    """Represents a FIBO ontology property."""
    uri: URIRef
    label: str
    domain: Optional[URIRef] = None
    range: Optional[URIRef] = None


class FIBOOntology:
    """
    FIBO Ontology wrapper for financial knowledge graphs.
    
    Provides:
    - Core FIBO class hierarchy for finance
    - Lookup methods for classes and properties
    - Validation against FIBO constraints
    - Export to RDF/Turtle for sharing
    
    Usage:
        ontology = FIBOOntology()
        company_cls = ontology.get_class("Organization")
        ontology.validate_entity(entity_uri, "Company")
    """

    # Core FIBO classes relevant to finance
    CORE_CLASSES = {
        # Organizations
        "Organization": "An organized group of persons together with "
                        "the infrastructure, resources, and rules for operation",
        "LegalEntity": "An organization recognized by law as having "
                       "rights and obligations",
        "BusinessEntity": "A legal entity that conducts business activity",
        "Corporation": "A business entity that has a legal identity "
                       "distinct from its owners",
        "Company": "A business entity — commonly used shorthand",
        "FinancialInstitution": "A business entity that provides "
                                 "financial services",
        "Bank": "A financial institution that accepts deposits and "
                "makes loans",
        "CreditUnion": "A member-owned financial institution",
        "InvestmentFirm": "A business entity that manages investments",
        "HedgeFund": "An investment fund using pooled capital",
        "PrivateEquityFirm": "An investment firm in private companies",
        
        # Financial Instruments
        "FinancialInstrument": "A tradable asset of any kind — "
                               "money, evidence of ownership, or a contract",
        "Security": "A financial instrument that represents an ownership "
                    "position or a creditor relationship",
        "EquitySecurity": "A security representing ownership in a corporation",
        "Stock": "An equity security — share of ownership in a company",
        "Bond": "A debt security — a fixed income instrument representing "
                "a loan from an investor to a borrower",
        "DebtSecurity": "A security representing borrowed money",
        "Derivative": "A security whose value depends on an underlying asset",
        
        # Loans & Credit
        "Loan": "A financial agreement where a lender gives a borrower "
                "an amount of money to be repaid with interest",
        "LoanFacility": "A loan that has been approved and is available",
        "Mortgage": "A loan secured by real property",
        "CreditFacility": "An arrangement for borrowing up to a limit",
        "CreditAgreement": "A contract governing a credit facility",
        "LineOfCredit": "A credit facility allowing flexible borrowing",
        
        # Securities & Equities
        "Issuer": "An entity that issues securities",
        "Shareholder": "An entity that holds shares in a corporation",
        "Investor": "An entity that allocates capital with expectation of return",
        "StockExchange": "A marketplace for trading securities",
        "Market": "A venue for buying and selling financial instruments",
        
        # Accounting
        "Accounting": "The process of recording financial transactions",
        "FinancialReporting": "The disclosure of financial information",
        "BalanceSheet": "A statement of financial position",
        "IncomeStatement": "A statement of financial performance",
        "CashFlowStatement": "A statement of cash flows",
        "FinancialStatement": "A formal record of financial activities",
        "Asset": "A resource with economic value controlled by an entity",
        "Liability": "A present obligation arising from past events",
        "Equity": "The residual interest in assets after deducting liabilities",
        "Revenue": "Income from ordinary activities",
        "Expense": "Outflows from ordinary activities",
        
        # Corporate Actions
        "Merger": "A combination of two companies into one",
        "Acquisition": "One company purchasing a controlling interest in another",
        "SpinOff": "A company divesting a business unit",
        "Investment": "The allocation of capital to assets for return",
        "Stake": "An ownership percentage in a company",
        
        # People & Roles
        "Person": "A human being",
        "Executive": "A senior officer of a corporation",
        "Director": "A member of a board of directors",
        "ChiefExecutiveOfficer": "The highest-ranking executive",
        "ChiefFinancialOfficer": "The executive responsible for financial matters",
        
        # Ratings & Risk
        "CreditRating": "An evaluation of creditworthiness",
        "RiskAssessment": "An evaluation of potential adverse outcomes",
        "Collateral": "An asset pledged to secure a loan",
    }

    # Core FIBO properties
    CORE_PROPERTIES = {
        "hasName": ("has name", None, None),
        "hasLegalName": ("has legal name", "LegalEntity", "Literal"),
        "hasIdentifier": ("has identifier", None, "Identifier"),
        "hasTicker": ("has ticker symbol", "Corporation", "Literal"),
        "isIncorporatedIn": ("is incorporated in", "Corporation", "Jurisdiction"),
        "hasHeadquarters": ("has headquarters", "Organization", "Location"),
        "hasCEO": ("has CEO", "Corporation", "Person"),
        "hasCFO": ("has CFO", "Corporation", "Person"),
        "hasEmployeeCount": ("has employee count", "Organization", "Integer"),
        "hasRevenue": ("has revenue", "Organization", "MonetaryAmount"),
        "hasTotalAssets": ("has total assets", "LegalEntity", "MonetaryAmount"),
        "hasTotalLiabilities": ("has total liabilities", "LegalEntity", "MonetaryAmount"),
        "hasNetIncome": ("has net income", "LegalEntity", "MonetaryAmount"),
        "hasStockPrice": ("has stock price", "Stock", "MonetaryAmount"),
        "hasMarketCap": ("has market capitalization", "Corporation", "MonetaryAmount"),
        "hasCreditRating": ("has credit rating", "LegalEntity", "CreditRating"),
        "hasISIN": ("has ISIN", "Security", "Literal"),
        "hasCUSIP": ("has CUSIP", "Security", "Literal"),
        "issuedBy": ("issued by", "Security", "Issuer"),
        "issuedTo": ("issued to", "Security", "Investor"),
        "hasLoanAmount": ("has loan amount", "Loan", "MonetaryAmount"),
        "hasInterestRate": ("has interest rate", "Loan", "Percentage"),
        "hasMaturityDate": ("has maturity date", "Loan", "Date"),
        "hasCollateral": ("has collateral", "Loan", "Asset"),
        "mergedWith": ("merged with", "Corporation", "Corporation"),
        "acquired": ("acquired", "Corporation", "Corporation"),
        "investedIn": ("invested in", "Investor", "LegalEntity"),
        "holdsStake": ("holds stake in", "Investor", "LegalEntity"),
        "hasStakePercentage": ("has stake percentage", "Stake", "Percentage"),
        "subsidiaryOf": ("subsidiary of", "Corporation", "Corporation"),
        "parentOf": ("parent of", "Corporation", "Corporation"),
        "competesWith": ("competes with", "Corporation", "Corporation"),
        "suppliesTo": ("supplies to", "Corporation", "Corporation"),
        "customerOf": ("customer of", "Corporation", "Corporation"),
    }

    def __init__(self) -> None:
        """Initialize FIBO ontology with embedded core classes."""
        self.graph = Graph()
        self._bind_namespaces()
        self._build_core_ontology()
        self._class_index: dict[str, FIBOClass] = {}
        self._property_index: dict[str, FIBOProperty] = {}
        self._build_indices()

    def _bind_namespaces(self) -> None:
        """Bind all namespaces to the graph."""
        self.graph.bind("fibo", FIBO)
        self.graph.bind("fibo-fbc", FIBO_FBC)
        self.graph.bind("fibo-sec", FIBO_SEC)
        self.graph.bind("finance", FINANCE)
        self.graph.bind("owl", OWL)

    def _build_core_ontology(self) -> None:
        """Build the embedded FIBO core subset."""
        for class_name, definition in self.CORE_CLASSES.items():
            uri = FINANCE[class_name]
            self.graph.add((uri, RDF.type, OWL.Class))
            self.graph.add((uri, RDFS.label, Literal(class_name)))
            self.graph.add((uri, RDFS.comment, Literal(definition)))

        for prop_name, (label, domain, range_) in self.CORE_PROPERTIES.items():
            uri = FINANCE[prop_name]
            self.graph.add((uri, RDF.type, RDF.Property))
            self.graph.add((uri, RDFS.label, Literal(label)))
            if domain:
                domain_uri = FINANCE[domain]
                self.graph.add((uri, RDFS.domain, domain_uri))
            if range_:
                range_uri = FINANCE[range_]
                self.graph.add((uri, RDFS.range, range_uri))

    def _build_indices(self) -> None:
        """Build class and property lookup indices."""
        for s, p, o in self.graph.triples((None, RDF.type, OWL.Class)):
            label = str(self.graph.value(s, RDFS.label) or s.split("/")[-1])
            definition = str(self.graph.value(s, RDFS.comment) or "")
            parent = self.graph.value(s, RDFS.subClassOf)
            self._class_index[label] = FIBOClass(
                uri=s, label=label, definition=definition, parent=parent
            )

        for s, p, o in self.graph.triples((None, RDF.type, RDF.Property)):
            label = str(self.graph.value(s, RDFS.label) or s.split("/")[-1])
            domain = self.graph.value(s, RDFS.domain)
            range_ = self.graph.value(s, RDFS.range)
            self._property_index[label] = FIBOProperty(
                uri=s, label=label, domain=domain, range=range_
            )

    def get_class(self, name: str) -> Optional[FIBOClass]:
        """Get a FIBO class by name."""
        return self._class_index.get(name)

    def get_property(self, name: str) -> Optional[FIBOProperty]:
        """Get a FIBO property by name."""
        return self._property_index.get(name)

    def get_all_classes(self) -> list[FIBOClass]:
        """Get all FIBO classes."""
        return list(self._class_index.values())

    def get_all_properties(self) -> list[FIBOProperty]:
        """Get all FIBO properties."""
        return list(self._property_index.values())

    def search_classes(self, query: str) -> list[FIBOClass]:
        """Search FIBO classes by name or definition."""
        query_lower = query.lower()
        return [
            cls for cls in self._class_index.values()
            if query_lower in cls.label.lower() or query_lower in cls.definition.lower()
        ]

    def validate_entity(self, entity_uri: URIRef, class_name: str) -> bool:
        """Check if an entity URI is a valid instance of the given class."""
        cls = self._class_index.get(class_name)
        if cls is None:
            return False
        for s, p, o in self.graph.triples((entity_uri, RDF.type, cls.uri)):
            return True
        return False

    def export(self, format: str = "turtle") -> str:
        """Export the ontology as RDF."""
        return self.graph.serialize(format=format)

    def export_to_file(self, path: Path, format: str = "turtle") -> None:
        """Export ontology to a file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.export(format=format))

    def merge_to_graph(self, target: Graph) -> None:
        """Merge this ontology into an existing RDF graph."""
        target += self.graph

    def __len__(self) -> int:
        """Number of triples in the ontology."""
        return len(self.graph)

    def __repr__(self) -> str:
        return f"FIBOOntology(classes={len(self._class_index)}, properties={len(self._property_index)})"
