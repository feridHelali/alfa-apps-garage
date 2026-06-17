from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from garage_app.domain.shared.aggregate_root import AggregateRoot
from garage_app.domain.shared.value_objects import Money
from garage_app.domain.shared.exceptions import BusinessRuleError


@dataclass
class MouvementCaisse:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    type: str = "entree"            # entree | sortie
    montant: Decimal = Decimal("0")
    motif: str = ""
    reference: str = ""             # facture ID, etc.
    horodatage: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    currency: str = "TND"

    def __post_init__(self) -> None:
        if not isinstance(self.id, uuid.UUID):
            self.id = uuid.UUID(str(self.id)) if self.id else uuid.uuid4()


@dataclass
class CreditClient:
    """Tracks outstanding customer balance (accounts-receivable)."""
    client_id: uuid.UUID = field(default_factory=uuid.uuid4)
    solde: Decimal = Decimal("0")       # positive = owes us money
    limite_credit: Decimal = Decimal("0")
    currency: str = "TND"

    def peut_crediter(self, montant: Decimal) -> bool:
        if self.limite_credit == Decimal("0"):
            return True  # unlimited credit (fleet/enterprise)
        return (self.solde + montant) <= self.limite_credit


@dataclass
class SessionCaisse(AggregateRoot):
    """
    A cashier session (journée de caisse).
    Opened at start of day, closed at end of day with reconciliation.
    """
    ouvert_par: uuid.UUID = field(default_factory=uuid.uuid4)   # user id
    solde_ouverture: Decimal = Decimal("0")
    currency: str = "TND"
    statut: str = "ouverte"     # ouverte | fermee
    mouvements: list[MouvementCaisse] = field(default_factory=list)
    ouvert_le: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ferme_le: datetime | None = None
    solde_fermeture_reel: Decimal | None = None

    @property
    def solde_theorique(self) -> Decimal:
        total = self.solde_ouverture
        for m in self.mouvements:
            if m.type == "entree":
                total += m.montant
            else:
                total -= m.montant
        return total

    def encaisser(self, montant: Decimal, motif: str, reference: str = "") -> None:
        self._assert_ouverte()
        if montant <= Decimal("0"):
            raise ValueError("Montant d'encaissement doit être positif.")
        self.mouvements.append(MouvementCaisse(
            type="entree", montant=montant, motif=motif, reference=reference, currency=self.currency
        ))

    def decaisser(self, montant: Decimal, motif: str) -> None:
        self._assert_ouverte()
        if montant > self.solde_theorique:
            raise BusinessRuleError(
                f"Solde insuffisant ({Money.of(self.solde_theorique).format()}). "
                f"Décaissement de {Money.of(montant).format()} refusé."
            )
        self.mouvements.append(MouvementCaisse(
            type="sortie", montant=montant, motif=motif, currency=self.currency
        ))

    def fermer(self, solde_reel: Decimal) -> Decimal:
        """Close session; returns écart (real - theoretical)."""
        self._assert_ouverte()
        self.statut = "fermee"
        self.ferme_le = datetime.now(timezone.utc)
        self.solde_fermeture_reel = solde_reel
        return solde_reel - self.solde_theorique

    def _assert_ouverte(self) -> None:
        if self.statut != "ouverte":
            raise BusinessRuleError("La session de caisse est déjà fermée.")
