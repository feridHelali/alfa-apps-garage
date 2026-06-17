from __future__ import annotations

import uuid
from decimal import Decimal

from garage_app.application.decorators import require_permission
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.atelier.dossier_reparation import DossierReparation
from garage_app.domain.atelier.ligne_diagnostic import LigneDiagnostic
from garage_app.domain.atelier.operation_mecanique import OperationMecanique
from garage_app.domain.atelier.piece_requise import PieceRequise
from garage_app.domain.atelier.repositories import DossierReparationRepository
from garage_app.domain.atelier.statut_dossier import StatutDossier
from garage_app.infrastructure.db.session import SessionFactory
from garage_app.infrastructure.events.in_memory_event_bus import InMemoryEventBus


class DossierService:
    def __init__(
        self,
        sf: SessionFactory,
        repo: DossierReparationRepository,
        bus: InMemoryEventBus,
    ) -> None:
        self._sf = sf
        self._repo = repo
        self._bus = bus

    @require_permission(Permission.CREATE_DOSSIER)
    def ouvrir_dossier(
        self,
        session: UserSession,
        vehicule_id: uuid.UUID,
        client_id: uuid.UUID,
        kilometrage: int,
    ) -> DossierReparation:
        dossier = DossierReparation(
            vehicule_id=vehicule_id, client_id=client_id, kilometrage_entree=kilometrage
        )
        with self._sf.get_session():
            self._repo.save(dossier)
        self._bus.publish_all(dossier.pull_events())
        return dossier

    @require_permission(Permission.MANAGE_DOSSIER)
    def lancer_diagnostic(self, session: UserSession, dossier_id: uuid.UUID) -> DossierReparation:
        with self._sf.get_session() as s:
            dossier = self._repo.get_by_id(dossier_id)
            if not dossier:
                raise ValueError(f"Dossier {dossier_id} introuvable.")
            dossier.lancer_diagnostic()
            self._repo.save(dossier)
        self._bus.publish_all(dossier.pull_events())
        return dossier

    @require_permission(Permission.MANAGE_DOSSIER)
    def enregistrer_panne(
        self, session: UserSession, dossier_id: uuid.UUID, ligne: LigneDiagnostic
    ) -> DossierReparation:
        with self._sf.get_session():
            dossier = self._repo.get_by_id(dossier_id)
            if not dossier:
                raise ValueError(f"Dossier {dossier_id} introuvable.")
            dossier.enregistrer_panne(ligne)
            self._repo.save(dossier)
        self._bus.publish_all(dossier.pull_events())
        return dossier

    @require_permission(Permission.MANAGE_DOSSIER)
    def soumettre_au_devis(self, session: UserSession, dossier_id: uuid.UUID) -> DossierReparation:
        with self._sf.get_session():
            dossier = self._repo.get_by_id(dossier_id)
            if not dossier:
                raise ValueError(f"Dossier {dossier_id} introuvable.")
            dossier.soumettre_au_devis()
            self._repo.save(dossier)
        self._bus.publish_all(dossier.pull_events())
        return dossier

    @require_permission(Permission.APPROVE_DEVIS)
    def approuver_devis(
        self, session: UserSession, dossier_id: uuid.UUID, devis_id: uuid.UUID
    ) -> DossierReparation:
        with self._sf.get_session():
            dossier = self._repo.get_by_id(dossier_id)
            if not dossier:
                raise ValueError(f"Dossier {dossier_id} introuvable.")
            dossier.approuver_devis(devis_id)
            self._repo.save(dossier)
        self._bus.publish_all(dossier.pull_events())
        return dossier

    @require_permission(Permission.VALIDATE_QUALITY)
    def valider_qualite(self, session: UserSession, dossier_id: uuid.UUID) -> DossierReparation:
        with self._sf.get_session():
            dossier = self._repo.get_by_id(dossier_id)
            if not dossier:
                raise ValueError(f"Dossier {dossier_id} introuvable.")
            dossier.valider_controle_qualite()
            self._repo.save(dossier)
        self._bus.publish_all(dossier.pull_events())
        return dossier

    @require_permission(Permission.VIEW_DOSSIERS)
    def list_open(self, session: UserSession) -> list[DossierReparation]:
        with self._sf.get_session():
            return self._repo.find_open()
