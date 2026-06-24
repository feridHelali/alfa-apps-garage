# Sprint 07 — Offres Commerciales, Devis & Facture Proforma

**Statut :** En cours (implémentation partielle — 2026-06-25)

## Avancement

| Livrable | Statut |
|---|---|
| Permissions VIEW/MANAGE/CONVERT_DEVIS, VIEW/MANAGE_PROFORMA | ✅ Terminé |
| Domain: `Devis`, `LigneDevis`, `FactureProforma`, `LigneProforma`, events, repos ABC | ✅ Terminé |
| Infrastructure: migrations devis table, `LigneDevisModel`, `FactureProformaModel`, `LigneProformaModel` | ✅ Terminé |
| Repositories: `SqlAlchemyDevisRepository`, `SqlAlchemyProformaRepository` | ✅ Terminé |
| Application: `DevisService` (CRUD + transitions + convert → proforma + convert → dossier) | ✅ Terminé |
| Bootstrap wiring + `NumerotationService` types devis/proforma | ✅ Terminé |
| GUI: `DevisListWindow`, `DevisFormWindow`, `ProformaViewerWindow`, `ProformaListWindow` | ✅ Terminé |
| Menu Atelier → Devis (Ctrl+W), Facturation → Proforma | ✅ Terminé |
| Guide ch. 8 — Devis & Proforma | ✅ Terminé |
| Tests domaine | ❌ Non implémenté |
| Report Designer — types devis/proforma | ❌ Différé |
**Dépend de :** Sprint 05 (Numérotation, Report Designer), Sprint 03 (Facturation)

---

## Objectif

Implémenter le cycle commercial **avant-vente** d'un garage automobile :
de la première offre au client, jusqu'à la transformation en dossier de réparation
et à la facturation finale. Ce sprint couvre les documents commerciaux qui précèdent
la facture définitive dans le flux de travail professionnel.

```
Offre Commerciale ──► Devis ──► Accepté ──► Dossier Réparation ──► Facture Client
                         │
                         └──► Facture Proforma ──► (acompte ou import) ──► Facture Client
```

---

## Contexte métier

En Tunisie, les garages intermédiaires (carrosserie, climatisation, électronique) émettent
systématiquement un **devis signé** avant tout travail. Ce document :

1. Protège le garage légalement (acceptation formelle du client)
2. Sert de base de facturation (reprend toutes les lignes)
3. Peut être converti en **facture proforma** pour les clients professionnels (importation, remboursement assurance)
4. Alimente directement la création du **dossier de réparation**

---

## Règles métier clés

| Règle | Description |
|---|---|
| **Devis ≠ Facture** | Un devis n'est pas un document comptable — pas de TVA collectée jusqu'à la facture |
| **Acceptation formelle** | Un devis doit être passé à l'état ACCEPTÉ avant toute conversion |
| **Conversion atomique** | La conversion Devis → Dossier crée le dossier + lie les lignes + met à jour le statut en une transaction |
| **Proforma ≠ Facture** | La facture proforma n'a pas de valeur comptable — elle sert d'engagement ou de demande d'acompte |
| **Numérotation indépendante** | Devis, Proforma ont leurs propres séquences (DEV-YYYY-NNN, PRO-YYYY-NNN) |
| **Expiration du devis** | Un devis non répondu après N jours (configurable) passe automatiquement en EXPIRÉ |
| **Immutabilité accepté** | Un devis ACCEPTÉ ne peut plus être modifié — seule une copie (révision) est possible |

---

## États du Devis

```
┌──────────────┐    Envoi    ┌──────────┐   Accord client   ┌────────────┐
│  BROUILLON   │───────────►│  ENVOYÉ  │──────────────────►│  ACCEPTÉ   │
└──────────────┘            └──────────┘                    └────────────┘
       │                         │                                │
       │ Annulation               │ Refus client                   │ Conversion
       ▼                         ▼                                ▼
┌──────────────┐            ┌──────────┐                    ┌──────────────────┐
│   ANNULÉ     │            │  REFUSÉ  │                    │ TRANSFORMÉ       │
└──────────────┘            └──────────┘                    │ (Dossier ou      │
                                 │                           │  Proforma créé)  │
                            ┌──────────┐                    └──────────────────┘
                            │  EXPIRÉ  │ (après N jours sans réponse)
                            └──────────┘
```

---

