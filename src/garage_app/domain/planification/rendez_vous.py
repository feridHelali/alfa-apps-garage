from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from garage_app.domain.shared.aggregate_root import AggregateRoot
from garage_app.domain.planification.events import RendezVousPlanifie


@dataclass
class RendezVous(AggregateRoot):
    client_id: uuid.UUID = field(default_factory=uuid.uuid4)
    vehicule_id: uuid.UUID = field(default_factory=uuid.uuid4)
    date_heure: datetime = field(default_factory=datetime.now)
    motif: str = ""
    statut: str = "planifie"  # planifie | confirme | annule | termine

    def __post_init__(self) -> None:
        self._raise_event(RendezVousPlanifie(
            rendez_vous_id=self.id,
            client_id=self.client_id,
            date_heure=self.date_heure,
        ))

    def confirmer(self) -> None:
        self.statut = "confirme"

    def annuler(self) -> None:
        self.statut = "annule"

    def terminer(self) -> None:
        self.statut = "termine"
