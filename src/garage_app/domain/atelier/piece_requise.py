from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from decimal import Decimal

from garage_app.domain.shared.entity import Entity
from garage_app.domain.atelier.statut_dossier import StatutDispo
from garage_app.domain.shared.value_objects import Money


@dataclass
class PieceRequise(Entity):
    piece_id: uuid.UUID = field(default_factory=uuid.uuid4)
    reference: str = ""
    designation: str = ""
    quantite: int = 1
    prix_unitaire: Decimal = Decimal("0")
    statut_dispo: StatutDispo = StatutDispo.EN_STOCK

    @property
    def montant(self) -> Money:
        return Money.of(self.prix_unitaire * self.quantite)
