"""
tests/test_sec_edgar_integration.py - SEC EDGAR integration tests.
"""
import pytest
from src.finance_kg.graph.knowledge_graph import FinanceKnowledgeGraph
from src.finance_kg.integrations.sec_edgar import SECEDGARIntegration


@pytest.fixture
def kg():
    return FinanceKnowledgeGraph()


@pytest.fixture
def integration(kg):
    return SECEDGARIntegration(kg)


class TestSECEDGARIntegration:
    def test_create(self, integration):
        assert integration is not None
        assert integration.kg is not None

    def test_load_filer_from_data(self, integration):
        filer = SECEDGARIntegration.generate_sample_filers()[0]
        uri = integration.load_filer_from_data(filer)
        assert uri is not None
        entity = integration.kg.get_entity(uri)
        assert entity is not None
        assert entity.entity_type == "Corporation"

    def test_load_10k_from_data(self, integration):
        # First load filer
        filer = SECEDGARIntegration.generate_sample_filers()[0]
        integration.load_filer_from_data(filer)
        filing = SECEDGARIntegration.generate_sample_10k()
        uri = integration.load_10k_from_data(filing)
        assert uri is not None
        entity = integration.kg.get_entity(uri)
        assert entity.entity_type == "FinancialStatement"

    def test_load_10q_from_data(self, integration):
        filer = SECEDGARIntegration.generate_sample_filers()[0]
        integration.load_filer_from_data(filer)
        filing = SECEDGARIntegration.generate_sample_10q()
        uri = integration.load_10q_from_data(filing)
        assert uri is not None
        entity = integration.kg.get_entity(uri)
        assert entity.entity_type == "FinancialStatement"

    def test_load_8k_from_data(self, integration):
        filer = SECEDGARIntegration.generate_sample_filers()[0]
        integration.load_filer_from_data(filer)
        filing = SECEDGARIntegration.generate_sample_8k()
        uri = integration.load_8k_from_data(filing)
        assert uri is not None
        entity = integration.kg.get_entity(uri)
        assert entity.entity_type == "CurrentReport"

    def test_load_insider_transaction_from_data(self, integration):
        filer = SECEDGARIntegration.generate_sample_filers()[0]
        integration.load_filer_from_data(filer)
        tx = SECEDGARIntegration.generate_sample_insider_transactions()[0]
        uri = integration.load_insider_transaction_from_data(tx)
        assert uri is not None
        entity = integration.kg.get_entity(uri)
        assert entity.entity_type == "InsiderTransaction"

    def test_load_executive_compensation_from_data(self, integration):
        filer = SECEDGARIntegration.generate_sample_filers()[0]
        integration.load_filer_from_data(filer)
        comp = SECEDGARIntegration.generate_sample_executive_compensation()[0]
        uri = integration.load_executive_compensation_from_data(comp)
        assert uri is not None
        entity = integration.kg.get_entity(uri)
        assert entity.entity_type == "ExecutiveCompensation"

    def test_cik_map_populated(self, integration):
        filer = SECEDGARIntegration.generate_sample_filers()[0]
        integration.load_filer_from_data(filer)
        assert "0000320193" in integration._cik_map

    def test_generate_sample_filers(self):
        filers = SECEDGARIntegration.generate_sample_filers()
        assert len(filers) == 2
        assert filers[0]["cik"] == "0000320193"

    def test_generate_sample_10k(self):
        filing = SECEDGARIntegration.generate_sample_10k()
        assert filing["form_type"] == "10-K"
        assert "items" in filing

    def test_generate_sample_10q(self):
        filing = SECEDGARIntegration.generate_sample_10q()
        assert filing["form_type"] == "10-Q"

    def test_generate_sample_8k(self):
        filing = SECEDGARIntegration.generate_sample_8k()
        assert filing["form_type"] == "8-K"

    def test_generate_sample_insider_transactions(self):
        txs = SECEDGARIntegration.generate_sample_insider_transactions()
        assert len(txs) == 2

    def test_generate_sample_executive_compensation(self):
        comps = SECEDGARIntegration.generate_sample_executive_compensation()
        assert len(comps) == 2

    def test_ten_k_items(self):
        assert "item_1" in SECEDGARIntegration.TEN_K_ITEMS
        assert "item_1a" in SECEDGARIntegration.TEN_K_ITEMS

    def test_ten_q_items(self):
        assert "item_1" in SECEDGARIntegration.TEN_Q_ITEMS

    def test_eight_k_items(self):
        assert "item_1_1" in SECEDGARIntegration.EIGHT_K_ITEMS

    def test_extract_risk_phrases(self):
        text = "The company faces significant risk from market competition. Regulatory changes could adversely affect results."
        phrases = SECEDGARIntegration._extract_risk_phrases(text)
        assert len(phrases) >= 1
