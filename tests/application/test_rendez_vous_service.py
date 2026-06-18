"""Integration tests for RendezVousService — uses in-memory SQLite."""
from __future__ import annotations

import uuid
from datetime import datetime, date

import pytest

from garage_app.application.rendez_vous_service import RendezVousService
from garage_app.domain.shared.exceptions import PermissionDeniedError
from garage_app.infrastructure.events.in_memory_event_bus import InMemoryEventBus
from garage_app.infrastructure.repositories.rendez_vous_repository import SqlAlchemyRendezVousRepository


@pytest.fixture
def rdv_repo(session_factory):
    return SqlAlchemyRendezVousRepository(session_factory)


@pytest.fixture
def bus():
    return InMemoryEventBus()


@pytest.fixture
def svc(rdv_repo, bus):
    return RendezVousService(rdv_repo, bus)


def _new_ids():
    return uuid.uuid4(), uuid.uuid4()  # client_id, vehicule_id


class TestPlanifier:
    def test_planifier_creates_rdv(self, svc, admin_session):
        cid, vid = _new_ids()
        rdv = svc.planifier(admin_session, cid, vid, datetime(2026, 9, 1, 9, 0), "Révision")
        assert rdv.id is not None
        assert rdv.statut == "planifie"
        assert rdv.motif == "Révision"

    def test_planifier_technicien_denied(self, svc, tech_session):
        cid, vid = _new_ids()
        with pytest.raises(PermissionDeniedError):
            svc.planifier(tech_session, cid, vid, datetime.now(), "")

    def test_planifier_persisted(self, svc, rdv_repo, admin_session):
        cid, vid = _new_ids()
        rdv = svc.planifier(admin_session, cid, vid, datetime(2026, 9, 5, 14, 0), "CT")
        reloaded = rdv_repo.get_by_id(rdv.id)
        assert reloaded is not None
        assert reloaded.motif == "CT"


class TestStatusTransitions:
    def test_confirmer(self, svc, admin_session):
        cid, vid = _new_ids()
        rdv = svc.planifier(admin_session, cid, vid, datetime.now(), "")
        confirmed = svc.confirmer(admin_session, rdv.id)
        assert confirmed.statut == "confirme"

    def test_terminer(self, svc, admin_session):
        cid, vid = _new_ids()
        rdv = svc.planifier(admin_session, cid, vid, datetime.now(), "")
        svc.confirmer(admin_session, rdv.id)
        finished = svc.terminer(admin_session, rdv.id)
        assert finished.statut == "termine"

    def test_annuler_planifie(self, svc, admin_session):
        cid, vid = _new_ids()
        rdv = svc.planifier(admin_session, cid, vid, datetime.now(), "")
        cancelled = svc.annuler(admin_session, rdv.id)
        assert cancelled.statut == "annule"

    def test_modifier_updates_fields(self, svc, admin_session):
        cid, vid = _new_ids()
        new_vid = uuid.uuid4()
        rdv = svc.planifier(admin_session, cid, vid, datetime(2026, 9, 1, 9, 0), "Original")
        updated = svc.modifier(
            admin_session, rdv.id, cid, new_vid, datetime(2026, 9, 15, 10, 0), "Modifié"
        )
        assert updated.motif == "Modifié"
        assert updated.vehicule_id == new_vid

    def test_modifier_annule_raises(self, svc, admin_session):
        cid, vid = _new_ids()
        rdv = svc.planifier(admin_session, cid, vid, datetime.now(), "")
        svc.annuler(admin_session, rdv.id)
        with pytest.raises(ValueError, match="annulé"):
            svc.modifier(admin_session, rdv.id, cid, vid, datetime.now(), "")

    def test_not_found_raises(self, svc, admin_session):
        with pytest.raises(ValueError, match="introuvable"):
            svc.confirmer(admin_session, uuid.uuid4())


class TestListMethods:
    def test_list_all(self, svc, admin_session):
        cid, vid = _new_ids()
        svc.planifier(admin_session, cid, vid, datetime.now(), "A")
        svc.planifier(admin_session, cid, vid, datetime.now(), "B")
        results = svc.list_all(admin_session)
        assert len(results) >= 2

    def test_list_by_date(self, svc, admin_session):
        cid, vid = _new_ids()
        target = datetime(2026, 10, 1, 11, 0)
        rdv = svc.planifier(admin_session, cid, vid, target, "On target")
        other = svc.planifier(admin_session, cid, vid, datetime(2026, 11, 5, 9, 0), "Other")
        results = svc.list_by_date(admin_session, date(2026, 10, 1))
        ids = [r.id for r in results]
        assert rdv.id in ids
        assert other.id not in ids

    def test_list_upcoming_excludes_annule(self, svc, admin_session):
        cid, vid = _new_ids()
        future = datetime(2030, 1, 1, 9, 0)
        rdv = svc.planifier(admin_session, cid, vid, future, "Future")
        svc.annuler(admin_session, rdv.id)
        upcoming = svc.list_upcoming(admin_session)
        assert all(r.statut in ("planifie", "confirme") for r in upcoming)

    def test_planifier_by_technicien_denied(self, svc, tech_session):
        with pytest.raises(PermissionDeniedError):
            svc.planifier(tech_session, uuid.uuid4(), uuid.uuid4(), datetime.now(), "")

    def test_supprimer(self, svc, rdv_repo, admin_session):
        cid, vid = _new_ids()
        rdv = svc.planifier(admin_session, cid, vid, datetime.now(), "")
        svc.supprimer(admin_session, rdv.id)
        assert rdv_repo.get_by_id(rdv.id) is None
