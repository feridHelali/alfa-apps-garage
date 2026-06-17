from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from decimal import Decimal

from garage_app.domain.shared.aggregate_root import AggregateRoot
from garage_app.domain.shared.value_objects import Money
from garage_app.domain.facturation.events import FactureEmise, PaiementEncaisse


@dataclass
class LigneFacture:
    designation: str
    quantite: int
    prix_unitaire: Decimal

    @property
    def montant(self) -> Money:
        return Money.of(self.prix_unitaire * self.quantite)


@dataclass
class Facture(AggregateRoot):
    dossier_id: uuid.UUID = field(default_factory=uuid.uuid4)
    client_id: uuid.UUID = field(default_factory=uuid.uuid4)
    numero: str = ""
    lignes: list[LigneFacture] = field(default_factory=list)
    taux_tva: Decimal = Decimal("20.0")
    statut_paiement: str = "en_attente"
    mode_paiement: str = ""
    est_flotte: bool = False   # 30-day payment exemption

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

    def emettre(self) -> None:
        if not self.lignes:
            raise ValueError("La facture doit contenir au moins une ligne.")
        self._raise_event(FactureEmise(facture_id=self.id, montant_ttc=self.montant_ttc.amount))

    def enregistrer_paiement(self, mode: str) -> None:
        """Règle Anti-Vol: vehicle cannot be released until payment is recorded."""
        if self.statut_paiement == "paye":
            raise ValueError("Cette facture est déjà payée.")
        if not self.est_flotte and self.statut_paiement != "en_attente":
            raise ValueError("Statut de paiement invalide.")
        self.statut_paiement = "paye"
        self.mode_paiement = mode
        self._raise_event(PaiementEncaisse(facture_id=self.id, montant=self.montant_ttc.amount))
