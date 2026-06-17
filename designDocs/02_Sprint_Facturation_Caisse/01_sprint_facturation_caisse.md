# Sprint 03 — Facturation, Caisse & Crédit

**Statut :** Planifié
**Dépend de :** Sprint 01 (Atelier — DossierReparation complet), Sprint 02 (Stock)

---

## Objectif

Implémenter le cycle complet de facturation : de la génération de la facture jusqu'à l'encaissement,
en passant par la gestion de la caisse journalière et les comptes clients en crédit.

---

## Règles métier clés

| Règle | Description |
|---|---|
| **Anti-Vol** | Clés non restituées tant que la facture n'est pas soldée |
| **Garantie-Qualité** | Facture générée uniquement après contrôle qualité validé |
| **Caisse unique** | Une seule session de caisse ouverte à la fois |
| **Écart de caisse** | Signalé en WARNING dans le journal d'audit |
| **Crédit flotte** | Client `est_flotte=True` → plafond de crédit configurable |

---

## Agrégats

### `Facture` (AggregateRoot — déjà scaffoldé)

États : `BROUILLON → EMISE → PARTIELLEMENT_PAYEE → PAYEE → ANNULEE`

Transitions :
- `emettre()` : BROUILLON → EMISE (déclenche `FactureEmise`)
- `enregistrer_paiement(montant, mode)` : calcule solde restant
- Solde = 0 → `PAYEE` → `VehiculeRestitue` event → déblocage clés

Modes de paiement : `ESPECES | CHEQUE | VIREMENT | CARTE | CREDIT`

### `SessionCaisse` (AggregateRoot — implémenté dans `caisse.py`)

- `ouvert_par` : user ID du caissier
- `encaisser(montant, motif, reference)` : paiement facture, autre encaissement
- `decaisser(montant, motif)` : sortie de caisse (achats petite monnaie, etc.)
- `fermer(solde_reel)` : retourne écart → loggé dans audit

### `CreditClient` (Value Object par client)

- `solde` : montant dû par le client
- `limite_credit` : `0` = illimité (flotte)
- `peut_crediter(montant)` : vérifie plafond

---

## Cycle complet

```
DossierReparation (PRET)
    │
    ├── generer_facture(montant_ttc)
    │       └── Facture créée (BROUILLON)
    │
    ├── Facture.emettre()
    │       └── FactureEmise → impression auto rapport
    │
    ├── Client paie à la caisse
    │       ├── SessionCaisse.encaisser(montant, motif="facture", ref=facture.id)
    │       └── Facture.enregistrer_paiement(montant, "ESPECES")
    │
    └── Facture.statut == PAYEE
            └── VehiculeRestitue → DossierReparation.statut == CLOTURE
```

---

## Couche Application

| Service | Permission | Description |
|---|---|---|
| `FactureService` | MANAGE_FACTURES | Générer, émettre, paiements |
| `CaisseService` | MANAGE_CAISSE | Ouvrir/fermer session, encaisser |
| `CreditService` | MANAGE_FACTURES | Consulter/ajuster solde crédit client |

---

## GUI

| Fenêtre | Description |
|---|---|
| `FactureListWindow` | Liste factures avec filtre (impayées, période) |
| `FactureDetailWindow` | Détail + bouton "Encaisser" |
| `CaisseWindow` | Session en cours : solde, mouvements du jour, fermeture |
| `CreditClientsWindow` | Tableau clients avec solde dû |

---

## Rapports

| Rapport | Template |
|---|---|
| Facture client | `invoice_v1` (seed) |
| Bon de réception véhicule | `bon_reception_v1` (seed) |
| Relevé de caisse journalier | À créer : `releve_caisse_v1` |
| État des créances | À créer : `etat_creances_v1` |

---

## Tables DB

- `factures` + `lignes_facture` + `paiements` (scaffoldées)
- `sessions_caisse` (nouvelle)
- `mouvements_caisse` (nouvelle)
- `credits_clients` (nouvelle)
