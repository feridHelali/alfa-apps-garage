from __future__ import annotations

import uuid
from abc import abstractmethod

from garage_app.domain.devis.devis import Devis, FactureProforma
from garage_app.domain.devis.statut_devis import StatutDevis, StatutProforma
from garage_app.domain.shared.repository import Repository


class DevisRepository(Repository[Devis]):
    @abstractmethod
    def find_by_client(self, client_id: uuid.UUID) -> list[Devis]: ...

    @abstractmethod
    def find_by_statut(self, statut: StatutDevis) -> list[Devis]: ...

    @abstractmethod
    def find_actifs(self) -> list[Devis]: ...


class ProformaRepository(Repository[FactureProforma]):
    @abstractmethod
    def find_by_client(self, client_id: uuid.UUID) -> list[FactureProforma]: ...

    @abstractmethod
    def find_by_devis(self, devis_id: uuid.UUID) -> FactureProforma | None: ...

    @abstractmethod
    def find_by_statut(self, statut: StatutProforma) -> list[FactureProforma]: ...