## Feature 1 — Domaine : Devis (OffreCommerciale / Devis)

### Aggregate : `Devis`

```python
@dataclass
class Devis(AggregateRoot):
    id: UUID
    numero: str                         # DEV-2026-001
    client_id: UUID
    vehicule_id: UUID | None
    statut: StatutDevis                  # BROUILLON, ENVOYE, ACCEPTE, REFUSE, TRANSFORME, EXPIRE, ANNULE
    date_creation: date
    date_expiration: date | None         # None = pas d'expiration
    lignes: list[LigneDevis]
    notes_client: str                    # Description des travaux demandés
    notes_internes: str                  # Notes internes garage
    dossier_id: UUID | None             # Renseigné après conversion
    proforma_id: UUID | None            # Renseigné si proforma créée
    created_by: UUID                    # Technicien / réceptionniste
    updated_at: datetime

@dataclass
class LigneDevis:
    id: UUID
    devis_id: UUID
    type_ligne: TypeLigne               # SERVICE, PIECE, FORFAIT
    designation: str
    quantite: Decimal
    prix_unitaire_ht: Money
    taux_tva: Decimal                   # ex: 0.19
    remise_pct: Decimal                 # 0.0 à 1.0

    @property
    def montant_ht(self) -> Money: ...
    @property
    def montant_tva(self) -> Money: ...
    @property
    def montant_ttc(self) -> Money: ...
```

### Méthodes de l'agrégat

| Méthode | Description | Transition |
|---|---|---|
| `envoyer()` | Finalise le brouillon et le marque comme envoyé | BROUILLON → ENVOYE |
| `accepter(par: UUID)` | Enregistre l'accord du client | ENVOYE → ACCEPTE |
| `refuser(motif: str)` | Enregistre le refus | ENVOYE → REFUSE |
| `annuler()` | Annule le devis | BROUILLON/ENVOYE → ANNULE |
| `expirer()` | Appelé par le planificateur | ENVOYE → EXPIRE |
| `marquer_transforme(dossier_id, proforma_id)` | Marque comme converti | ACCEPTE → TRANSFORME |
| `dupliquer()` → `Devis` | Crée une révision (nouveau brouillon) | — |

### Événements domaine

- `DevisCreePourClient(devis_id, client_id, vehicule_id)`
- `DevisAccepteParClient(devis_id, client_id, accepte_par)`
- `DevisTransformeEnDossier(devis_id, dossier_id)`
- `DevisTransformeEnProforma(devis_id, proforma_id)`

---

## Feature 2 — Domaine : Facture Proforma

### Aggregate : `FactureProforma`

```python
@dataclass
class FactureProforma(AggregateRoot):
    id: UUID
    numero: str                         # PRO-2026-001
    client_id: UUID
    devis_id: UUID | None               # Source si créée depuis un devis
    statut: StatutProforma              # EMISE, ACOMPTE_RECU, ANNULEE, LIEE_FACTURE
    date_emission: date
    lignes: list[LigneProforma]         # Identiques à LigneDevis
    acompte_recu: Money                 # Montant déjà encaissé
    facture_finale_id: UUID | None      # Renseigné quand la facture définitive est créée
    notes: str
```

### Règles spécifiques à la Proforma

- Pas de paiement de solde sur la proforma — uniquement un acompte
- Lors de la création de la facture définitive, l'acompte de la proforma est automatiquement
  déduit comme paiement partiel
- Une proforma peut exister indépendamment d'un devis (créée manuellement)

---

## Feature 3 — Conversion Devis → Dossier

### Service : `DevisService.convertir_en_dossier(devis_id, session)`

**Préconditions :** `devis.statut == ACCEPTE`

**Algorithme :**

```
BEGIN TRANSACTION
  1. Charger le devis (avec ses lignes)
  2. Créer un DossierReparation (statut=CREE)
     - client_id = devis.client_id
     - vehicule_id = devis.vehicule_id
     - notes = devis.notes_client
     - devis_source_id = devis.id
  3. Pour chaque LigneDevis de type PIECE :
     - Créer une LignePieceDossier correspondante (pré-réservation stock)
  4. Pour chaque LigneDevis de type SERVICE/FORFAIT :
     - Créer une LigneOperationDossier correspondante
  5. Appeler devis.marquer_transforme(dossier_id=dossier.id)
  6. Sauvegarder devis + dossier
  7. Publier DevisTransformeEnDossier
COMMIT
```

