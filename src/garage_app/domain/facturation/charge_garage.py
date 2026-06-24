from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum, auto

from garage_app.domain.shared.aggregate_root import AggregateRoot


class CategorieCharge(StrEnum):
    LOYER = auto()
    ELECTRICITE = auto()
    EAU = auto()
    SALAIRES = auto()
    ASSURANCE = auto()
    CARBURANT = auto()
    MATERIEL = auto()
    ENTRETIEN = auto()
    AUTRE = auto()

    @classmethod
    def label(cls, val: str) -> str:
        labels = {
            cls.LOYER: "Loyer",
            cls.ELECTRICITE: "Électricité",
            cls.EAU: "Eau",
            cls.SALAIRES: "Salaires",
            cls.ASSURANCE: "Assurance",
            cls.CARBURANT: "Carburant",
            cls.MATERIEL: "Matériel",
            cls.ENTRETIEN: "Entretien",
            cls.AUTRE: "Autre",
        }
        try:
            return labels[cls(val)]
        except (ValueError, KeyError):
            return val.capitalize()


class PeriodiciteCharge(StrEnum):
    UNIQUE = auto()
    MENSUELLE = auto()
    TRIMESTRIELLE = auto()
    SEMESTRIELLE = auto()
    ANNUELLE = auto()

    @classmethod
    def label(cls, val: str) -> str:
        labels = {
            cls.UNIQUE: "Unique",
            cls.MENSUELLE: "Mensuelle",
            cls.TRIMESTRIELLE: "Trimestrielle",
            cls.SEMESTRIELLE: "Semestrielle",
            cls.ANNUELLE: "Annuelle",
        }
        try:
            return labels[cls(val)]
        except (ValueError, KeyError):
            return val.capitalize()


class StatutCharge(StrEnum):
    SAISIE = auto()
    PAYEE = auto()
    ANNULEE = auto()


@dataclass
class ChargeGarage(AggregateRoot):
    categorie: CategorieCharge = CategorieCharge.AUTRE
    description: str = ""
    montant: Decimal = Decimal("0")
    date_charge: datetime = field(default_factory=datetime.now)
    date_echeance: datetime | None = None
    periodicite: PeriodiciteCharge = PeriodiciteCharge.UNIQUE
    statut: StatutCharge = StatutCharge.SAISIE
    mode_paiement: str = ""
    reference_document: str = ""

    def marquer_payee(self, mode: str = "", reference: str = "") -> None:
        if self.statut != StatutCharge.SAISIE:
            raise ValueError(f"Impossible de payer en statut '{self.statut}'.")
        self.statut = StatutCharge.PAYEE
        self.mode_paiement = mode
        self.reference_document = reference

    def annuler(self) -> None:
        if self.statut == StatutCharge.ANNULEE:
            raise ValueError("Charge déjà annulée.")
        self.statut = StatutCharge.ANNULEE
