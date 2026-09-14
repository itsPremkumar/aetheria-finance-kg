"""
tests/test_fineract_integration.py - Apache Fineract integration tests.
"""
import pytest
from src.finance_kg.graph.knowledge_graph import FinanceKnowledgeGraph
from src.finance_kg.integrations.fineract import FineractIntegration, FineractConfig


@pytest.fixture
def kg():
    return FinanceKnowledgeGraph()


@pytest.fixture
def integration(kg):
    return FineractIntegration(kg)


class TestFineractConfig:
    def test_default_config(self):
        config = FineractConfig()
        assert config.base_url == "https://demo.fineract.dev/fineract-provider/api/v1"
        assert config.tenant_id == "default"
        assert config.username == "mifos"
        assert config.password == "password"
        assert config.page_size == 200

    def test_custom_config(self):
        config = FineractConfig(
            base_url="https://custom.fineract.dev/api/v1",
            tenant_id="custom_tenant",
            username="admin",
            password="secret",
            page_size=500,
        )
        assert config.tenant_id == "custom_tenant"
        assert config.page_size == 500


class TestFineractIntegration:
    def test_create(self, integration):
        assert integration is not None
        assert integration.kg is not None

    def test_load_clients_from_data(self, integration):
        clients = FineractIntegration.generate_sample_clients()
        uris = integration.load_clients_from_data(clients)
        assert len(uris) == 3

    def test_load_clients_empty(self, integration):
        uris = integration.load_clients_from_data([])
        assert len(uris) == 0

    def test_load_loans_from_data(self, integration):
        clients = FineractIntegration.generate_sample_clients()
        integration.load_clients_from_data(clients)
        loans = FineractIntegration.generate_sample_loans()
        uris = integration.load_loans_from_data(loans)
        assert len(uris) == 2

    def test_load_loans_empty(self, integration):
        uris = integration.load_loans_from_data([])
        assert len(uris) == 0

    def test_load_savings_from_data(self, integration):
        clients = FineractIntegration.generate_sample_clients()
        integration.load_clients_from_data(clients)
        savings = FineractIntegration.generate_sample_savings()
        uris = integration.load_savings_from_data(savings)
        assert len(uris) == 2

    def test_load_savings_empty(self, integration):
        uris = integration.load_savings_from_data([])
        assert len(uris) == 0

    def test_load_gl_accounts_from_data(self, integration):
        accounts = FineractIntegration.generate_sample_gl_accounts()
        uris = integration.load_gl_accounts_from_data(accounts)
        assert len(uris) == 5

    def test_load_gl_accounts_empty(self, integration):
        uris = integration.load_gl_accounts_from_data([])
        assert len(uris) == 0

    def test_load_transactions_from_data(self, integration):
        clients = FineractIntegration.generate_sample_clients()
        integration.load_clients_from_data(clients)
        loans = FineractIntegration.generate_sample_loans()
        integration.load_loans_from_data(loans)
        transactions = FineractIntegration.generate_sample_transactions()
        uris = integration.load_loan_transactions_from_data(transactions)
        assert len(uris) == 2

    def test_load_transactions_empty(self, integration):
        uris = integration.load_loan_transactions_from_data([])
        assert len(uris) == 0

    def test_client_mapping(self, integration):
        clients = [{"id": 1, "firstname": "John", "lastname": "Doe", "status": {"value": "Active"}}]
        uris = integration.load_clients_from_data(clients)
        entity = integration.kg.get_entity(uris[0])
        assert entity is not None
        assert "John" in entity.label

    def test_organization_client_mapping(self, integration):
        clients = [{"id": 1, "fullname": "Acme Corp", "status": {"value": "Active"}}]
        uris = integration.load_clients_from_data(clients)
        entity = integration.kg.get_entity(uris[0])
        assert entity is not None
        assert entity.entity_type == "Organization"

    def test_loan_links_to_client(self, integration):
        clients = FineractIntegration.generate_sample_clients()
        integration.load_clients_from_data(clients)
        loans = FineractIntegration.generate_sample_loans()
        loan_uris = integration.load_loans_from_data(loans)
        # Check that loan entity exists
        entity = integration.kg.get_entity(loan_uris[0])
        assert entity is not None
        assert entity.entity_type == "Loan"

    def test_parse_fineract_date(self):
        result = FineractIntegration._parse_fineract_date([2023, 1, 15])
        assert result == "2023-01-15"

    def test_parse_fineract_date_string(self):
        result = FineractIntegration._parse_fineract_date("2023-01-15")
        assert result == "2023-01-15"

    def test_parse_fineract_date_invalid(self):
        result = FineractIntegration._parse_fineract_date(None)
        assert result is None

    def test_generate_sample_clients(self):
        clients = FineractIntegration.generate_sample_clients()
        assert len(clients) == 3
        assert clients[0]["id"] == 1

    def test_generate_sample_loans(self):
        loans = FineractIntegration.generate_sample_loans()
        assert len(loans) == 2
        assert loans[0]["principal"] == 5000.00

    def test_generate_sample_savings(self):
        savings = FineractIntegration.generate_sample_savings()
        assert len(savings) == 2

    def test_generate_sample_gl_accounts(self):
        accounts = FineractIntegration.generate_sample_gl_accounts()
        assert len(accounts) == 5

    def test_generate_sample_transactions(self):
        transactions = FineractIntegration.generate_sample_transactions()
        assert len(transactions) == 2
