from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from garage_app.domain.facturation.caisse import CreditClient
from garage_app.domain.facturation.repositories import CreditRepository
from garage_app.infrastructure.db.models.facture_model import CreditClientModel


class SqlAlchemyCreditRepository(CreditRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def get_by_id(self, entity_id: uuid.UUID) -> CreditClient | None:
        m = self._s.get(CreditClientModel, str(entity_id))
        return self._to_domain(m) if m else None

    def find_by_client(self, client_id: uuid.UUID) -> CreditClient | None:
        m = self._s.query(CreditClientModel).filter_by(client_id=str(client_id)).first()
        return self._to_domain(m) if m else None

    def find_all_with_solde(self) -> list[CreditClient]:
        rows = (
            self._s.query(CreditClientModel)
            .filter(CreditClientModel.solde > 0)
            .order_by(CreditClientModel.solde.desc())
            .all()
        )
        return [self._to_domain(m) for m in rows]

    def find_all(self) -> list[CreditClient]:
        return [self._to_domain(m) for m in self._s.query(CreditClientModel).all()]

    def save(self, credit: CreditClient) -> None:
        m = self._s.query(CreditClientModel).filter_by(client_id=str(credit.client_id)).first()
        if m:
            m.solde = float(credit.solde)
            m.limite_credit = float(credit.limite_credit)
            m.currency = credit.currency
            m.derniere_mise_a_jour = datetime.now(timezone.utc)
        else:
            self._s.add(CreditClientModel(
                id=str(uuid.uuid4()),
                client_id=str(credit.client_id),
                solde=float(credit.solde),
                limite_credit=float(credit.limite_credit),
                currency=credit.currency,
                derniere_mise_a_jour=datetime.now(timezone.utc),
            ))

    def delete(self, entity_id: uuid.UUID) -> None:
        m = self._s.get(CreditClientModel, str(entity_id))
        if m:
            self._s.delete(m)

    @staticmethod
    def _to_domain(m: CreditClientModel) -> CreditClient:
        credit = CreditClient(client_id=uuid.UUID(m.client_id))
        credit.solde = Decimal(str(m.solde or 0))
        credit.limite_credit = Decimal(str(m.limite_credit or 0))
        credit.currency = m.currency or "TND"
        return credit
