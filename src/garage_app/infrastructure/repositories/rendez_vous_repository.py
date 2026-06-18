from __future__ import annotations

import uuid
from calendar import monthrange
from datetime import date, datetime

from sqlalchemy import and_

from garage_app.domain.planification.rendez_vous import RendezVous
from garage_app.domain.planification.repositories import RendezVousRepository
from garage_app.infrastructure.db.models.rendez_vous_model import RendezVousModel
from garage_app.infrastructure.db.session import SessionFactory


class SqlAlchemyRendezVousRepository(RendezVousRepository):
    def __init__(self, sf: SessionFactory) -> None:
        self._sf = sf

    def get_by_id(self, entity_id: uuid.UUID) -> RendezVous | None:
        with self._sf.get_session() as s:
            m = s.get(RendezVousModel, str(entity_id))
            return self._to_domain(m) if m else None

    def find_all(self) -> list[RendezVous]:
        with self._sf.get_session() as s:
            rows = s.query(RendezVousModel).order_by(RendezVousModel.date_heure).all()
            return [self._to_domain(m) for m in rows]

    def find_upcoming(self) -> list[RendezVous]:
        now = datetime.now()
        with self._sf.get_session() as s:
            rows = s.query(RendezVousModel).filter(
                RendezVousModel.date_heure >= now,
                RendezVousModel.statut.in_(["planifie", "confirme"]),
            ).order_by(RendezVousModel.date_heure).all()
            return [self._to_domain(m) for m in rows]

    def find_by_date(self, target: date) -> list[RendezVous]:
        start = datetime(target.year, target.month, target.day, 0, 0, 0)
        end = datetime(target.year, target.month, target.day, 23, 59, 59)
        with self._sf.get_session() as s:
            rows = s.query(RendezVousModel).filter(
                and_(RendezVousModel.date_heure >= start, RendezVousModel.date_heure <= end)
            ).order_by(RendezVousModel.date_heure).all()
            return [self._to_domain(m) for m in rows]

    def find_by_month(self, year: int, month: int) -> list[RendezVous]:
        _, last_day = monthrange(year, month)
        start = datetime(year, month, 1)
        end = datetime(year, month, last_day, 23, 59, 59)
        with self._sf.get_session() as s:
            rows = s.query(RendezVousModel).filter(
                and_(RendezVousModel.date_heure >= start, RendezVousModel.date_heure <= end)
            ).order_by(RendezVousModel.date_heure).all()
            return [self._to_domain(m) for m in rows]

    def save(self, rdv: RendezVous) -> None:
        with self._sf.get_session() as s:
            m = s.get(RendezVousModel, str(rdv.id))
            if m:
                m.client_id = str(rdv.client_id)
                m.vehicule_id = str(rdv.vehicule_id)
                m.date_heure = rdv.date_heure
                m.motif = rdv.motif
                m.statut = rdv.statut
            else:
                s.add(RendezVousModel(
                    id=str(rdv.id),
                    client_id=str(rdv.client_id),
                    vehicule_id=str(rdv.vehicule_id),
                    date_heure=rdv.date_heure,
                    motif=rdv.motif,
                    statut=rdv.statut,
                ))

    def delete(self, entity_id: uuid.UUID) -> None:
        with self._sf.get_session() as s:
            m = s.get(RendezVousModel, str(entity_id))
            if m:
                s.delete(m)

    @staticmethod
    def _to_domain(m: RendezVousModel) -> RendezVous:
        rdv = RendezVous(
            id=uuid.UUID(m.id),
            client_id=uuid.UUID(m.client_id),
            vehicule_id=uuid.UUID(m.vehicule_id),
            date_heure=m.date_heure,
            motif=m.motif,
            statut=m.statut,
        )
        rdv.pull_events()  # discard spurious RendezVousPlanifie raised by __post_init__
        return rdv
