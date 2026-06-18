from __future__ import annotations

import uuid
from abc import abstractmethod
from datetime import date

from garage_app.domain.planification.client import Client
from garage_app.domain.planification.vehicule import Vehicule
from garage_app.domain.planification.rendez_vous import RendezVous
from garage_app.domain.shared.repository import Repository


class ClientRepository(Repository[Client]):
    @abstractmethod
    def search(self, query: str) -> list[Client]: ...


class VehiculeRepository(Repository[Vehicule]):
    @abstractmethod
    def find_by_client(self, client_id: uuid.UUID) -> list[Vehicule]: ...

    @abstractmethod
    def get_by_immatriculation(self, immat: str) -> Vehicule | None: ...


class RendezVousRepository(Repository[RendezVous]):
    @abstractmethod
    def find_upcoming(self) -> list[RendezVous]: ...

    @abstractmethod
    def find_by_date(self, target: date) -> list[RendezVous]: ...

    @abstractmethod
    def find_by_month(self, year: int, month: int) -> list[RendezVous]: ...
