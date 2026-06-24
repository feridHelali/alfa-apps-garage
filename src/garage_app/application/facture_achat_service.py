from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from garage_app.application.decorators import require_permission
from garage_app.application.numerotation_service import NumerotationService
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.facturation.facture_achat import FactureAchat, LigneAchat, StatutAchat
from garage_app.domain.stock.repositories import PieceRepository
from garage_app.infrastructure.db.session import SessionFactory
from garage_app.infrastructure.repositories.facture_achat_repository import FactureAchatRepository


class FactureAchatService:
    def __init__(
        self,
        sf: SessionFactory,
        repo: FactureAchatRepository,
        piece_repo: PieceRepository,
        numerotation: NumerotationService,
    ) -> None:
        self._sf = sf
        self._repo = repo
        self._pieces = piece_repo
        self._numerotation = numerotation

    @require_permission(Permission.VIEW_STOCK)
    def list_factures_achat(self, session: UserSession) -> list[FactureAchat]:
        return self._repo.find_all()

    @require_permission(Permission.VIEW_STOCK)
    def get_facture_achat(self, session: UserSession, facture_id: uuid.UUID) -> FactureAchat | None:
        return self._repo.get_by_id(facture_id)

    @require_permission(Permission.MANAGE_STOCK)
    def creer_facture_achat(
        self,
        session: UserSession,
        fournisseur_id: uuid.UUID,
        numero_fournisseur: str,
        date_facture: datetime,
        lignes: list[dict],
        taux_tva: Decimal = Decimal("19"),
        date_echeance: datetime | None = None,
        notes: str = "",
    ) -> FactureAchat:
        notre_numero = self._numerotation.generer_numero("facture_achat")
        fa = FactureAchat(
            fournisseur_id=fournisseur_id,
            numero_fournisseur=numero_fournisseur,
            notre_numero=notre_numero,
            date_facture=date_facture,
            date_echeance=date_echeance,
            taux_tva=taux_tva,
            notes=notes,
        )
        for l in lignes:
            piece_id = uuid.UUID(str(l["piece_id"]))
            piece = self._pieces.get_by_id(piece_id)
            fa.lignes.append(LigneAchat(
                piece_id=piece_id,
                designation=l.get("designation") or (piece.designation if piece else "Pièce"),
                quantite=int(l["quantite"]),
                prix_unitaire=Decimal(str(l["prix_unitaire"])),
            ))
        self._repo.save(fa)
        return fa

    @require_permission(Permission.MANAGE_STOCK)
    def valider(self, session: UserSession, facture_id: uuid.UUID) -> FactureAchat:
        fa = self._repo.get_by_id(facture_id)
        if not fa:
            raise ValueError(f"Facture achat {facture_id} introuvable.")
        stock_updates = fa.valider()
        # Update stock and purchase price for each line
        with self._sf.get_session() as s:
            for piece_id, quantite, prix_unitaire in stock_updates:
                from garage_app.infrastructure.db.models.piece_model import PieceModel
                pm = s.get(PieceModel, str(piece_id))
                if pm:
                    pm.quantite_stock = (pm.quantite_stock or 0) + quantite
                    pm.prix_achat = float(prix_unitaire)
        self._repo.save(fa)
        return fa

    @require_permission(Permission.MANAGE_STOCK)
    def marquer_payee(self, session: UserSession, facture_id: uuid.UUID) -> FactureAchat:
        fa = self._repo.get_by_id(facture_id)
        if not fa:
            raise ValueError(f"Facture achat {facture_id} introuvable.")
        fa.marquer_payee()
        self._repo.save(fa)
        return fa

    @require_permission(Permission.MANAGE_STOCK)
    def annuler(self, session: UserSession, facture_id: uuid.UUID) -> FactureAchat:
        fa = self._repo.get_by_id(facture_id)
        if not fa:
            raise ValueError(f"Facture achat {facture_id} introuvable.")
        reversal = fa.annuler()
        if reversal:
            with self._sf.get_session() as s:
                for piece_id, quantite in reversal:
                    from garage_app.infrastructure.db.models.piece_model import PieceModel
                    pm = s.get(PieceModel, str(piece_id))
                    if pm:
                        pm.quantite_stock = max(0, (pm.quantite_stock or 0) - quantite)
        self._repo.save(fa)
        return fa
