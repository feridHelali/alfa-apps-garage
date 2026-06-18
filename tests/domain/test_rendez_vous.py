"""Unit tests for RendezVous domain aggregate — pure Python, no DB."""
from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from garage_app.domain.planification.rendez_vous import RendezVous
from garage_app.domain.planification.events import RendezVousPlanifie


def make_rdv(statut: str = "planifie") -> RendezVous:
    rdv = RendezVous(
        client_id=uuid.uuid4(),
        vehicule_id=uuid.uuid4(),
        date_heure=datetime(2026, 7, 15, 9, 0),
        motif="Vidange",
        statut=statut,
    )
    rdv.pull_events()  # discard creation event
    return rdv


class TestRendezVousCreation:
    def test_initial_statut_is_planifie(self):
        rdv = RendezVous(
            client_id=uuid.uuid4(),
            vehicule_id=uuid.uuid4(),
            date_heure=datetime.now(),
        )
        assert rdv.statut == "planifie"

    def test_creation_raises_planifie_event(self):
        rdv = RendezVous(
            client_id=uuid.uuid4(),
            vehicule_id=uuid.uuid4(),
            date_heure=datetime.now(),
            motif="Révision",
        )
        events = rdv.pull_events()
        assert len(events) == 1
        assert isinstance(events[0], RendezVousPlanifie)

    def test_creation_event_carries_correct_ids(self):
        client_id = uuid.uuid4()
        rdv = RendezVous(
            client_id=client_id,
            vehicule_id=uuid.uuid4(),
            date_heure=datetime.now(),
        )
        event = rdv.pull_events()[0]
        assert isinstance(event, RendezVousPlanifie)
        assert event.client_id == client_id
        assert event.rendez_vous_id == rdv.id

    def test_has_unique_id(self):
        rdv1 = RendezVous(client_id=uuid.uuid4(), vehicule_id=uuid.uuid4(), date_heure=datetime.now())
        rdv2 = RendezVous(client_id=uuid.uuid4(), vehicule_id=uuid.uuid4(), date_heure=datetime.now())
        assert rdv1.id != rdv2.id


class TestRendezVousTransitions:
    def test_confirmer(self):
        rdv = make_rdv("planifie")
        rdv.confirmer()
        assert rdv.statut == "confirme"

    def test_annuler_planifie(self):
        rdv = make_rdv("planifie")
        rdv.annuler()
        assert rdv.statut == "annule"

    def test_annuler_confirme(self):
        rdv = make_rdv("confirme")
        rdv.annuler()
        assert rdv.statut == "annule"

    def test_terminer(self):
        rdv = make_rdv("confirme")
        rdv.terminer()
        assert rdv.statut == "termine"

    def test_fields_preserved_after_confirm(self):
        date = datetime(2026, 8, 1, 10, 30)
        rdv = RendezVous(
            client_id=uuid.uuid4(),
            vehicule_id=uuid.uuid4(),
            date_heure=date,
            motif="CT",
        )
        rdv.pull_events()
        rdv.confirmer()
        assert rdv.motif == "CT"
        assert rdv.date_heure == date

    def test_pull_events_clears_list(self):
        rdv = RendezVous(client_id=uuid.uuid4(), vehicule_id=uuid.uuid4(), date_heure=datetime.now())
        first = rdv.pull_events()
        second = rdv.pull_events()
        assert len(first) == 1
        assert len(second) == 0
