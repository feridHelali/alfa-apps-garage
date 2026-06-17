"""Unit tests for Facture aggregate (Sprint 03 — multi-payment state machine)."""
from decimal import Decimal

import pytest

from garage_app.domain.facturation.facture import Facture, LigneFacture, StatutFacture
from garage_app.domain.facturation.events import FactureEmise, PaiementEncaisse, VehiculeRestitue


def make_facture() -> Facture:
    f = Facture(numero="F2025-0001")
    f.lignes.append(LigneFacture(designation="Main d'oeuvre", quantite=1, prix_unitaire=Decimal("120")))
    f.lignes.append(LigneFacture(designation="Filtre", quantite=2, prix_unitaire=Decimal("15")))
    return f


class TestFactureMontants:
    def test_montant_ht(self):
        f = make_facture()
        assert f.montant_ht.amount == Decimal("150")

    def test_montant_ttc_19pct(self):
        f = make_facture()
        # 150 * 1.19 = 178.50
        assert f.montant_ttc.amount == Decimal("178.50")

    def test_solde_restant_initial(self):
        f = make_facture()
        assert f.solde_restant == f.montant_ttc.amount

    def test_montant_paye_zero_initial(self):
        assert make_facture().montant_paye == Decimal("0")


class TestFactureStateMachine:
    def test_initial_statut_brouillon(self):
        assert make_facture().statut == StatutFacture.BROUILLON

    def test_emettre(self):
        f = make_facture()
        f.emettre()
        assert f.statut == StatutFacture.EMISE
        events = f.pull_events()
        assert any(isinstance(e, FactureEmise) for e in events)

    def test_emettre_sans_lignes_raises(self):
        f = Facture(numero="F0")
        with pytest.raises(ValueError, match="au moins une ligne"):
            f.emettre()

    def test_emettre_deux_fois_raises(self):
        f = make_facture()
        f.emettre()
        with pytest.raises(ValueError):
            f.emettre()

    def test_paiement_total(self):
        f = make_facture()
        f.emettre()
        f.pull_events()
        montant = f.montant_ttc.amount
        f.enregistrer_paiement(montant, "especes")
        assert f.statut == StatutFacture.PAYEE
        assert f.solde_restant == Decimal("0")
        events = f.pull_events()
        assert any(isinstance(e, PaiementEncaisse) for e in events)
        assert any(isinstance(e, VehiculeRestitue) for e in events)

    def test_paiement_partiel(self):
        f = make_facture()
        f.emettre()
        f.pull_events()
        f.enregistrer_paiement(Decimal("50"), "carte")
        assert f.statut == StatutFacture.PARTIELLEMENT_PAYEE
        assert f.montant_paye == Decimal("50")
        assert f.solde_restant > Decimal("0")

    def test_paiement_partiel_puis_solde(self):
        f = make_facture()
        f.emettre()
        f.enregistrer_paiement(Decimal("50"), "especes")
        f.enregistrer_paiement(f.solde_restant, "carte")
        assert f.statut == StatutFacture.PAYEE
        assert f.solde_restant == Decimal("0")

    def test_paiement_depasse_solde_raises(self):
        f = make_facture()
        f.emettre()
        with pytest.raises(ValueError, match="dépasse"):
            f.enregistrer_paiement(Decimal("99999"), "especes")

    def test_paiement_brouillon_raises(self):
        f = make_facture()
        with pytest.raises(ValueError):
            f.enregistrer_paiement(Decimal("10"), "especes")

    def test_annuler_emise(self):
        f = make_facture()
        f.emettre()
        f.pull_events()
        f.annuler()
        assert f.statut == StatutFacture.ANNULEE

    def test_annuler_payee_raises(self):
        f = make_facture()
        f.emettre()
        f.enregistrer_paiement(f.montant_ttc.amount, "especes")
        with pytest.raises(ValueError, match="déjà payée"):
            f.annuler()

    def test_paiement_montant_zero_raises(self):
        f = make_facture()
        f.emettre()
        with pytest.raises(ValueError, match="positif"):
            f.enregistrer_paiement(Decimal("0"), "especes")
