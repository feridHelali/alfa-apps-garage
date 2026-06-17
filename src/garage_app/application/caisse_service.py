from __future__ import annotations

from decimal import Decimal

from garage_app.application.audit_service import AuditService
from garage_app.application.decorators import require_permission
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.facturation.caisse import SessionCaisse
from garage_app.domain.facturation.repositories import CaisseRepository
from garage_app.infrastructure.db.session import SessionFactory
from garage_app.infrastructure.events.in_memory_event_bus import InMemoryEventBus


class CaisseService:
    def __init__(
        self,
        sf: SessionFactory,
        repo: CaisseRepository,
        bus: InMemoryEventBus,
        audit: AuditService | None = None,
    ) -> None:
        self._sf = sf
        self._repo = repo
        self._bus = bus
        self._audit = audit

    @require_permission(Permission.VIEW_FACTURES)
    def get_session_active(self, session: UserSession) -> SessionCaisse | None:
        with self._sf.get_session():
            return self._repo.find_session_active()

    @require_permission(Permission.MANAGE_CAISSE)
    def ouvrir_session(
        self,
        session: UserSession,
        solde_ouverture: Decimal = Decimal("0"),
    ) -> SessionCaisse:
        with self._sf.get_session():
            active = self._repo.find_session_active()
            if active:
                raise ValueError("Une session de caisse est déjà ouverte.")
            sc = SessionCaisse(
                ouvert_par=session.user_id,
                solde_ouverture=solde_ouverture,
            )
            self._repo.save(sc)
        if self._audit:
            self._audit.log_business(
                f"Session caisse ouverte par {session.full_name} "
                f"(solde ouverture: {solde_ouverture} TND)",
                user_id=session.user_id,
                username=session.username,
            )
        return sc

    @require_permission(Permission.MANAGE_CAISSE)
    def encaisser(
        self,
        session: UserSession,
        montant: Decimal,
        motif: str,
        reference: str = "",
    ) -> SessionCaisse:
        with self._sf.get_session():
            sc = self._repo.find_session_active()
            if not sc:
                raise ValueError("Aucune session de caisse ouverte.")
            sc.encaisser(montant, motif, reference)
            self._repo.save(sc)
        return sc

    @require_permission(Permission.MANAGE_CAISSE)
    def decaisser(
        self,
        session: UserSession,
        montant: Decimal,
        motif: str,
    ) -> SessionCaisse:
        with self._sf.get_session():
            sc = self._repo.find_session_active()
            if not sc:
                raise ValueError("Aucune session de caisse ouverte.")
            sc.decaisser(montant, motif)
            self._repo.save(sc)
        return sc

    @require_permission(Permission.MANAGE_CAISSE)
    def fermer_session(
        self,
        session: UserSession,
        solde_reel: Decimal,
    ) -> tuple[SessionCaisse, Decimal]:
        with self._sf.get_session():
            sc = self._repo.find_session_active()
            if not sc:
                raise ValueError("Aucune session de caisse ouverte.")
            ecart = sc.fermer(solde_reel)
            self._repo.save(sc)
        if self._audit:
            level = "WARNING" if abs(ecart) > Decimal("0.001") else "INFO"
            self._audit.log_business(
                f"Session caisse fermée par {session.full_name}. "
                f"Théorique: {sc.solde_theorique:.3f} TND, "
                f"Réel: {solde_reel:.3f} TND, Écart: {ecart:.3f} TND.",
                user_id=session.user_id,
                username=session.username,
            )
        return sc, ecart

    @require_permission(Permission.MANAGE_CAISSE)
    def list_sessions(self, session: UserSession) -> list[SessionCaisse]:
        with self._sf.get_session():
            return self._repo.find_all()
