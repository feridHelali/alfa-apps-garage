from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from garage_app.domain.stock.piece import Piece
from garage_app.domain.stock.repositories import PieceRepository
from garage_app.infrastructure.db.models.piece_model import MouvementStockModel, PieceModel
from garage_app.infrastructure.db.session import SessionFactory


class SqlAlchemyPieceRepository(PieceRepository):
    def __init__(self, sf: SessionFactory) -> None:
        self._sf = sf

    def get_by_id(self, entity_id: uuid.UUID) -> Piece | None:
        with self._sf.get_session() as s:
            m = s.get(PieceModel, str(entity_id))
            return self._to_domain(m) if m else None

    def find_all(self) -> list[Piece]:
        with self._sf.get_session() as s:
            return [self._to_domain(m) for m in s.query(PieceModel).all()]

    def search(self, query: str) -> list[Piece]:
        q = f"%{query}%"
        with self._sf.get_session() as s:
            rows = s.query(PieceModel).filter(
                PieceModel.designation.ilike(q) | PieceModel.reference_constructeur.ilike(q)
            ).all()
            return [self._to_domain(m) for m in rows]

    def find_in_alert(self) -> list[Piece]:
        with self._sf.get_session() as s:
            rows = s.query(PieceModel).filter(
                PieceModel.quantite_stock <= PieceModel.seuil_alerte
            ).all()
            return [self._to_domain(m) for m in rows]

    def find_by_fournisseur(self, fournisseur_id: uuid.UUID) -> list[Piece]:
        with self._sf.get_session() as s:
            rows = s.query(PieceModel).filter(
                PieceModel.fournisseur_id == str(fournisseur_id)
            ).all()
            return [self._to_domain(m) for m in rows]

    def save(self, p: Piece) -> None:
        with self._sf.get_session() as s:
            m = s.get(PieceModel, str(p.id))
            if m:
                m.designation = p.designation
                m.categorie = p.categorie
                m.emplacement = p.emplacement
                m.prix_achat = float(p.prix_achat)
                m.prix_vente = float(p.prix_vente)
                m.quantite_stock = p.quantite_stock
                m.seuil_alerte = p.seuil_alerte
                m.fournisseur_id = str(p.fournisseur_id) if p.fournisseur_id else None
            else:
                s.add(PieceModel(
                    id=str(p.id),
                    reference_constructeur=p.reference_constructeur,
                    designation=p.designation,
                    categorie=p.categorie,
                    emplacement=p.emplacement,
                    prix_achat=float(p.prix_achat),
                    prix_vente=float(p.prix_vente),
                    quantite_stock=p.quantite_stock,
                    seuil_alerte=p.seuil_alerte,
                    fournisseur_id=str(p.fournisseur_id) if p.fournisseur_id else None,
                ))

    def delete(self, entity_id: uuid.UUID) -> None:
        with self._sf.get_session() as s:
            m = s.get(PieceModel, str(entity_id))
            if m:
                s.delete(m)

    def add_mouvement(
        self,
        piece_id: uuid.UUID,
        type_mouvement: str,
        quantite: int,
        quantite_avant: int,
        reference: str = "",
        utilisateur_id: uuid.UUID | None = None,
        utilisateur_nom: str = "",
    ) -> None:
        with self._sf.get_session() as s:
            s.add(MouvementStockModel(
                id=str(uuid.uuid4()),
                piece_id=str(piece_id),
                type_mouvement=type_mouvement,
                quantite=quantite,
                quantite_avant=quantite_avant,
                reference=reference,
                horodatage=datetime.now(),
                utilisateur_id=str(utilisateur_id) if utilisateur_id else None,
                utilisateur_nom=utilisateur_nom,
            ))

    @staticmethod
    def _to_domain(m: PieceModel) -> Piece:
        p = Piece(id=uuid.UUID(m.id))
        p.reference_constructeur = m.reference_constructeur
        p.designation = m.designation
        p.categorie = m.categorie
        p.emplacement = getattr(m, "emplacement", "") or ""
        p.prix_achat = Decimal(str(m.prix_achat or 0))
        p.prix_vente = Decimal(str(m.prix_vente or 0))
        p.quantite_stock = m.quantite_stock
        p.seuil_alerte = m.seuil_alerte
        p.fournisseur_id = uuid.UUID(m.fournisseur_id) if m.fournisseur_id else None
        return p
