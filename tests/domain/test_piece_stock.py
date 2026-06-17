"""Domain unit tests for Piece stock operations."""
import pytest
from garage_app.domain.stock.piece import Piece
from garage_app.domain.stock.events import StockAlerteDeclenchee, InventaireAjuste


def test_entrer_stock():
    p = Piece(quantite_stock=5)
    p.entrer_stock(10)
    assert p.quantite_stock == 15


def test_entrer_stock_zero_raises():
    p = Piece()
    with pytest.raises(ValueError):
        p.entrer_stock(0)


def test_sortir_stock():
    p = Piece(quantite_stock=10)
    p.sortir_stock(3)
    assert p.quantite_stock == 7


def test_sortir_stock_insuffisant_raises():
    p = Piece(quantite_stock=2)
    with pytest.raises(ValueError, match="insuffisant"):
        p.sortir_stock(5)


def test_sortir_stock_declenche_alerte():
    p = Piece(quantite_stock=6, seuil_alerte=5)
    p.sortir_stock(2)
    events = p.pull_events()
    assert any(isinstance(e, StockAlerteDeclenchee) for e in events)


def test_ajuster_stock():
    p = Piece(quantite_stock=10)
    p.ajuster_stock(3)
    assert p.quantite_stock == 3
    events = p.pull_events()
    ajust = [e for e in events if isinstance(e, InventaireAjuste)]
    assert len(ajust) == 1
    assert ajust[0].ancienne_quantite == 10
    assert ajust[0].nouvelle_quantite == 3


def test_ajuster_stock_negatif_raises():
    p = Piece(quantite_stock=5)
    with pytest.raises(ValueError):
        p.ajuster_stock(-1)


def test_ajuster_stock_sous_seuil_declenche_alerte():
    p = Piece(quantite_stock=20, seuil_alerte=5)
    p.ajuster_stock(2)
    events = p.pull_events()
    assert any(isinstance(e, StockAlerteDeclenchee) for e in events)


def test_est_disponible():
    p = Piece(quantite_stock=1)
    assert p.est_disponible is True
    p2 = Piece(quantite_stock=0)
    assert p2.est_disponible is False


def test_en_alerte():
    p = Piece(quantite_stock=3, seuil_alerte=5)
    assert p.en_alerte is True
    p2 = Piece(quantite_stock=10, seuil_alerte=5)
    assert p2.en_alerte is False
