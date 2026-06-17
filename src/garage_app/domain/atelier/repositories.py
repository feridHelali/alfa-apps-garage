from __future__ import annotations

import uuid
from abc import abstractmethod

from garage_app.domain.atelier.dossier_reparation import DossierReparation
from garage_app.domain.atelier.statut_dossier import StatutDossier
from garage_app.domain.shared.repository import Repository


class DossierReparationRepository(Repository[DossierReparation]):
    @abstractmethod
    def find_by_vehicule(self, vehicule_id: uuid.UUID) -> list[DossierReparation]: ...

    @abstractmethod
    def find_by_statut(self, statut: StatutDossier) -> list[DossierReparation]: ...

    @abstractmethod
    def find_open(self) -> list[DossierReparation]: ...
