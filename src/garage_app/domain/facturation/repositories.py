from __future__ import annotations

import uuid
from abc import abstractmethod
from datetime import date

from garage_app.domain.facturation.caisse import CreditClient, SessionCaisse
from garage_app.domain.facturation.facture import Facture, StatutFacture
from garage_app.domain.shared.repository import Repository


class FactureRepository(Repository[Facture]):
    @abstractmethod
    def find_by_dossier(self, dossier_id: uuid.UUID) -> Facture | None: ...

    @abstractmethod
    def find_by_statut(self, statut: StatutFacture) -> list[Facture]: ...

    @abstractmethod
    def find_impayees(self) -> list[Facture]: ...

    @abstractmethod
    def find_by_client(self, client_id: uuid.UUID) -> list[Facture]: ...

    @abstractmethod
    def next_numero(self) -> str: ...


class CaisseRepository(Repository[SessionCaisse]):
    @abstractmethod
    def find_session_active(self) -> SessionCaisse | None: ...

    @abstractmethod
    def find_by_date(self, jour: date) -> list[SessionCaisse]: ...


class CreditRepository(Repository[CreditClient]):
    @abstractmethod
    def find_by_client(self, client_id: uuid.UUID) -> CreditClient | None: ...

    @abstractmethod
    def find_all_with_solde(self) -> list[CreditClient]: ...
