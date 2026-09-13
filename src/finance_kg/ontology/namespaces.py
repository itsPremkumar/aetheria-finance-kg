"""
ontology/namespaces.py - RDF namespace definitions for Finance KG.

Defines all RDF namespaces used across the project.
FIBO is the primary ontology; custom namespaces extend it
for Fineract, OpenBB, and SEC filing data.
"""

from rdflib import Namespace, RDF, RDFS, OWL, XSD, SKOS, DCTERMS

# FIBO (Financial Industry Business Ontology) - primary ontology
FIBO = Namespace("https://spec.edmcouncil.org/fibo/ontology/")

# FIBO specific domains
FIBO_BE = Namespace("https://spec.edmcouncil.org/fibo/ontology/BE/")
FIBO_FBC = Namespace("https://spec.edmcouncil.org/fibo/ontology/FBC/")
FIBO_IND = Namespace("https://spec.edmcouncil.org/fibo/ontology/IND/")
FIBO_SEC = Namespace("https://spec.edmcouncil.org/fibo/ontology/SEC/")

# Custom namespaces for integrations
FINERACT = Namespace("https://aetheria.finance/kg/fineract/")
OPENBB = Namespace("https://aetheria.finance/kg/openbb/")
SEC = Namespace("https://aetheria.finance/kg/sec/")
FINANCE = Namespace("https://aetheria.finance/kg/finance/")

# Common prefixes for SPARQL queries
DEFAULT_PREFIXES = """
    PREFIX fibo: <https://spec.edmcouncil.org/fibo/ontology/>
    PREFIX fibo-fbc: <https://spec.edmcouncil.org/fibo/ontology/FBC/>
    PREFIX fibo-sec: <https://spec.edmcouncil.org/fibo/ontology/SEC/>
    PREFIX fineract: <https://aetheria.finance/kg/fineract/>
    PREFIX openbb: <https://aetheria.finance/kg/openbb/>
    PREFIX sec: <https://aetheria.finance/kg/sec/>
    PREFIX finance: <https://aetheria.finance/kg/finance/>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
"""
