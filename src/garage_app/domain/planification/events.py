from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from garage_app.domain.shared.domain_event import DomainEvent


@dataclass(frozen=True)
class RendezVousPlanifie(DomainEvent):
    rendez_vous_id: uuid.UUID = uuid.uuid4()
    client_id: uuid.UUID = uuid.uuid4()
    date_heure: datetime = datetime.now()


@dataclass(frozen=True)
class VehiculeDepose(DomainEvent):
    vehicule_id: uuid.UUID = uuid.uuid4()
    dossier_id: uuid.UUID = uuid.uuid4()
