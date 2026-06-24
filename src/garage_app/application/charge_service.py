from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from garage_app.application.decorators import require_permission
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.facturation.charge_garage import (
    CategorieCharge, ChargeGarage, PeriodiciteCharge,
)
from garage_app.infrastructure.repositories.charge_garage_repository import ChargeGarageRepository


class ChargeService:
    def __init__(self, repo: ChargeGarageRepository) -> None:
        self._repo = repo

    @require_permission(Permission.MANAGE_SETTINGS)
    def list_charges(self, session: UserSession) -> list[ChargeGarage]:
        return self._repo.find_all()

    @require_permission(Permission.MANAGE_SETTINGS)
    def list_charges_periode(
        self, session: UserSession, debut: datetime, fin: datetime
    ) -> list[ChargeGarage]:
        return self._repo.find_by_periode(debut, fin)

    @require_permission(Permission.MANAGE_SETTINGS)
    def get_charge(self, session: UserSession, charge_id: uuid.UUID) -> ChargeGarage | None:
        return self._repo.get_by_id(charge_id)

    @require_permission(Permission.MANAGE_SETTINGS)
    def creer_charge(
        self,
        session: UserSession,
        categorie: str,
        description: str,
        montant: Decimal,
        date_charge: datetime,
        periodicite: str = "unique",
        date_echeance: datetime | None = None,
        reference_document: str = "",
    ) -> ChargeGarage:
        charge = ChargeGarage(
            categorie=CategorieCharge(categorie),
            description=description,
            montant=montant,
            date_charge=date_charge,
            date_echeance=date_echeance,
            periodicite=PeriodiciteCharge(periodicite),
            reference_document=reference_document,
        )
        self._repo.save(charge)
        return charge

    @require_permission(Permission.MANAGE_SETTINGS)
    def modifier_charge(
        self,
        session: UserSession,
        charge_id: uuid.UUID,
        categorie: str,
        description: str,
        montant: Decimal,
        date_charge: datetime,
        periodicite: str = "unique",
        date_echeance: datetime | None = None,
        reference_document: str = "",
    ) -> ChargeGarage:
        charge = self._repo.get_by_id(charge_id)
        if not charge:
            raise ValueError(f"Charge {charge_id} introuvable.")
        charge.categorie = CategorieCharge(categorie)
        charge.description = description
        charge.montant = montant
        charge.date_charge = date_charge
        charge.date_echeance = date_echeance
        charge.periodicite = PeriodiciteCharge(periodicite)
        charge.reference_document = reference_document
        self._repo.save(charge)
        return charge

    @require_permission(Permission.MANAGE_SETTINGS)
    def marquer_payee(
        self,
        session: UserSession,
        charge_id: uuid.UUID,
        mode: str = "",
        reference: str = "",
    ) -> ChargeGarage:
        charge = self._repo.get_by_id(charge_id)
        if not charge:
            raise ValueError(f"Charge {charge_id} introuvable.")
        charge.marquer_payee(mode=mode, reference=reference)
        self._repo.save(charge)
        return charge

    @require_permission(Permission.MANAGE_SETTINGS)
    def annuler(self, session: UserSession, charge_id: uuid.UUID) -> ChargeGarage:
        charge = self._repo.get_by_id(charge_id)
        if not charge:
            raise ValueError(f"Charge {charge_id} introuvable.")
        charge.annuler()
        self._repo.save(charge)
        return charge

    @require_permission(Permission.MANAGE_SETTINGS)
    def reconduire(self, session: UserSession, charge_id: uuid.UUID) -> ChargeGarage:
        """Duplicate a recurring charge for the next period."""
        charge = self._repo.get_by_id(charge_id)
        if not charge:
            raise ValueError(f"Charge {charge_id} introuvable.")
        nouvelle = ChargeGarage(
            categorie=charge.categorie,
            description=charge.description,
            montant=charge.montant,
            date_charge=datetime.now(),
            periodicite=charge.periodicite,
        )
        self._repo.save(nouvelle)
        return nouvelle

    @require_permission(Permission.MANAGE_SETTINGS)
    def supprimer(self, session: UserSession, charge_id: uuid.UUID) -> None:
        self._repo.delete(charge_id)