**Retourne :** `dossier_id: UUID`

---

## Feature 4 — Conversion Devis → Facture Proforma

### Service : `DevisService.convertir_en_proforma(devis_id, session)`

**Préconditions :** `devis.statut == ACCEPTE`

**Algorithme :**

```
BEGIN TRANSACTION
  1. Créer FactureProforma avec les lignes du devis
  2. Numéroter (NumerotationService)
  3. devis.marquer_transforme(proforma_id=proforma.id)
  4. Sauvegarder
COMMIT
```

---

## Feature 5 — GUI : DevisListWindow

Fenêtre MDI liste des devis — `gui/devis/devis_list_window.py`

**Colonnes du tableau :**

| Colonne | Type | Description |
|---|---|---|
| Numéro | str | DEV-2026-001 |
| Date | date | Date de création |
| Client | str | Nom complet |
| Véhicule | str | Immatriculation |
| Montant TTC | Money | Total du devis |
| Statut | badge coloré | BROUILLON / ENVOYÉ / ACCEPTÉ / … |
| Expiration | date | Date d'expiration (rouge si dépassée) |

**Actions disponibles selon statut :**

| Action | Statut requis |
|---|---|
| Nouveau | — |
| Modifier | BROUILLON |
| Envoyer | BROUILLON |
| Accepter | ENVOYE |
| Refuser | ENVOYE |
| Convertir → Dossier | ACCEPTE |
| Convertir → Proforma | ACCEPTE |
| Dupliquer (révision) | Tout |
| Imprimer | Tout |
| Annuler | BROUILLON, ENVOYE |

---

## Feature 6 — GUI : DevisFormWindow

Formulaire de saisie d'un devis — `gui/devis/devis_form_window.py`

**Layout (3 zones) :**

```
┌─────────────────────────────────────────────────────────────┐
│ En-tête : Client, Véhicule, Date, Expiration, Notes client  │
├─────────────────────────────────────────────────────────────┤
│ Tableau de lignes (éditables en place) :                    │
│  Type | Désignation | Qté | PU HT | TVA | Remise | Total   │
│  [+Ajouter] [Supprimer] [Monter/Descendre]                 │
├─────────────────────────────────────────────────────────────┤
│ Totaux (droite) : Total HT | TVA | Remise | TTC            │
│ Notes internes (gauche)                                     │
│ Boutons : [Enregistrer] [Envoyer] [Annuler]                │
└─────────────────────────────────────────────────────────────┘
```

**Sélection de pièces :** Popup de recherche dans le catalogue stock avec auto-complétion.
Les prix d'achat et de vente sont pré-remplis depuis le catalogue.

---

## Feature 7 — GUI : ProformaViewerWindow

Aperçu et gestion d'une facture proforma — `gui/devis/proforma_viewer_window.py`

- Aperçu HTML (même moteur que FactureReportWindow)
- Bouton **Enregistrer acompte** : saisir un paiement partiel
- Bouton **Créer la facture définitive** : génère la Facture avec l'acompte déjà imputé
- Bouton **Imprimer**

---

## Tables DB

### `devis`

