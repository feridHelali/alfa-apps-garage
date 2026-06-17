from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from garage_app.domain.stock.piece import Piece
from garage_app.domain.stock.repositories import PieceRepository
from garage_app.infrastructure.db.models.piece_model import PieceModel


class SqlAlchemyPieceRepository(PieceRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def get_by_id(self, entity_id: uuid.UUID) -> Piece | None:
        m = self._s.get(PieceModel, str(entity_id))
        return self._to_domain(m) if m else None

    def find_all(self) -> list[Piece]:
        return [self._to_domain(m) for m in self._s.query(PieceModel).all()]

    def search(self, query: str) -> list[Piece]:
        q = f"%{query}%"
        rows = self._s.query(PieceModel).filter(
            PieceModel.designation.ilike(q) | PieceModel.reference_constructeur.ilike(q)
        ).all()
        return [self._to_domain(m) for m in rows]

    def find_in_alert(self) -> list[Piece]:
        rows = self._s.query(PieceModel).filter(
            PieceModel.quantite_stock <= PieceModel.seuil_alerte
        ).all()
        return [self._to_domain(m) for m in rows]

    def save(self, p: Piece) -> None:
        m = self._s.get(PieceModel, str(p.id))
        if m:
            m.designation = p.designation
            m.categorie = p.categorie
            m.prix_achat = float(p.prix_achat)
            m.prix_vente = float(p.prix_vente)
            m.quantite_stock = p.quantite_stock
            m.seuil_alerte = p.seuil_alerte
        else:
            self._s.add(PieceModel(
                id=str(p.id),
                reference_constructeur=p.reference_constructeur,
                designation=p.designation,
                categorie=p.categorie,
                prix_achat=float(p.prix_achat),
                prix_vente=float(p.prix_vente),
                quantite_stock=p.quantite_stock,
                seuil_alerte=p.seuil_alerte,
                fournisseur_id=str(p.fournisseur_id) if p.fournisseur_id else None,
            ))

    def delete(self, entity_id: uuid.UUID) -> None:
        m = self._s.get(PieceModel, str(entity_id))
        if m:
            self._s.delete(m)

    @staticmethod
    def _to_domain(m: PieceModel) -> Piece:
        p = Piece(id=uuid.UUID(m.id))
        p.reference_constructeur = m.reference_constructeur
        p.designation = m.designation
        p.categorie = m.categorie
        p.prix_achat = Decimal(str(m.prix_achat))
        p.prix_vente = Decimal(str(m.prix_vente))
        p.quantite_stock = m.quantite_stock
        p.seuil_alerte = m.seuil_alerte
        p.fournisseur_id = uuid.UUID(m.fournisseur_id) if m.fournisseur_id else None
        return p
