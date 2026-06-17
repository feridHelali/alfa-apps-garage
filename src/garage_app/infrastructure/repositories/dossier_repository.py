from __future__ import annotations

import uuid
from decimal import Decimal

from garage_app.domain.atelier.dossier_reparation import DossierReparation
from garage_app.domain.atelier.ligne_diagnostic import LigneDiagnostic
from garage_app.domain.atelier.operation_mecanique import OperationMecanique
from garage_app.domain.atelier.piece_requise import PieceRequise
from garage_app.domain.atelier.statut_dossier import StatutDossier, StatutTache, StatutDispo, GravitePanne
from garage_app.domain.atelier.repositories import DossierReparationRepository
from garage_app.infrastructure.db.models.dossier_model import (
    DossierReparationModel, LigneDiagnosticModel, OperationMecaniqueModel, PieceRequiseModel,
)
from garage_app.infrastructure.db.session import SessionFactory


class SqlAlchemyDossierRepository(DossierReparationRepository):
    def __init__(self, sf: SessionFactory) -> None:
        self._sf = sf

    def get_by_id(self, entity_id: uuid.UUID) -> DossierReparation | None:
        with self._sf.get_session() as s:
            m = s.get(DossierReparationModel, str(entity_id))
            return self._to_domain(m) if m else None

    def find_all(self) -> list[DossierReparation]:
        with self._sf.get_session() as s:
            return [self._to_domain(m) for m in s.query(DossierReparationModel).all()]

    def find_by_vehicule(self, vehicule_id: uuid.UUID) -> list[DossierReparation]:
        with self._sf.get_session() as s:
            rows = s.query(DossierReparationModel).filter_by(vehicule_id=str(vehicule_id)).all()
            return [self._to_domain(m) for m in rows]

    def find_by_statut(self, statut: StatutDossier) -> list[DossierReparation]:
        with self._sf.get_session() as s:
            rows = s.query(DossierReparationModel).filter_by(statut=statut.value).all()
            return [self._to_domain(m) for m in rows]

    def find_open(self) -> list[DossierReparation]:
        with self._sf.get_session() as s:
            rows = s.query(DossierReparationModel).filter(
                DossierReparationModel.statut != StatutDossier.CLOTURE.value
            ).all()
            return [self._to_domain(m) for m in rows]

    def save(self, d: DossierReparation) -> None:
        with self._sf.get_session() as s:
            m = s.get(DossierReparationModel, str(d.id))
            if not m:
                m = DossierReparationModel(
                    id=str(d.id),
                    vehicule_id=str(d.vehicule_id),
                    client_id=str(d.client_id),
                    kilometrage_entree=d.kilometrage_entree,
                )
                s.add(m)
            m.statut = d.statut.value
            m.devis_id = str(d.devis_id) if d.devis_id else None
            m.facture_id = str(d.facture_id) if d.facture_id else None
            m.notes = d.notes
            m.lignes_diagnostic.clear()
            for l in d.lignes_diagnostic:
                m.lignes_diagnostic.append(LigneDiagnosticModel(
                    id=str(l.id), dossier_id=str(d.id),
                    code_defaut=l.code_defaut, description=l.description, gravite=l.gravite.value,
                ))
            m.operations.clear()
            for op in d.operations:
                m.operations.append(OperationMecaniqueModel(
                    id=str(op.id), dossier_id=str(d.id),
                    technicien_id=str(op.technicien_id) if op.technicien_id else None,
                    code_main_oeuvre=op.code_main_oeuvre, description=op.description,
                    temps_estime=float(op.temps_estime), temps_passe=float(op.temps_passe),
                    taux_horaire=float(op.taux_horaire), statut=op.statut.value,
                ))
            m.pieces.clear()
            for p in d.pieces:
                m.pieces.append(PieceRequiseModel(
                    id=str(p.id), dossier_id=str(d.id), piece_id=str(p.piece_id),
                    reference=p.reference, designation=p.designation,
                    quantite=p.quantite, prix_unitaire=float(p.prix_unitaire),
                    statut_dispo=p.statut_dispo.value,
                ))

    def delete(self, entity_id: uuid.UUID) -> None:
        with self._sf.get_session() as s:
            m = s.get(DossierReparationModel, str(entity_id))
            if m:
                s.delete(m)

    @staticmethod
    def _to_domain(m: DossierReparationModel) -> DossierReparation:
        d = DossierReparation(
            id=uuid.UUID(m.id),
            vehicule_id=uuid.UUID(m.vehicule_id),
            client_id=uuid.UUID(m.client_id),
            kilometrage_entree=m.kilometrage_entree,
            statut=StatutDossier(m.statut),
            notes=m.notes,
        )
        d.devis_id = uuid.UUID(m.devis_id) if m.devis_id else None
        d.facture_id = uuid.UUID(m.facture_id) if m.facture_id else None
        for l in m.lignes_diagnostic:
            ld = LigneDiagnostic(id=uuid.UUID(l.id))
            ld.code_defaut = l.code_defaut
            ld.description = l.description
            ld.gravite = GravitePanne(l.gravite)
            d.lignes_diagnostic.append(ld)
        for op in m.operations:
            o = OperationMecanique(id=uuid.UUID(op.id))
            o.technicien_id = uuid.UUID(op.technicien_id) if op.technicien_id else None
            o.code_main_oeuvre = op.code_main_oeuvre
            o.description = op.description
            o.temps_estime = Decimal(str(op.temps_estime))
            o.temps_passe = Decimal(str(op.temps_passe))
            o.taux_horaire = Decimal(str(op.taux_horaire))
            o.statut = StatutTache(op.statut)
            d.operations.append(o)
        for p in m.pieces:
            pr = PieceRequise(id=uuid.UUID(p.id))
            pr.piece_id = uuid.UUID(p.piece_id)
            pr.reference = p.reference
            pr.designation = p.designation
            pr.quantite = p.quantite
            pr.prix_unitaire = Decimal(str(p.prix_unitaire))
            pr.statut_dispo = StatutDispo(p.statut_dispo)
            d.pieces.append(pr)
        return d