```sql
CREATE TABLE devis (
    id TEXT PRIMARY KEY,
    numero TEXT UNIQUE NOT NULL,
    client_id TEXT NOT NULL REFERENCES clients(id),
    vehicule_id TEXT REFERENCES vehicules(id),
    statut TEXT NOT NULL DEFAULT 'BROUILLON',
    date_creation TEXT NOT NULL,
    date_expiration TEXT,
    notes_client TEXT NOT NULL DEFAULT '',
    notes_internes TEXT NOT NULL DEFAULT '',
    dossier_id TEXT REFERENCES dossiers(id),
    proforma_id TEXT,
    created_by TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### `lignes_devis`

```sql
CREATE TABLE lignes_devis (
    id TEXT PRIMARY KEY,
    devis_id TEXT NOT NULL REFERENCES devis(id) ON DELETE CASCADE,
    type_ligne TEXT NOT NULL,         -- SERVICE, PIECE, FORFAIT
    designation TEXT NOT NULL,
    quantite TEXT NOT NULL DEFAULT '1',
    prix_unitaire_ht TEXT NOT NULL,
    taux_tva TEXT NOT NULL DEFAULT '0.19',
    remise_pct TEXT NOT NULL DEFAULT '0',
    ordre INTEGER NOT NULL DEFAULT 0,
    piece_id TEXT REFERENCES pieces(id)  -- NULL pour les services
);
```

### `factures_proforma`

```sql
CREATE TABLE factures_proforma (
    id TEXT PRIMARY KEY,
    numero TEXT UNIQUE NOT NULL,
    client_id TEXT NOT NULL REFERENCES clients(id),
    devis_id TEXT REFERENCES devis(id),
    statut TEXT NOT NULL DEFAULT 'EMISE',
    date_emission TEXT NOT NULL,
    acompte_recu TEXT NOT NULL DEFAULT '0',
    facture_finale_id TEXT,
    notes TEXT NOT NULL DEFAULT ''
);
```

### `lignes_proforma`

```sql
CREATE TABLE lignes_proforma (
    id TEXT PRIMARY KEY,
    proforma_id TEXT NOT NULL REFERENCES factures_proforma(id) ON DELETE CASCADE,
    -- mêmes colonnes que lignes_devis --
    type_ligne TEXT NOT NULL,
    designation TEXT NOT NULL,
    quantite TEXT NOT NULL,
    prix_unitaire_ht TEXT NOT NULL,
    taux_tva TEXT NOT NULL,
    remise_pct TEXT NOT NULL DEFAULT '0',
    ordre INTEGER NOT NULL DEFAULT 0
);
```

---

## Permissions requises

| Permission | Description |
|---|---|
| `VIEW_DEVIS` | Voir la liste des devis |
| `MANAGE_DEVIS` | Créer, modifier, envoyer, accepter des devis |
| `CONVERT_DEVIS` | Convertir un devis en dossier ou proforma |
| `VIEW_PROFORMA` | Voir les factures proforma |
| `MANAGE_PROFORMA` | Créer des factures proforma, enregistrer acomptes |

---

## Menu GUI

Menu **Atelier** :
- Devis clients… (`MANAGE_DEVIS`)

Menu **Facturation** :
- Factures proforma… (`VIEW_PROFORMA`)

---

## Plan d'implémentation

### Étape 1 — Domaine
- [ ] `src/garage_app/domain/devis/` — `StatutDevis`, `LigneDevis`, `Devis`, events
- [ ] `src/garage_app/domain/facturation/facture_proforma.py` — `FactureProforma`, `LigneProforma`
- [ ] Tests domain : `tests/domain/devis/test_devis.py`

### Étape 2 — Infrastructure
- [ ] Migration DB — tables `devis`, `lignes_devis`, `factures_proforma`, `lignes_proforma`
- [ ] `src/garage_app/infrastructure/models/` — ORM models
- [ ] `src/garage_app/infrastructure/repositories/` — `SqlAlchemyDevisRepository`, `SqlAlchemyProformaRepository`

### Étape 3 — Application
- [ ] `src/garage_app/application/devis_service.py` — CRUD + transitions + conversions
- [ ] `src/garage_app/application/proforma_service.py` — CRUD + acompte + création facture finale
- [ ] Injection dans `bootstrap.py`

### Étape 4 — GUI
- [ ] `src/garage_app/gui/devis/devis_list_window.py`
- [ ] `src/garage_app/gui/devis/devis_form_window.py`
- [ ] `src/garage_app/gui/devis/proforma_viewer_window.py`
- [ ] Ajout dans `main_window.py` — menus Atelier + Facturation
- [ ] Ajout dans `report_designer_window.py` — type de document `devis`

### Étape 5 — Report Designer
- [ ] Ajouter `devis` et `proforma` dans `_DOC_TYPES` du Report Designer
- [ ] Colonnes par défaut pour ces deux types de documents
- [ ] `SAMPLE_CONTEXTS` pour aperçu

---

## Critères d'acceptance

- [ ] Un devis BROUILLON peut être modifié librement
- [ ] Un devis ENVOYÉ ne peut être ni modifié ni supprimé
- [ ] Un devis ACCEPTÉ se convertit en Dossier avec toutes ses lignes
- [ ] Un devis REFUSÉ peut être dupliqué en nouvelle révision
- [ ] La facture proforma déduit automatiquement l'acompte sur la facture finale
- [ ] La numérotation est séquentielle et sans doublon
- [ ] Impression conforme via le Report Designer
