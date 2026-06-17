from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum, auto

from garage_app.domain.shared.aggregate_root import AggregateRoot
from garage_app.domain.shared.entity import Entity
from garage_app.domain.shared.value_objects import Money
from garage_app.domain.facturation.events import FactureEmise, PaiementEncaisse, VehiculeRestitue


class StatutFacture(StrEnum):
    BROUILLON = auto()
    EMISE = auto()
    PARTIELLEMENT_PAYEE = auto()
    PAYEE = auto()
    ANNULEE = auto()


class ModePaiement(StrEnum):
    ESPECES = auto()
    CHEQUE = auto()
    VIREMENT = auto()
    CARTE = auto()
    CREDIT = auto()

    @classmethod
    def label(cls, mode: str) -> str:
        labels = {
            cls.ESPECES: "Espèces", cls.CHEQUE: "Chèque",
            cls.VIREMENT: "Virement", cls.CARTE: "Carte",
            cls.CREDIT: "Crédit client",
        }
        try:
            return labels[cls(mode)]
        except (ValueError, KeyError):
            return mode.capitalize()


@dataclass
class LigneFacture:
    designation: str
    quantite: int
    prix_unitaire: Decimal

    @property
    def montant(self) -> Money:
        return Money.of(self.prix_unitaire * self.quantite)


@dataclass
class Paiement(Entity):
    montant: Decimal = Decimal("0")
    mode: str = ModePaiement.ESPECES
    date_paiement: datetime = field(default_factory=datetime.now)
    reference: str = ""


@dataclass
class Facture(AggregateRoot):
    dossier_id: uuid.UUID = field(default_factory=uuid.uuid4)
    client_id: uuid.UUID = field(default_factory=uuid.uuid4)
    numero: str = ""
    lignes: list[LigneFacture] = field(default_factory=list)
    taux_tva: Decimal = Decimal("19")   # Tunisia standard TVA
    statut: StatutFacture = StatutFacture.BROUILLON
    est_flotte: bool = False
    paiements: list[Paiement] = field(default_factory=list)
    notes: str = ""

    # ── Computed properties ─────────────────────────────────────────────────

    @property
    def montant_ht(self) -> Money:
        total = Money.zero()
        for l in self.lignes:
            total = total + l.montant
        return total

    @property
    def montant_tva(self) -> Money:
        return Money.of(self.montant_ht.amount * self.taux_tva / Decimal("100"))

    @property
    def montant_ttc(self) -> Money:
        return self.montant_ht + self.montant_tva

    @property
    def montant_paye(self) -> Decimal:
        return sum((p.montant for p in self.paiements), Decimal("0"))

    @property
    def solde_restant(self) -> Decimal:
        return max(Decimal("0"), self.montant_ttc.amount - self.montant_paye)

    @property
    def est_soldee(self) -> bool:
        return self.statut == StatutFacture.PAYEE

    # ── State machine ───────────────────────────────────────────────────────

    def emettre(self) -> None:
        if self.statut != StatutFacture.BROUILLON:
            raise ValueError(f"La facture est déjà en statut '{self.statut}'.")
        if not self.lignes:
            raise ValueError("La facture doit contenir au moins une ligne.")
        self.statut = StatutFacture.EMISE
        self._raise_event(FactureEmise(facture_id=self.id, montant_ttc=self.montant_ttc.amount))

    def enregistrer_paiement(self, montant: Decimal, mode: str, reference: str = "") -> None:
        if self.statut not in (StatutFacture.EMISE, StatutFacture.PARTIELLEMENT_PAYEE):
            raise ValueError(f"Impossible d'encaisser en statut '{self.statut}'.")
        if montant <= Decimal("0"):
            raise ValueError("Le montant doit être positif.")
        if montant > self.solde_restant:
            raise ValueError(
                f"Paiement ({Money.of(montant).format()}) "
                f"dépasse le solde restant ({Money.of(self.solde_restant).format()})."
            )
        paiement = Paiement(montant=montant, mode=mode, reference=reference)
        self.paiements.append(paiement)
        self._raise_event(
            PaiementEncaisse(facture_id=self.id, montant=montant)
        )
        if self.solde_restant == Decimal("0"):
            self.statut = StatutFacture.PAYEE
            self._raise_event(VehiculeRestitue(dossier_id=self.dossier_id, client_id=self.client_id))
        else:
            self.statut = StatutFacture.PARTIELLEMENT_PAYEE

    def annuler(self) -> None:
        if self.statut == StatutFacture.PAYEE:
            raise ValueError("Impossible d'annuler une facture déjà payée.")
        if self.statut == StatutFacture.ANNULEE:
            raise ValueError("Facture déjà annulée.")
        self.statut = StatutFacture.ANNULEE
        from garage_app.domain.facturation.events import FactureAnnulee
        self._raise_event(FactureAnnulee(facture_id=self.id))
