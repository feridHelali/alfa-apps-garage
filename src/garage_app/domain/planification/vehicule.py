from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from garage_app.domain.shared.entity import Entity


@dataclass
class Vehicule(Entity):
    client_id: uuid.UUID = field(default_factory=uuid.uuid4)
    immatriculation: str = ""
    vin: str = ""
    marque: str = ""
    modele: str = ""
    annee: int = 0
    couleur: str = ""

    @property
    def designation(self) -> str:
        return f"{self.marque} {self.modele} ({self.annee}) — {self.immatriculation}"
