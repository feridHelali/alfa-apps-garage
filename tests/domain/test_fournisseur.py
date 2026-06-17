"""Domain unit tests for Fournisseur aggregate."""
import pytest
from garage_app.domain.stock.fournisseur import Fournisseur


def test_create_fournisseur_defaults():
    f = Fournisseur()
    assert f.est_actif is True
    assert f.delai_livraison_jours == 7


def test_desactiver():
    f = Fournisseur(raison_sociale="Acme")
    f.desactiver()
    assert f.est_actif is False


def test_desactiver_already_inactive_raises():
    f = Fournisseur(raison_sociale="Acme", est_actif=False)
    with pytest.raises(ValueError):
        f.desactiver()


def test_activer():
    f = Fournisseur(raison_sociale="Acme", est_actif=False)
    f.activer()
    assert f.est_actif is True


def test_activer_already_active_raises():
    f = Fournisseur(raison_sociale="Acme", est_actif=True)
    with pytest.raises(ValueError):
        f.activer()


def test_inequality_different_instances():
    f1 = Fournisseur(raison_sociale="A")
    f2 = Fournisseur(raison_sociale="A")
    assert f1 != f2  # different UUIDs → not equal
