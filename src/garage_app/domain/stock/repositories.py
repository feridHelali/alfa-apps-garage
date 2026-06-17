from __future__ import annotations

from abc import abstractmethod

from garage_app.domain.stock.piece import Piece
from garage_app.domain.shared.repository import Repository


class PieceRepository(Repository[Piece]):
    @abstractmethod
    def search(self, query: str) -> list[Piece]: ...

    @abstractmethod
    def find_in_alert(self) -> list[Piece]: ...
