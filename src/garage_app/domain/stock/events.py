from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from garage_app.domain.shared.domain_event import DomainEvent


@dataclass(frozen=True)
class FournisseurCree(DomainEvent):
    fournisseur_id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass(frozen=True)
class CommandeCreee(DomainEvent):
    commande_id: uuid.UUID = field(default_factory=uuid.uuid4)
    fournisseur_id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass(frozen=True)
class CommandeEnvoyee(DomainEvent):
    commande_id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass(frozen=True)
class PiecesRecues(DomainEvent):
    commande_id: uuid.UUID = field(default_factory=uuid.uuid4)
    piece_id: uuid.UUID = field(default_factory=uuid.uuid4)
    quantite: int = 0


@dataclass(frozen=True)
class StockAlerteDeclenchee(DomainEvent):
    piece_id: uuid.UUID = field(default_factory=uuid.uuid4)
    quantite: int = 0


@dataclass(frozen=True)
class InventaireAjuste(DomainEvent):
    piece_id: uuid.UUID = field(default_factory=uuid.uuid4)
    ancienne_quantite: int = 0
    nouvelle_quantite: int = 0
