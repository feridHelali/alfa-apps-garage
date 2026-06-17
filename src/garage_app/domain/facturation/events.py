from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from decimal import Decimal

from garage_app.domain.shared.domain_event import DomainEvent


@dataclass(frozen=True)
class FactureEmise(DomainEvent):
    facture_id: uuid.UUID = field(default_factory=uuid.uuid4)
    montant_ttc: Decimal = Decimal("0")


@dataclass(frozen=True)
class PaiementEncaisse(DomainEvent):
    facture_id: uuid.UUID = field(default_factory=uuid.uuid4)
    montant: Decimal = Decimal("0")


@dataclass(frozen=True)
class VehiculeRestitue(DomainEvent):
    dossier_id: uuid.UUID = field(default_factory=uuid.uuid4)
    client_id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass(frozen=True)
class FactureAnnulee(DomainEvent):
    facture_id: uuid.UUID = field(default_factory=uuid.uuid4)
