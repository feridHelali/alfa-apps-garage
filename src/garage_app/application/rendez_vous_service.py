from __future__ import annotations

import uuid
from datetime import date, datetime

from garage_app.application.decorators import require_permission
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.planification.rendez_vous import RendezVous
from garage_app.domain.planification.repositories import RendezVousRepository
from garage_app.infrastructure.events.in_memory_event_bus import InMemoryEventBus


class RendezVousService:
    def __init__(self, repo: RendezVousRepository, bus: InMemoryEventBus) -> None:
        self._repo = repo
        self._bus = bus

    @require_permission(Permission.MANAGE_RENDEZ_VOUS)
    def planifier(
        self,
        session: UserSession,
        client_id: uuid.UUID,
        vehicule_id: uuid.UUID,
        date_heure: datetime,
        motif: str = "",
    ) -> RendezVous:
        rdv = RendezVous(
            client_id=client_id,
            vehicule_id=vehicule_id,
            date_heure=date_heure,
            motif=motif,
        )
        self._repo.save(rdv)
        self._bus.publish_all(rdv.pull_events())
        return rdv

    @require_permission(Permission.MANAGE_RENDEZ_VOUS)
    def modifier(
        self,
        session: UserSession,
        rdv_id: uuid.UUID,
        client_id: uuid.UUID,
        vehicule_id: uuid.UUID,
        date_heure: datetime,
        motif: str,
    ) -> RendezVous:
        rdv = self._repo.get_by_id(rdv_id)
        if not rdv:
            raise ValueError(f"Rendez-vous {rdv_id} introuvable.")
        if rdv.statut in ("annule", "termine"):
            raise ValueError("Impossible de modifier un rendez-vous annulé ou terminé.")
        rdv.client_id = client_id
        rdv.vehicule_id = vehicule_id
        rdv.date_heure = date_heure
        rdv.motif = motif
        self._repo.save(rdv)
        return rdv

    @require_permission(Permission.MANAGE_RENDEZ_VOUS)
    def confirmer(self, session: UserSession, rdv_id: uuid.UUID) -> RendezVous:
        rdv = self._repo.get_by_id(rdv_id)
        if not rdv:
            raise ValueError(f"Rendez-vous {rdv_id} introuvable.")
        rdv.confirmer()
        self._repo.save(rdv)
        return rdv

    @require_permission(Permission.MANAGE_RENDEZ_VOUS)
    def terminer(self, session: UserSession, rdv_id: uuid.UUID) -> RendezVous:
        rdv = self._repo.get_by_id(rdv_id)
        if not rdv:
            raise ValueError(f"Rendez-vous {rdv_id} introuvable.")
        rdv.terminer()
        self._repo.save(rdv)
        return rdv

    @require_permission(Permission.MANAGE_RENDEZ_VOUS)
    def annuler(self, session: UserSession, rdv_id: uuid.UUID) -> RendezVous:
        rdv = self._repo.get_by_id(rdv_id)
        if not rdv:
            raise ValueError(f"Rendez-vous {rdv_id} introuvable.")
        rdv.annuler()
        self._repo.save(rdv)
        return rdv

    @require_permission(Permission.MANAGE_RENDEZ_VOUS)
    def supprimer(self, session: UserSession, rdv_id: uuid.UUID) -> None:
        self._repo.delete(rdv_id)

    @require_permission(Permission.VIEW_RENDEZ_VOUS)
    def list_all(self, session: UserSession) -> list[RendezVous]:
        return self._repo.find_all()

    @require_permission(Permission.VIEW_RENDEZ_VOUS)
    def list_upcoming(self, session: UserSession) -> list[RendezVous]:
        return self._repo.find_upcoming()

    @require_permission(Permission.VIEW_RENDEZ_VOUS)
    def list_by_date(self, session: UserSession, target: date) -> list[RendezVous]:
        return self._repo.find_by_date(target)

    @require_permission(Permission.VIEW_RENDEZ_VOUS)
    def list_by_month(self, session: UserSession, year: int, month: int) -> list[RendezVous]:
        return self._repo.find_by_month(year, month)
