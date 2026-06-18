"""Integration tests for DossierService new methods — in-memory SQLite."""
from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from garage_app.application.dossier_service import DossierService
from garage_app.domain.atelier.ligne_diagnostic import LigneDiagnostic
from garage_app.domain.atelier.operation_mecanique import OperationMecanique
from garage_app.domain.atelier.piece_requise import PieceRequise
from garage_app.domain.atelier.statut_dossier import GravitePanne, StatutDossier, StatutTache
from garage_app.domain.shared.exceptions import PermissionDeniedError
from garage_app.infrastructure.events.in_memory_event_bus import InMemoryEventBus
from garage_app.infrastructure.repositories.dossier_repository import SqlAlchemyDossierRepository


@pytest.fixture
def dossier_repo(session_factory):
    return SqlAlchemyDossierRepository(session_factory)


@pytest.fixture
def bus():
    return InMemoryEventBus()


@pytest.fixture
def svc(session_factory, dossier_repo, bus):
    return DossierService(session_factory, dossier_repo, bus)


def _open_and_advance_to_diagnostic(svc, session):
    d = svc.ouvrir_dossier(session, uuid.uuid4(), uuid.uuid4(), 80000)
    d = svc.lancer_diagnostic(session, d.id)
    return d


def _open_and_advance_to_en_cours(svc, session):
    d = _open_and_advance_to_diagnostic(svc, session)
    ligne = LigneDiagnostic(code_defaut="P0420", description="Catalyseur", gravite=GravitePanne.BLOQUANT)
    d = svc.enregistrer_panne(session, d.id, ligne)
    d = svc.soumettre_au_devis(session, d.id)
    d = svc.approuver_devis(session, d.id, uuid.uuid4())
    return d


class TestSupprimerLigneDiagnostic:
    def test_supprimer_removes_ligne(self, svc, admin_session):
        d = _open_and_advance_to_diagnostic(svc, admin_session)
        ligne = LigneDiagnostic(code_defaut="P0100", description="Débitmètre", gravite=GravitePanne.INFO)
        d = svc.enregistrer_panne(admin_session, d.id, ligne)
        assert len(d.lignes_diagnostic) == 1
        ligne_id = d.lignes_diagnostic[0].id
        d = svc.supprimer_ligne_diagnostic(admin_session, d.id, ligne_id)
        assert len(d.lignes_diagnostic) == 0

    def test_supprimer_ligne_not_found_is_noop(self, svc, admin_session):
        d = _open_and_advance_to_diagnostic(svc, admin_session)
        ligne = LigneDiagnostic(code_defaut="P0200", description="Inj.", gravite=GravitePanne.A_SURVEILLER)
        d = svc.enregistrer_panne(admin_session, d.id, ligne)
        d2 = svc.supprimer_ligne_diagnostic(admin_session, d.id, uuid.uuid4())
        assert len(d2.lignes_diagnostic) == 1

    def test_technicien_denied_create(self, svc, tech_session):
        with pytest.raises(PermissionDeniedError):
            svc.ouvrir_dossier(tech_session, uuid.uuid4(), uuid.uuid4(), 0)


class TestAjouterOperation:
    def test_ajouter_operation_persisted(self, svc, admin_session):
        d = _open_and_advance_to_en_cours(svc, admin_session)
        op = OperationMecanique(
            description="Remplacement filtres",
            temps_estime=Decimal("1.5"),
            taux_horaire=Decimal("60"),
        )
        d = svc.ajouter_operation(admin_session, d.id, op)
        assert len(d.operations) == 1
        assert d.operations[0].description == "Remplacement filtres"

    def test_ajouter_operation_wrong_statut_raises(self, svc, admin_session):
        from garage_app.domain.shared.exceptions import BusinessRuleError
        d = _open_and_advance_to_diagnostic(svc, admin_session)
        op = OperationMecanique(description="X")
        with pytest.raises(BusinessRuleError):
            svc.ajouter_operation(admin_session, d.id, op)


