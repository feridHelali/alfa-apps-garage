"""Unit tests for DossierReparation state machine — pure domain, no DB."""
from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from garage_app.domain.atelier.dossier_reparation import DossierReparation
from garage_app.domain.atelier.ligne_diagnostic import LigneDiagnostic
from garage_app.domain.atelier.operation_mecanique import OperationMecanique
from garage_app.domain.atelier.piece_requise import PieceRequise
from garage_app.domain.atelier.statut_dossier import GravitePanne, StatutDossier, StatutTache
from garage_app.domain.atelier import events
from garage_app.domain.shared.exceptions import BusinessRuleError, InvariantViolationError


def make_dossier() -> DossierReparation:
    return DossierReparation(
        vehicule_id=uuid.uuid4(),
        client_id=uuid.uuid4(),
        kilometrage_entree=50000,
    )


class TestStateMachine:
    def test_initial_state_is_cree(self):
        d = make_dossier()
        assert d.statut == StatutDossier.CREE

    def test_lancer_diagnostic(self):
        d = make_dossier()
        d.lancer_diagnostic()
        assert d.statut == StatutDossier.DIAGNOSTIC
        evts = d.pull_events()
        assert any(isinstance(e, events.DiagnosticLance) for e in evts)

    def test_cannot_lancer_diagnostic_twice(self):
        d = make_dossier()
        d.lancer_diagnostic()
        with pytest.raises(BusinessRuleError):
            d.lancer_diagnostic()

    def test_enregistrer_panne(self):
        d = make_dossier()
        d.lancer_diagnostic()
        d.pull_events()
        ligne = LigneDiagnostic(code_defaut="P0300", description="Ratés allumage", gravite=GravitePanne.BLOQUANT)
        d.enregistrer_panne(ligne)
        assert len(d.lignes_diagnostic) == 1
        evts = d.pull_events()
        assert any(isinstance(e, events.PanneIdentifiee) for e in evts)

    def test_soumettre_au_devis_requires_panne(self):
        d = make_dossier()
        d.lancer_diagnostic()
        d.pull_events()
        with pytest.raises(InvariantViolationError):
            d.soumettre_au_devis()

    def test_full_happy_path(self):
        d = make_dossier()
        d.lancer_diagnostic()
        ligne = LigneDiagnostic(code_defaut="P0300", description="Ratés", gravite=GravitePanne.BLOQUANT)
        d.enregistrer_panne(ligne)
        d.soumettre_au_devis()
        assert d.statut == StatutDossier.EN_ATTENTE_DEVIS

        devis_id = uuid.uuid4()
        d.approuver_devis(devis_id)
        assert d.statut == StatutDossier.EN_COURS
        assert d.devis_id == devis_id

        op = OperationMecanique(
            description="Remplacement bobines",
            temps_passe=Decimal("2"),
            taux_horaire=Decimal("60"),
            statut=StatutTache.TERMINEE,
        )
        d.ajouter_operation(op)
        d.terminer_reparation()
        assert d.statut == StatutDossier.QUALITE

        d.valider_controle_qualite()
        assert d.statut == StatutDossier.PRET

        facture_id = uuid.uuid4()
        d.generer_facture(facture_id, Decimal("144"))
        assert d.statut == StatutDossier.CLOTURE
        assert d.facture_id == facture_id

    def test_terminer_reparation_blocks_on_incomplete_tasks(self):
        d = make_dossier()
        d.lancer_diagnostic()
        ligne = LigneDiagnostic(code_defaut="P0300", description="Ratés", gravite=GravitePanne.BLOQUANT)
        d.enregistrer_panne(ligne)
        d.soumettre_au_devis()
        d.approuver_devis(uuid.uuid4())
        op = OperationMecanique(description="Travaux", statut=StatutTache.EN_COURS)
        d.ajouter_operation(op)
        with pytest.raises(InvariantViolationError):
            d.terminer_reparation()

    def test_montant_total(self):
        d = make_dossier()
        d.lancer_diagnostic()
        d.enregistrer_panne(LigneDiagnostic(description="Panne", code_defaut="X1"))
        d.soumettre_au_devis()
        d.approuver_devis(uuid.uuid4())
        op = OperationMecanique(
            description="Main d'oeuvre",
            temps_passe=Decimal("3"),
            taux_horaire=Decimal("50"),
            statut=StatutTache.TERMINEE,
        )
        d.ajouter_operation(op)
        piece = PieceRequise(designation="Filtre", quantite=2, prix_unitaire=Decimal("25"))
        d.ajouter_piece(piece)
        assert d.montant_total_ht.amount == Decimal("200")  # 150 + 50
