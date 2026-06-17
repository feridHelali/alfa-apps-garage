from __future__ import annotations

import uuid
from decimal import Decimal

from garage_app.application.decorators import require_permission
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.stock.commande_fournisseur import CommandeFournisseur, StatutCommande
from garage_app.domain.stock.repositories import CommandeRepository, PieceRepository
from garage_app.infrastructure.db.session import SessionFactory
from garage_app.infrastructure.events.in_memory_event_bus import InMemoryEventBus
from garage_app.infrastructure.repositories.piece_repository import SqlAlchemyPieceRepository


class CommandeService:
    def __init__(
        self,
        sf: SessionFactory,
        commande_repo: CommandeRepository,
        piece_repo: PieceRepository,
        bus: InMemoryEventBus,
    ) -> None:
        self._sf = sf
        self._commande_repo = commande_repo
        self._piece_repo = piece_repo
        self._bus = bus

    @require_permission(Permission.VIEW_STOCK)
    def list_commandes(self, session: UserSession) -> list[CommandeFournisseur]:
        with self._sf.get_session():
            return self._commande_repo.find_all()

    @require_permission(Permission.VIEW_STOCK)
    def get_commande(self, session: UserSession, commande_id: uuid.UUID) -> CommandeFournisseur | None:
        with self._sf.get_session():
            return self._commande_repo.get_by_id(commande_id)

    @require_permission(Permission.MANAGE_STOCK)
    def create_commande(
        self,
        session: UserSession,
        fournisseur_id: uuid.UUID,
        lignes: list[tuple[uuid.UUID, str, int, float]],  # (piece_id, designation, qte, prix_ht)
        notes: str = "",
    ) -> CommandeFournisseur:
        commande = CommandeFournisseur(fournisseur_id=fournisseur_id, notes=notes)
        for piece_id, designation, qte, prix in lignes:
            commande.ajouter_ligne(piece_id, qte, prix, designation)
        with self._sf.get_session():
            self._commande_repo.save(commande)
        self._bus.publish_all(commande.pull_events())
        return commande

    @require_permission(Permission.MANAGE_STOCK)
    def envoyer_commande(self, session: UserSession, commande_id: uuid.UUID) -> CommandeFournisseur:
        with self._sf.get_session():
            c = self._commande_repo.get_by_id(commande_id)
            if not c:
                raise ValueError("Commande introuvable.")
            c.envoyer()
            self._commande_repo.save(c)
        self._bus.publish_all(c.pull_events())
        return c

    @require_permission(Permission.MANAGE_STOCK)
    def recevoir_tout(self, session: UserSession, commande_id: uuid.UUID) -> CommandeFournisseur:
        with self._sf.get_session():
            c = self._commande_repo.get_by_id(commande_id)
            if not c:
                raise ValueError("Commande introuvable.")
            events = c.recevoir_tout()
            self._commande_repo.save(c)
            # Update piece stock for each received line
            for ev in events:
                piece = self._piece_repo.get_by_id(ev.piece_id)
                if piece:
                    avant = piece.quantite_stock
                    piece.entrer_stock(ev.quantite)
                    self._piece_repo.save(piece)
                    if isinstance(self._piece_repo, SqlAlchemyPieceRepository):
                        self._piece_repo.add_mouvement(
                            piece_id=piece.id,
                            type_mouvement="entree",
                            quantite=ev.quantite,
                            quantite_avant=avant,
                            reference=f"CMD-{str(commande_id)[:8]}",
                            utilisateur_id=session.user_id,
                            utilisateur_nom=session.full_name,
                        )
        self._bus.publish_all(c.pull_events())
        return c

    @require_permission(Permission.MANAGE_STOCK)
    def recevoir_partiel(
        self,
        session: UserSession,
        commande_id: uuid.UUID,
        receptions: dict[uuid.UUID, int],
    ) -> CommandeFournisseur:
        with self._sf.get_session():
            c = self._commande_repo.get_by_id(commande_id)
            if not c:
                raise ValueError("Commande introuvable.")
            events = c.recevoir_partiel(receptions)
            self._commande_repo.save(c)
            for ev in events:
                piece = self._piece_repo.get_by_id(ev.piece_id)
                if piece:
                    avant = piece.quantite_stock
                    piece.entrer_stock(ev.quantite)
                    self._piece_repo.save(piece)
                    if isinstance(self._piece_repo, SqlAlchemyPieceRepository):
                        self._piece_repo.add_mouvement(
                            piece_id=piece.id,
                            type_mouvement="entree",
                            quantite=ev.quantite,
                            quantite_avant=avant,
                            reference=f"CMD-{str(commande_id)[:8]}",
                            utilisateur_id=session.user_id,
                            utilisateur_nom=session.full_name,
                        )
        self._bus.publish_all(c.pull_events())
        return c

    @require_permission(Permission.MANAGE_STOCK)
    def annuler_commande(self, session: UserSession, commande_id: uuid.UUID) -> CommandeFournisseur:
        with self._sf.get_session():
            c = self._commande_repo.get_by_id(commande_id)
            if not c:
                raise ValueError("Commande introuvable.")
            c.annuler()
            self._commande_repo.save(c)
        self._bus.publish_all(c.pull_events())
        return c
