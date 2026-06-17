"""Domain unit tests for CommandeFournisseur state machine."""
import uuid
import pytest
from garage_app.domain.stock.commande_fournisseur import (
    CommandeFournisseur, StatutCommande,
)
from garage_app.domain.stock.events import CommandeEnvoyee, PiecesRecues


def _commande_with_lines() -> CommandeFournisseur:
    c = CommandeFournisseur(fournisseur_id=uuid.uuid4())
    c.ajouter_ligne(uuid.uuid4(), quantite=10, prix_unitaire=5.0, designation="Filtre")
    c.ajouter_ligne(uuid.uuid4(), quantite=4, prix_unitaire=20.0, designation="Bougie")
    return c


def test_new_commande_is_brouillon():
    c = CommandeFournisseur()
    assert c.statut == StatutCommande.BROUILLON
    assert c.lignes == []


def test_ajouter_ligne():
    c = CommandeFournisseur()
    l = c.ajouter_ligne(uuid.uuid4(), 5, designation="Pièce")
    assert len(c.lignes) == 1
    assert l.quantite_commandee == 5
    assert l.quantite_recue == 0


def test_ajouter_ligne_quantite_zero_raises():
    c = CommandeFournisseur()
    with pytest.raises(ValueError):
        c.ajouter_ligne(uuid.uuid4(), 0)


def test_supprimer_ligne():
    c = CommandeFournisseur()
    l = c.ajouter_ligne(uuid.uuid4(), 3)
    c.supprimer_ligne(l.id)
    assert c.lignes == []


def test_envoyer_transition():
    c = _commande_with_lines()
    c.envoyer()
    assert c.statut == StatutCommande.ENVOYEE
    events = c.pull_events()
    assert any(isinstance(e, CommandeEnvoyee) for e in events)


def test_envoyer_sans_lignes_raises():
    c = CommandeFournisseur()
    with pytest.raises(ValueError, match="au moins une ligne"):
        c.envoyer()


def test_envoyer_non_brouillon_raises():
    c = _commande_with_lines()
    c.envoyer()
    with pytest.raises(ValueError):
        c.envoyer()


def test_recevoir_tout():
    c = _commande_with_lines()
    c.envoyer()
    c.pull_events()
    events = c.recevoir_tout()
    assert c.statut == StatutCommande.RECUE
    assert len(events) == 2
    assert all(isinstance(e, PiecesRecues) for e in events)
    assert all(l.est_recue for l in c.lignes)


def test_recevoir_partiel():
    c = _commande_with_lines()
    c.envoyer()
    c.pull_events()
    ligne = c.lignes[0]
    c.recevoir_partiel({ligne.id: 5})
    assert c.statut == StatutCommande.PARTIELLEMENT_RECUE
    assert ligne.quantite_recue == 5
    assert not ligne.est_recue


def test_recevoir_partiel_puis_tout():
    c = _commande_with_lines()
    c.envoyer()
    c.pull_events()
    l0, l1 = c.lignes
    c.recevoir_partiel({l0.id: 10, l1.id: 4})
    assert c.statut == StatutCommande.RECUE


def test_recevoir_ne_depasse_pas_commande():
    c = _commande_with_lines()
    c.envoyer()
    ligne = c.lignes[0]
    c.recevoir_partiel({ligne.id: 999})
    assert ligne.quantite_recue == ligne.quantite_commandee


def test_annuler_brouillon():
    c = _commande_with_lines()
    c.annuler()
    assert c.statut == StatutCommande.ANNULEE


def test_annuler_envoyee():
    c = _commande_with_lines()
    c.envoyer()
    c.pull_events()
    c.annuler()
    assert c.statut == StatutCommande.ANNULEE


def test_annuler_recue_raises():
    c = _commande_with_lines()
    c.envoyer()
    c.recevoir_tout()
    with pytest.raises(ValueError):
        c.annuler()


def test_modifier_commande_non_brouillon_raises():
    c = _commande_with_lines()
    c.envoyer()
    with pytest.raises(ValueError):
        c.ajouter_ligne(uuid.uuid4(), 1)


def test_reste_a_recevoir():
    c = _commande_with_lines()
    l = c.lignes[0]
    assert l.reste_a_recevoir == l.quantite_commandee
    c.envoyer()
    c.recevoir_partiel({l.id: 3})
    assert l.reste_a_recevoir == l.quantite_commandee - 3
