from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum, auto

from garage_app.domain.shared.aggregate_root import AggregateRoot
from garage_app.domain.shared.entity import Entity


class StatutAchat(StrEnum):
    SAISIE = auto()
    VALIDEE = auto()
    PAYEE = auto()
    ANNULEE = auto()


@dataclass
class LigneAchat(Entity):
    piece_id: uuid.UUID = field(default_factory=uuid.uuid4)
    designation: str = ""
    quantite: int = 1
    prix_unitaire: Decimal = Decimal("0")

    @property
    def montant(self) -> Decimal:
        return self.quantite * self.prix_unitaire


@dataclass
class FactureAchat(AggregateRoot):
    fournisseur_id: uuid.UUID = field(default_factory=uuid.uuid4)
    numero_fournisseur: str = ""
    notre_numero: str = ""
    date_facture: datetime = field(default_factory=datetime.now)
    date_echeance: datetime | None = None
    statut: StatutAchat = StatutAchat.SAISIE
    commande_id: uuid.UUID | None = None
    notes: str = ""
    taux_tva: Decimal = Decimal("19")
    lignes: list[LigneAchat] = field(default_factory=list)

    # ── Computed ────────────────────────────────────────────────────────────

    @property
    def montant_ht(self) -> Decimal:
        return sum((l.montant for l in self.lignes), Decimal("0"))

    @property
    def montant_tva(self) -> Decimal:
        return self.montant_ht * self.taux_tva / Decimal("100")

    @property
    def montant_ttc(self) -> Decimal:
        return self.montant_ht + self.montant_tva

    # ── State machine ───────────────────────────────────────────────────────

    def valider(self) -> list[tuple[uuid.UUID, int, Decimal]]:
        """Returns list of (piece_id, quantite, prix_unitaire) for stock update."""
        if self.statut != StatutAchat.SAISIE:
            raise ValueError(f"Impossible de valider en statut '{self.statut}'.")
        if not self.lignes:
            raise ValueError("La facture doit contenir au moins une ligne.")
        self.statut = StatutAchat.VALIDEE
        return [(l.piece_id, l.quantite, l.prix_unitaire) for l in self.lignes]

    def marquer_payee(self) -> None:
        if self.statut != StatutAchat.VALIDEE:
            raise ValueError(f"Impossible de marquer payée en statut '{self.statut}'.")
        self.statut = StatutAchat.PAYEE

    def annuler(self) -> list[tuple[uuid.UUID, int]] | None:
        """Returns (piece_id, quantite) pairs to reverse if was VALIDEE, else None."""
        if self.statut == StatutAchat.ANNULEE:
            raise ValueError("Facture déjà annulée.")
        if self.statut == StatutAchat.PAYEE:
            raise ValueError("Impossible d'annuler une facture payée.")
        was_validee = self.statut == StatutAchat.VALIDEE
        self.statut = StatutAchat.ANNULEE
        if was_validee:
            return [(l.piece_id, l.quantite) for l in self.lignes]
        return None
