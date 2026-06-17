"""Unit tests for Facture aggregate."""
from decimal import Decimal

import pytest

from garage_app.domain.facturation.facture import Facture, LigneFacture


def make_facture() -> Facture:
    f = Facture(numero="F2025-0001")
    f.lignes.append(LigneFacture(designation="Main d'oeuvre", quantite=1, prix_unitaire=Decimal("120")))
    f.lignes.append(LigneFacture(designation="Filtre", quantite=2, prix_unitaire=Decimal("15")))
    return f


class TestFacture:
    def test_montant_ht(self):
        f = make_facture()
        assert f.montant_ht.amount == Decimal("150")

    def test_montant_ttc_20pct(self):
        f = make_facture()
        assert f.montant_ttc.amount == Decimal("180.00")

    def test_paiement(self):
        f = make_facture()
        f.emettre()
        f.enregistrer_paiement("carte")
        assert f.statut_paiement == "paye"

    def test_double_paiement_raises(self):
        f = make_facture()
        f.emettre()
        f.enregistrer_paiement("especes")
        with pytest.raises(ValueError):
            f.enregistrer_paiement("carte")