class TestDemarrerTerminerOperation:
    def test_demarrer_operation(self, svc, admin_session):
        d = _open_and_advance_to_en_cours(svc, admin_session)
        op = OperationMecanique(description="Diagnostic capteur")
        d = svc.ajouter_operation(admin_session, d.id, op)
        op_id = d.operations[0].id
        d = svc.demarrer_operation(admin_session, d.id, op_id)
        assert d.operations[0].statut == StatutTache.EN_COURS

    def test_terminer_operation(self, svc, admin_session):
        d = _open_and_advance_to_en_cours(svc, admin_session)
        op = OperationMecanique(description="Remplacement plaquettes")
        d = svc.ajouter_operation(admin_session, d.id, op)
        op_id = d.operations[0].id
        svc.demarrer_operation(admin_session, d.id, op_id)
        d = svc.terminer_operation(admin_session, d.id, op_id, Decimal("2.5"))
        assert d.operations[0].statut == StatutTache.TERMINEE
        assert d.operations[0].temps_passe == Decimal("2.5")

    def test_op_not_found_raises(self, svc, admin_session):
        d = _open_and_advance_to_en_cours(svc, admin_session)
        with pytest.raises(ValueError, match="introuvable"):
            svc.demarrer_operation(admin_session, d.id, uuid.uuid4())


class TestAjouterPiece:
    def test_ajouter_piece_persisted(self, svc, admin_session):
        d = _open_and_advance_to_en_cours(svc, admin_session)
        piece = PieceRequise(
            piece_id=uuid.uuid4(),
            reference="FLT-001",
            designation="Filtre à huile",
            quantite=1,
            prix_unitaire=Decimal("12.500"),
        )
        d = svc.ajouter_piece(admin_session, d.id, piece)
        assert len(d.pieces) == 1
        assert d.pieces[0].designation == "Filtre à huile"
        assert d.montant_pieces.amount == Decimal("12.500")

    def test_supprimer_piece(self, svc, admin_session):
        d = _open_and_advance_to_en_cours(svc, admin_session)
        piece = PieceRequise(piece_id=uuid.uuid4(), designation="Bougie", quantite=4, prix_unitaire=Decimal("5"))
        d = svc.ajouter_piece(admin_session, d.id, piece)
        piece_id = d.pieces[0].id
        d = svc.supprimer_piece(admin_session, d.id, piece_id)
        assert len(d.pieces) == 0


class TestTerminerReparation:
    def test_terminer_reparation_transitions_to_qualite(self, svc, admin_session):
        d = _open_and_advance_to_en_cours(svc, admin_session)
        op = OperationMecanique(description="Test")
        d = svc.ajouter_operation(admin_session, d.id, op)
        op_id = d.operations[0].id
        svc.demarrer_operation(admin_session, d.id, op_id)
        d = svc.terminer_operation(admin_session, d.id, op_id, Decimal("1"))
        d = svc.terminer_reparation(admin_session, d.id)
        assert d.statut == StatutDossier.QUALITE

    def test_terminer_reparation_with_incomplete_ops_raises(self, svc, admin_session):
        from garage_app.domain.shared.exceptions import InvariantViolationError
        d = _open_and_advance_to_en_cours(svc, admin_session)
        op = OperationMecanique(description="Incomplete", statut=StatutTache.EN_COURS)
        svc.ajouter_operation(admin_session, d.id, op)
        with pytest.raises(InvariantViolationError):
            svc.terminer_reparation(admin_session, d.id)

    def test_full_lifecycle(self, svc, admin_session):
        d = _open_and_advance_to_en_cours(svc, admin_session)
        op = OperationMecanique(description="Vidange", statut=StatutTache.TERMINEE, temps_passe=Decimal("1"))
        d = svc.ajouter_operation(admin_session, d.id, op)
        d = svc.terminer_reparation(admin_session, d.id)
        assert d.statut == StatutDossier.QUALITE
        d = svc.valider_qualite(admin_session, d.id)
        assert d.statut == StatutDossier.PRET
