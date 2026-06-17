# Sprint 02 — Gestion des Stocks & Fournisseurs

**Statut :** Planifié
**Priorité :** Haute (bloquant facturation complète)

---

## Objectif

Implémenter la gestion des achats de pièces, le suivi des stocks et la gestion des fournisseurs.

---

## Contexte métier

Le garage achète des pièces détachées auprès de fournisseurs.
Ces pièces sont stockées, puis consommées lors des réparations (`PieceRequise` dans un `DossierReparation`).
Le responsable doit pouvoir : commander, réceptionner, suivre le stock, et être alerté en cas de rupture.

---

## Bounded Context : Stock

```
Fournisseur ──1:N──► CommandeFournisseur ──1:N──► LigneCommande ──N:1──► Piece
                              │
                     (réceptionner)
                              │
                              ▼
                    MouvementStock (entree)
                              │
                    Piece.stock_actuel +/-
```

---

## Agrégats & Entités

### `Fournisseur` (AggregateRoot)
| Champ | Type |
|---|---|
| raison_sociale | str |
| contact_nom | str |
| telephone | str |
| email | str |
| adresse | str |
| delai_livraison_jours | int |
| est_actif | bool |

### `CommandeFournisseur` (AggregateRoot — state machine)

États : `BROUILLON → ENVOYEE → PARTIELLEMENT_RECUE → RECUE → ANNULEE`

| Méthode | Transition | Règle |
|---|---|---|
| `envoyer()` | BROUILLON → ENVOYEE | ≥1 ligne |
| `recevoir_partiel(lignes)` | ENVOYEE → PARTIELLEMENT_RECUE | |
| `recevoir_tout()` | → RECUE | Déclenche MouvementsStock |
| `annuler()` | BROUILLON/ENVOYEE → ANNULEE | |

### `Piece` (AggregateRoot — déjà scaffoldé, à enrichir)
- Ajouter `fournisseur_id_prefere`, `prix_achat`, `prix_vente`, `emplacement`
- `entrer_stock(qte, ref_commande)` → `MouvementStock(entree)`
- `sortir_stock(qte, ref_dossier)` → `MouvementStock(sortie)`

### `MouvementStock` (Entity)
| Champ | Type |
|---|---|
| piece_id | UUID |
| type | entree \| sortie \| ajustement |
| quantite | int |
| reference | str (commande ID / dossier ID) |
| horodatage | datetime |
| utilisateur_id | UUID |

---

## Règles métier

1. **Stock négatif interdit** : sortie bloquée si `stock_actuel - qte < 0`
2. **Alerte seuil** : si `stock_actuel < stock_alerte` → `StockAlerteDeclenchee`
3. **Prix de revient** : FIFO sur les entrées (sprint optionnel)
4. **Inventaire** : `ajustement` reset le stock_actuel à la valeur comptée

---

## Events domaine

| Event | Déclencheur |
|---|---|
| `FournisseurCree` | Nouveau fournisseur |
| `CommandeCreee` | Brouillon crée |
| `CommandeEnvoyee` | Commande transmise au fournisseur |
| `PiecesRecues` | Réception partielle ou totale |
| `StockAlerteDeclenchee` | Stock < seuil |
| `InventaireAjuste` | Ajustement manuel |

---

## Couche Application

| Service | Permission | Description |
|---|---|---|
| `FournisseurService` | MANAGE_STOCK | CRUD fournisseurs |
| `CommandeService` | MANAGE_STOCK | Créer / envoyer / réceptionner |
| `StockService` | MANAGE_STOCK | Ajustements, mouvements, alertes |
| `InventaireService` | MANAGE_STOCK | Comptage physique |

---

## GUI (sous-fenêtres MDI)

| Fenêtre | Description |
|---|---|
| `FournisseurWindow` | Master/Detail fournisseurs |
| `CommandeWindow` | Création/réception de commandes |
| `StockMouvementsWindow` | Historique des mouvements |
| `AlertesStockWindow` | Pièces en dessous du seuil |
| `InventaireWindow` | Comptage physique |

---

## Tables DB nouvelles

- `fournisseurs`
- `commandes_fournisseur`
- `lignes_commande`
- `mouvements_stock`
- Enrichissement `pieces` : `fournisseur_id_prefere`, `prix_achat`, `prix_vente`, `emplacement`
