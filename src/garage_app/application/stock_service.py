from __future__ import annotations

import uuid

from garage_app.application.decorators import require_permission
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.stock.piece import Piece
from garage_app.domain.stock.repositories import PieceRepository
from garage_app.infrastructure.db.session import SessionFactory
from garage_app.infrastructure.events.in_memory_event_bus import InMemoryEventBus
from garage_app.infrastructure.repositories.piece_repository import SqlAlchemyPieceRepository


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
    def search_pieces(self, session: UserSession, query: str) -> list[Piece]:
        with self._sf.get_session():
            return self._repo.search(query)

    @require_permission(Permission.VIEW_STOCK)
    def get_piece(self, session: UserSession, piece_id: uuid.UUID) -> Piece | None:
        with self._sf.get_session():
            return self._repo.get_by_id(piece_id)

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
    def update_piece(self, session: UserSession, piece: Piece) -> Piece:
        with self._sf.get_session():
            existing = self._repo.get_by_id(piece.id)
            if not existing:
                raise ValueError("Pièce introuvable.")
            self._repo.save(piece)
        return piece

    @require_permission(Permission.MANAGE_STOCK)
    def delete_piece(self, session: UserSession, piece_id: uuid.UUID) -> None:
        with self._sf.get_session():
            self._repo.delete(piece_id)

    @require_permission(Permission.MANAGE_STOCK)
    def entrer_stock(
        self,
        session: UserSession,
        piece_id: uuid.UUID,
        quantite: int,
        reference: str = "",
    ) -> Piece:
        with self._sf.get_session():
            piece = self._repo.get_by_id(piece_id)
            if not piece:
                raise ValueError("Pièce introuvable.")
            avant = piece.quantite_stock
            piece.entrer_stock(quantite)
            self._repo.save(piece)
            if isinstance(self._repo, SqlAlchemyPieceRepository):
                self._repo.add_mouvement(
                    piece_id=piece.id,
                    type_mouvement="entree",
                    quantite=quantite,
                    quantite_avant=avant,
                    reference=reference,
                    utilisateur_id=session.user_id,
                    utilisateur_nom=session.full_name,
                )
        self._bus.publish_all(piece.pull_events())
        return piece

    @require_permission(Permission.MANAGE_STOCK)
    def sortir_stock(
        self,
        session: UserSession,
        piece_id: uuid.UUID,
        quantite: int,
        reference: str = "",
    ) -> Piece:
        with self._sf.get_session():
            piece = self._repo.get_by_id(piece_id)
            if not piece:
                raise ValueError("Pièce introuvable.")
            avant = piece.quantite_stock
            piece.sortir_stock(quantite)
            self._repo.save(piece)
            if isinstance(self._repo, SqlAlchemyPieceRepository):
                self._repo.add_mouvement(
                    piece_id=piece.id,
                    type_mouvement="sortie",
                    quantite=quantite,
                    quantite_avant=avant,
                    reference=reference,
                    utilisateur_id=session.user_id,
                    utilisateur_nom=session.full_name,
                )
        self._bus.publish_all(piece.pull_events())
        return piece

    @require_permission(Permission.MANAGE_STOCK)
    def ajuster_stock(
        self,
        session: UserSession,
        piece_id: uuid.UUID,
        nouvelle_quantite: int,
        reference: str = "Inventaire",
    ) -> Piece:
        with self._sf.get_session():
            piece = self._repo.get_by_id(piece_id)
            if not piece:
                raise ValueError("Pièce introuvable.")
            avant = piece.quantite_stock
            piece.ajuster_stock(nouvelle_quantite)
            self._repo.save(piece)
            if isinstance(self._repo, SqlAlchemyPieceRepository):
                self._repo.add_mouvement(
                    piece_id=piece.id,
                    type_mouvement="ajustement",
                    quantite=nouvelle_quantite - avant,
                    quantite_avant=avant,
                    reference=reference,
                    utilisateur_id=session.user_id,
                    utilisateur_nom=session.full_name,
                )
        self._bus.publish_all(piece.pull_events())
        return piece
