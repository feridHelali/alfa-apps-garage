from __future__ import annotations

import uuid
from abc import abstractmethod

from garage_app.domain.shared.repository import Repository
from garage_app.domain.stock.commande_fournisseur import CommandeFournisseur, StatutCommande
from garage_app.domain.stock.fournisseur import Fournisseur
from garage_app.domain.stock.piece import Piece


class PieceRepository(Repository[Piece]):
    @abstractmethod
    def search(self, query: str) -> list[Piece]: ...

    @abstractmethod
    def find_in_alert(self) -> list[Piece]: ...

    @abstractmethod
    def find_by_fournisseur(self, fournisseur_id: uuid.UUID) -> list[Piece]: ...


class FournisseurRepository(Repository[Fournisseur]):
    @abstractmethod
    def find_actifs(self) -> list[Fournisseur]: ...

    @abstractmethod
    def find_by_raison_sociale(self, query: str) -> list[Fournisseur]: ...


class CommandeRepository(Repository[CommandeFournisseur]):
    @abstractmethod
    def find_by_statut(self, statut: StatutCommande) -> list[CommandeFournisseur]: ...

    @abstractmethod
    def find_by_fournisseur(self, fournisseur_id: uuid.UUID) -> list[CommandeFournisseur]: ...
