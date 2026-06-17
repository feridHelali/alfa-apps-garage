from __future__ import annotations

import uuid
from abc import abstractmethod

from garage_app.domain.facturation.facture import Facture
from garage_app.domain.shared.repository import Repository


class FactureRepository(Repository[Facture]):
    @abstractmethod
    def find_by_dossier(self, dossier_id: uuid.UUID) -> Facture | None: ...

    @abstractmethod
    def find_impayees(self) -> list[Facture]: ...

    @abstractmethod
    def next_numero(self) -> str: ...
