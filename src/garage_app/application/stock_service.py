from __future__ import annotations

from garage_app.application.decorators import require_permission
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.stock.piece import Piece
from garage_app.domain.stock.repositories import PieceRepository
from garage_app.infrastructure.db.session import SessionFactory
from garage_app.infrastructure.events.in_memory_event_bus import InMemoryEventBus


class StockService:
    def __init__(self, sf: SessionFactory, repo: PieceRepository, bus: InMemoryEventBus) -> None:
        self._sf = sf
        self._repo = repo
        self._bus = bus

    @require_permission(Permission.VIEW_STOCK)
    def list_pieces(self, session: UserSession) -> list[Piece]:
        with self._sf.get_session():
            return self._repo.find_all()

    @require_permission(Permission.VIEW_STOCK)
    def pieces_en_alerte(self, session: UserSession) -> list[Piece]:
        with self._sf.get_session():
            return self._repo.find_in_alert()

    @require_permission(Permission.MANAGE_STOCK)
    def create_piece(self, session: UserSession, piece: Piece) -> Piece:
        with self._sf.get_session():
            self._repo.save(piece)
        return piece

    @require_permission(Permission.MANAGE_STOCK)
    def entrer_stock(self, session: UserSession, piece_id, quantite: int) -> Piece:
        with self._sf.get_session():
            piece = self._repo.get_by_id(piece_id)
            if not piece:
                raise ValueError(f"Pièce introuvable.")
            piece.entrer_stock(quantite)
            self._repo.save(piece)
        self._bus.publish_all(piece.pull_events())
        return piece
