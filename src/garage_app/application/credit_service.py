from __future__ import annotations

import uuid
from decimal import Decimal

from garage_app.application.decorators import require_permission
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.facturation.caisse import CreditClient
from garage_app.domain.facturation.repositories import CreditRepository
from garage_app.infrastructure.db.session import SessionFactory


class CreditService:
    def __init__(self, sf: SessionFactory, repo: CreditRepository) -> None:
        self._sf = sf
        self._repo = repo

    @require_permission(Permission.VIEW_FACTURES)
    def get_credit(self, session: UserSession, client_id: uuid.UUID) -> CreditClient:
        with self._sf.get_session():
            credit = self._repo.find_by_client(client_id)
            if not credit:
                credit = CreditClient(client_id=client_id)
            return credit

    @require_permission(Permission.VIEW_FACTURES)
    def list_credits(self, session: UserSession) -> list[CreditClient]:
        with self._sf.get_session():
            return self._repo.find_all_with_solde()

    @require_permission(Permission.MANAGE_FACTURES)
    def crediter_client(
        self,
        session: UserSession,
        client_id: uuid.UUID,
        montant: Decimal,
    ) -> CreditClient:
        with self._sf.get_session():
            credit = self._repo.find_by_client(client_id)
            if not credit:
                credit = CreditClient(client_id=client_id)
            if not credit.peut_crediter(montant):
                raise ValueError(
                    f"Crédit refusé: plafond de {credit.limite_credit:.3f} DT dépassé."
                )
            credit.solde += montant
            self._repo.save(credit)
        return credit

    @require_permission(Permission.MANAGE_FACTURES)
    def rembourser_credit(
        self,
        session: UserSession,
        client_id: uuid.UUID,
        montant: Decimal,
    ) -> CreditClient:
        with self._sf.get_session():
            credit = self._repo.find_by_client(client_id)
            if not credit:
                raise ValueError("Aucun crédit trouvé pour ce client.")
            if montant > credit.solde:
                raise ValueError(
                    f"Remboursement ({montant:.3f} DT) > solde dû ({credit.solde:.3f} DT)."
                )
            credit.solde -= montant
            self._repo.save(credit)
        return credit

    @require_permission(Permission.MANAGE_FACTURES)
    def definir_limite(
        self,
        session: UserSession,
        client_id: uuid.UUID,
        limite: Decimal,
    ) -> CreditClient:
        with self._sf.get_session():
            credit = self._repo.find_by_client(client_id)
            if not credit:
                credit = CreditClient(client_id=client_id)
            credit.limite_credit = limite
            self._repo.save(credit)
        return credit
