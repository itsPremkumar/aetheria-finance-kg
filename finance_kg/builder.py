"""
Finance KG - Knowledge graph builder.

Builds the knowledge graph from Fineract and OpenBB data sources.
"""

from __future__ import annotations
from typing import Any, Optional


class KGBuilder:
    """Builds the knowledge graph from various data sources."""

    def __init__(
        self,
        graph,
        entity_extractor,
        relation_extractor,
        cache,
    ):
        self.graph = graph
        self.entity_extractor = entity_extractor
        self.relation_extractor = relation_extractor
        self.cache = cache

    def build_from_fineract(self, fineract_client, client_id: Optional[str] = None) -> dict[str, Any]:
        """Build knowledge graph from Fineract data."""
        entities = []
        relations = []

        if client_id:
            # Get specific client
            client = fineract_client.get_client(client_id)
            client_entities = self._extract_client_entities(client)
            entities.extend(client_entities)

            # Get loans
            loans = fineract_client.get_loans(client_id)
            for loan in loans:
                loan_entity = self._extract_loan_entity(loan)
                entities.append(loan_entity)
                relations.append(self._create_relationship(
                    client_entities[0].id if client_entities else "unknown",
                    loan_entity.id,
                    "HAS_LOAN",
                ))

            # Get savings
            savings = fineract_client.get_savings(client_id)
            for savings_acc in savings:
                account_entity = self._extract_account_entity(savings_acc)
                entities.append(account_entity)
                relations.append(self._create_relationship(
                    client_entities[0].id if client_entities else "unknown",
                    account_entity.id,
                    "HAS_ACCOUNT",
                ))
        else:
            # Get all clients
            clients = fineract_client.get_clients()
            for client in clients:
                client_entities = self._extract_client_entities(client)
                entities.extend(client_entities)

        self.graph.add_entities(entities)
        self.graph.add_relations(relations)

        return {"entities": len(entities), "relations": len(relations)}

    def build_from_openbb(self, openbb_client, symbols: list[str]) -> dict[str, Any]:
        """Build knowledge graph from OpenBB market data."""
        entities = []
        relations = []

        for symbol in symbols:
            # Get stock info
            info = openbb_client.get_stock_info(symbol)
            if info and "error" not in info:
                security_entity = self._extract_security_entity(info)
                entities.append(security_entity)

                # Get company info for relations
                financials = openbb_client.get_financials(symbol)
                if financials and "error" not in financials:
                    company_entity = self._extract_company_from_financials(financials)
                    if company_entity:
                        entities.append(company_entity)
                        relations.append(self._create_relationship(
                            company_entity.id,
                            security_entity.id,
                            "ISSUES",
                        ))

        self.graph.add_entities(entities)
        self.graph.add_relations(relations)

        return {"entities": len(entities), "relations": len(relations)}

    def _extract_client_entities(self, client: dict) -> list:
        """Extract entities from Fineract client data."""
        from .entities import Entity, EntityType

        entities = []
        client_id = str(client.get("id", ""))
        display_name = client.get("displayName", "")

        if display_name:
            entities.append(Entity(
                id=f"fineract_client_{client_id}",
                entity_type=EntityType.PERSON,
                label=display_name,
                source="fineract",
                properties={"fineract_id": client_id},
            ))

        return entities

    def _extract_loan_entity(self, loan: dict):
        """Extract entity from loan data."""
        from .entities import Entity, EntityType

        loan_id = str(loan.get("id", ""))
        loan_type = loan.get("loanType", "individual")

        return Entity(
            id=f"fineract_loan_{loan_id}",
            entity_type=EntityType.LOAN,
            label=f"Loan #{loan_id}",
            source="fineract",
            properties={
                "loan_id": loan_id,
                "loan_type": loan_type,
            },
        )

    def _extract_account_entity(self, account: dict):
        """Extract entity from account data."""
        from .entities import Entity, EntityType

        account_id = str(account.get("id", ""))
        account_type = account.get("accountType", "savings")

        return Entity(
            id=f"fineract_account_{account_id}",
            entity_type=EntityType.ACCOUNT,
            label=f"Account #{account_id}",
            source="fineract",
            properties={
                "account_id": account_id,
                "account_type": account_type,
            },
        )

    def _extract_security_entity(self, info: dict):
        """Extract entity from OpenBB security info."""
        from .entities import Entity, EntityType

        symbol = info.get("symbol", "")
        name = info.get("name", symbol)

        return Entity(
            id=f"openbb_security_{symbol}",
            entity_type=EntityType.SECURITY,
            label=name,
            source="openbb",
            properties={"symbol": symbol},
        )

    def _extract_company_from_financials(self, financials: dict):
        """Extract company entity from financials data."""
        from .entities import Entity, EntityType

        name = financials.get("name", "")
        if not name:
            return None

        return Entity(
            id=f"openbb_company_{name.replace(' ', '_')}",
            entity_type=EntityType.COMPANY,
            label=name,
            source="openbb",
        )

    def _create_relationship(self, source_id: str, target_id: str, rel_type: str):
        """Create a relationship."""
        from .relations import Relation, RelationType

        return Relation(
            id=f"rel_{source_id}_{target_id}",
            relation_type=RelationType(rel_type) if rel_type in [e.value for e in RelationType] else RelationType.OWNS_SECURITY,
            source_id=source_id,
            target_id=target_id,
        )
