from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from garage_app.domain.facturation.charge_garage import (
    CategorieCharge, ChargeGarage, PeriodiciteCharge, StatutCharge,
)
from garage_app.infrastructure.db.models.charge_garage_model import ChargeGarageModel
from garage_app.infrastructure.db.session import SessionFactory


class ChargeGarageRepository:
    def __init__(self, sf: SessionFactory) -> None:
        self._sf = sf

    def get_by_id(self, entity_id: uuid.UUID) -> ChargeGarage | None:
        with self._sf.get_session() as s:
            m = s.get(ChargeGarageModel, str(entity_id))
            return self._to_domain(m) if m else None

    def find_all(self) -> list[ChargeGarage]:
        with self._sf.get_session() as s:
            rows = (
                s.query(ChargeGarageModel)
                .order_by(ChargeGarageModel.date_charge.desc())
                .all()
            )
            return [self._to_domain(m) for m in rows]

    def find_by_periode(self, debut: datetime, fin: datetime) -> list[ChargeGarage]:
        with self._sf.get_session() as s:
            rows = (
                s.query(ChargeGarageModel)
                .filter(
                    ChargeGarageModel.date_charge >= debut,
                    ChargeGarageModel.date_charge <= fin,
                )
                .order_by(ChargeGarageModel.date_charge.desc())
                .all()
            )
            return [self._to_domain(m) for m in rows]

    def save(self, c: ChargeGarage) -> None:
        with self._sf.get_session() as s:
            m = s.get(ChargeGarageModel, str(c.id))
            if m:
                m.statut = c.statut.value
                m.mode_paiement = c.mode_paiement
                m.reference_document = c.reference_document
                m.description = c.description
                m.montant = float(c.montant)
                m.date_echeance = c.date_echeance
            else:
                m = ChargeGarageModel(
                    id=str(c.id),
                    categorie=c.categorie.value,
                    description=c.description,
                    montant=float(c.montant),
                    date_charge=c.date_charge,
                    date_echeance=c.date_echeance,
                    periodicite=c.periodicite.value,
                    statut=c.statut.value,
                    mode_paiement=c.mode_paiement,
                    reference_document=c.reference_document,
                )
                s.add(m)

    def delete(self, entity_id: uuid.UUID) -> None:
        with self._sf.get_session() as s:
            m = s.get(ChargeGarageModel, str(entity_id))
            if m:
                s.delete(m)

    @staticmethod
    def _to_domain(m: ChargeGarageModel) -> ChargeGarage:
        c = ChargeGarage(id=uuid.UUID(m.id))
        try:
            c.categorie = CategorieCharge(m.categorie)
        except ValueError:
            c.categorie = CategorieCharge.AUTRE
        c.description = m.description or ""
        c.montant = Decimal(str(m.montant or 0))
        c.date_charge = m.date_charge if isinstance(m.date_charge, datetime) else datetime.now()
        c.date_echeance = m.date_echeance if isinstance(m.date_echeance, datetime) else None
        try:
            c.periodicite = PeriodiciteCharge(m.periodicite)
        except ValueError:
            c.periodicite = PeriodiciteCharge.UNIQUE
        try:
            c.statut = StatutCharge(m.statut)
        except ValueError:
            c.statut = StatutCharge.SAISIE
        c.mode_paiement = m.mode_paiement or ""
        c.reference_document = m.reference_document or ""
        return c
