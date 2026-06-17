from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from garage_app.domain.facturation.caisse import MouvementCaisse, SessionCaisse
from garage_app.domain.facturation.repositories import CaisseRepository
from garage_app.infrastructure.db.models.facture_model import MouvementCaisseModel, SessionCaisseModel


class SqlAlchemyCaisseRepository(CaisseRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def get_by_id(self, entity_id: uuid.UUID) -> SessionCaisse | None:
        m = self._s.get(SessionCaisseModel, str(entity_id))
        return self._to_domain(m) if m else None

    def find_all(self) -> list[SessionCaisse]:
        rows = self._s.query(SessionCaisseModel).order_by(SessionCaisseModel.ouvert_le.desc()).all()
        return [self._to_domain(m) for m in rows]

    def find_session_active(self) -> SessionCaisse | None:
        m = self._s.query(SessionCaisseModel).filter_by(statut="ouverte").first()
        return self._to_domain(m) if m else None

    def find_by_date(self, jour: date) -> list[SessionCaisse]:
        rows = (
            self._s.query(SessionCaisseModel)
            .filter(SessionCaisseModel.ouvert_le >= datetime.combine(jour, datetime.min.time()))
            .filter(SessionCaisseModel.ouvert_le < datetime.combine(jour, datetime.max.time()))
            .all()
        )
        return [self._to_domain(m) for m in rows]

    def save(self, sc: SessionCaisse) -> None:
        m = self._s.get(SessionCaisseModel, str(sc.id))
        if m:
            m.statut = sc.statut
            m.ferme_le = sc.ferme_le
            m.solde_fermeture_reel = float(sc.solde_fermeture_reel) if sc.solde_fermeture_reel is not None else None
            # sync new mouvements only
            existing_ids = {mv.id for mv in m.mouvements}
            for mv in sc.mouvements:
                if str(mv.id) not in existing_ids:
                    m.mouvements.append(MouvementCaisseModel(
                        id=str(mv.id),
                        session_id=str(sc.id),
                        type=mv.type,
                        montant=float(mv.montant),
                        motif=mv.motif,
                        reference=mv.reference,
                        horodatage=mv.horodatage,
                        currency=mv.currency,
                    ))
        else:
            new_m = SessionCaisseModel(
                id=str(sc.id),
                ouvert_par=str(sc.ouvert_par),
                solde_ouverture=float(sc.solde_ouverture),
                currency=sc.currency,
                statut=sc.statut,
                ouvert_le=sc.ouvert_le,
            )
            self._s.add(new_m)
            self._s.flush()
            for mv in sc.mouvements:
                self._s.add(MouvementCaisseModel(
                    id=str(mv.id),
                    session_id=str(sc.id),
                    type=mv.type,
                    montant=float(mv.montant),
                    motif=mv.motif,
                    reference=mv.reference,
                    horodatage=mv.horodatage,
                    currency=mv.currency,
                ))

    def delete(self, entity_id: uuid.UUID) -> None:
        m = self._s.get(SessionCaisseModel, str(entity_id))
        if m:
            self._s.delete(m)

    @staticmethod
    def _to_domain(m: SessionCaisseModel) -> SessionCaisse:
        sc = SessionCaisse(id=uuid.UUID(m.id))
        sc.ouvert_par = uuid.UUID(m.ouvert_par)
        sc.solde_ouverture = Decimal(str(m.solde_ouverture or 0))
        sc.currency = m.currency or "TND"
        sc.statut = m.statut
        sc.ouvert_le = m.ouvert_le if isinstance(m.ouvert_le, datetime) else datetime.now(timezone.utc)
        sc.ferme_le = m.ferme_le
        sc.solde_fermeture_reel = Decimal(str(m.solde_fermeture_reel)) if m.solde_fermeture_reel is not None else None
        sc.mouvements = []
        for mv in (m.mouvements or []):
            mouv = MouvementCaisse(id=mv.id)
            mouv.type = mv.type
            mouv.montant = Decimal(str(mv.montant))
            mouv.motif = mv.motif or ""
            mouv.reference = mv.reference or ""
            mouv.horodatage = mv.horodatage if isinstance(mv.horodatage, datetime) else datetime.now(timezone.utc)
            mouv.currency = mv.currency or "TND"
            sc.mouvements.append(mouv)
        return sc
