from __future__ import annotations

import uuid
from dataclasses import dataclass

from garage_app.domain.shared.domain_event import DomainEvent


@dataclass(frozen=True)
class StockAlerteDeclenchee(DomainEvent):
    piece_id: uuid.UUID = uuid.uuid4()
    quantite: int = 0


@dataclass(frozen=True)
class PiecesCommandees(DomainEvent):
    piece_id: uuid.UUID = uuid.uuid4()
    quantite: int = 0
    fournisseur_id: uuid.UUID = uuid.uuid4()


@dataclass(frozen=True)
class PiecesRecues(DomainEvent):
    commande_id: uuid.UUID = uuid.uuid4()
    piece_id: uuid.UUID = uuid.uuid4()
    quantite: int = 0
