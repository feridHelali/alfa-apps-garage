# Sprint 05 — Numérotation, Factures Achat, Charges, Multi-Dossier, i18n AR/RTL & Report Designer

**Statut :** Terminé (partiel)
**Dépend de :** Sprint 03 (Facturation), Sprint 02 (Stock & Fournisseurs)
**Terminé le :** 2026-06-24

## Résumé d'implémentation

### Fonctionnalités livrées

| # | Feature | Statut | Fichiers clés |
|---|---|---|---|
| 1 | Numérotation configurable | ✅ Terminé | `application/numerotation_service.py`, `gui/admin/numerotation_window.py` |
| 2 | Factures Fournisseurs (FactureAchat) | ✅ Terminé | `domain/stock/facture_achat.py`, `gui/stock/facture_achat_window.py` |
| 3 | Charges du Garage | ✅ Terminé | `domain/facturation/charge_garage.py`, `gui/facturation/charge_window.py` |
| 4 | Multi-Dossier / DossierManager | ✅ Terminé | `dossier_manager.py`, `gui/dossier_selector_dialog.py` |
| 5 | Sidebar responsive | ✅ Terminé | `gui/main_window.py` — mode compact <1400px |
| 6 | Arabe & RTL (i18n) | ❌ Différé Sprint 06+ | — |
| 7 | Report Designer | ✅ Terminé | `tools/report_engine/html_template*.py`, `gui/reports/report_designer_window.py` |

### Corrections post-sprint

- `date_emission NOT NULL` — contrainte SQLite forcée via `server_default=func.now()`
- `next_numero MAX()` — correction de la requête utilisant `MAX(numero_seq)` au lieu de `COUNT`
- Login SVG logo — chargement via `resource_path()` dans `gui/auth/login_window.py`
- `resource_path()` helper — corrige tous les `__file__.parents[N]` pour le bundle PyInstaller frozen
- Seed trigger — `seed_runner.py` conditionnel au premier lancement uniquement
- `_DEFAULT_COLONNES` aliasing — `__post_init__` crée des copies fraîches de `ColonneConfig`
- `from_dict()` mutation — copie défensive `data = dict(data)` avant `pop("colonnes")`

### Non livré (différé)

- Arabe/RTL i18n (Feature 6) — complexité de retournement Qt layout, report Sprint 06+
- Bilan Charges vs CA graphique — report Sprint 06 (affiché en mode tableau uniquement)

---

## Objectif

Sept axes d'amélioration alignés sur les pratiques des ERP comptables (Sage, Ciel) :

1. **Numérotation configurable** — préfixe + compteur pour Factures, Dossiers, Bons de Travail, Factures Achat
2. **Factures Fournisseurs** — saisie d'une facture d'achat directe qui met à jour le stock et le prix d'achat
3. **Charges du Garage** — suivi des dépenses récurrentes et ponctuelles (loyer, salaires, électricité…)
4. **Multi-Dossier / Multi-Instance (Sage-like)** — création d'une nouvelle base de données (nouvel exercice ou nouvelle société) en self-service, avec seed automatique
5. **Sidebar responsive** — mode compact pour écrans 15" (1366 × 768)
6. **Arabe & RTL (i18n)** — support complet de l'interface en arabe avec retournement RTL de la mise en page
7. **Report Designer (self-service)** — créer, stocker et réutiliser des formats de documents (façon Crystal Reports / Access)

---

## Règles métier clés

| Règle | Description |
|---|---|
| **Unicité numéro** | Génération atomique dans une transaction — jamais de doublon |
| **Réinitialisation annuelle** | Compteur peut se remettre à 1 au 1er janvier si activé |
| **Stock validé à la facture** | `FactureAchat.valider()` est le seul déclencheur d'entrée de stock (pas la commande) |
| **Charge payée ≠ caisse** | Payer une charge n'ouvre pas la caisse — c'est un flux comptable distinct |
| **Isolation DB** | Chaque dossier Sage = un fichier `.db` distinct ; la session active est sélectionnée au démarrage |
| **Seed toujours présente** | Toute nouvelle base reçoit le seed complet (rôles, utilisateurs, société, paramètres) |
| **Locale par utilisateur** | La langue/direction est stockée par utilisateur dans `app_settings` et s'applique sans redémarrage |
| **Modèle de rapport isolé** | Les formats de rapport sont des fichiers JSON stockés hors DB — portables, versionnables |

---

## Feature 1 — Numérotation configurable

### Contexte

Actuellement `next_numero()` scanne les lignes existantes (`MAX + 1`). L'approche Sage stocke un
**compteur persistant** modifiable par l'utilisateur — ce qui permet :
- de caler la numérotation sur l'existant lors d'une première installation,
- de choisir un préfixe métier (`GAR-`, `REP-`, `2026/`…),
- de réinitialiser le compteur chaque année.

### Domaine — `NumerotationConfig` (Value Object persisté)

```
Clés app_settings — une entrée par type de document :

  numerotation.{type}.prefixe          ex. "F{ANNEE}-"
  numerotation.{type}.prochain         ex. "1"        (entier, incrémenté atomiquement)
  numerotation.{type}.longueur         ex. "4"        (zéro-padding)
  numerotation.{type}.reset_annuel     ex. "true"
  numerotation.{type}.dernier_annee    ex. "2026"     (détecte le changement d'année)

Types : facture | dossier | bon_travail | facture_achat
```

Macros de préfixe : `{ANNEE}` → `2026`, `{MOIS}` → `06`

Exemples de rendu :

| Type | Préfixe | Prochain | Résultat |
|---|---|---|---|
| Facture | `F{ANNEE}-` | 42 | `F2026-0042` |
| Dossier | `REP-` | 7 | `REP-0007` |
| Bon de Travail | `BT{ANNEE}/` | 3 | `BT2026/0003` |
| Facture Achat | `FA-` | 15 | `FA-0015` |

### Application — `NumerotationService`

```python
class NumerotationService:
    @require_permission(Permission.MANAGE_SETTINGS)
    def get_config(self, session, type_doc: str) -> NumerotationConfig: ...

    @require_permission(Permission.MANAGE_SETTINGS)
    def update_config(self, session, type_doc: str, config: NumerotationConfig) -> None: ...

    def generer_numero(self, type_doc: str) -> str:
        """Lit, incrémente et persiste le compteur dans UNE transaction."""
```

> `generer_numero` n'a pas de garde `@require_permission` — il est appelé
> depuis d'autres services (FactureService, DossierService…) déjà sécurisés.

Migration : remplacer tous les appels `repo.next_numero()` par
`numerotation_service.generer_numero(type)`.

### GUI — onglet « Numérotation » dans `SettingsWindow`

| Champ | Exemple |
|---|---|
| Type de document | Facture (dropdown) |
| Préfixe | `F{ANNEE}-` |
| Prochain numéro | `42` (spinbox modifiable) |
| Longueur séquence | `4` |
| Réinitialisation annuelle | ☑ |
| **Aperçu** | `F2026-0042` (mis à jour en live) |

Bouton « Tester » qui génère un numéro d'aperçu sans incrémenter.

### DB

Table `app_settings` existante — nouvelles clés ajoutées par `SeedRunner`.

Migration `_COLUMN_MIGRATIONS` : aucune modification de schéma nécessaire.

---

## Feature 2 — Factures Fournisseurs (Achat Direct + Mise à jour Stock)

### Contexte

Un achat de pièces peut arriver sans bon de commande préalable (achat cash, dépannage urgent).
La facture fournisseur est **la pièce comptable de référence** ; c'est sa validation qui déclenche
l'entrée en stock et la mise à jour du prix d'achat — exactement comme dans Sage.

### Domaine

#### `FactureAchat` (AggregateRoot)

```
États : SAISIE → VALIDEE → PAYEE → ANNULEE
```

| Champ | Type | Détail |
|---|---|---|
| `fournisseur_id` | UUID | |
| `numero_fournisseur` | str | N° sur la facture papier |
| `notre_numero` | str | généré par `NumerotationService` (type `facture_achat`) |
| `date_facture` | datetime | |
| `date_echeance` | datetime \| None | pour alerte paiement fournisseur |
| `lignes` | list[LigneAchat] | |
| `statut` | StatutAchat | |
| `commande_id` | UUID \| None | lien optionnel à `CommandeFournisseur` |
| `notes` | str | |

#### `LigneAchat` (Entity)

| Champ | Type |
|---|---|
| `piece_id` | UUID |
| `designation` | str |
| `quantite` | int |
| `prix_unitaire` | Decimal |

#### Transitions d'état

| Méthode | De → Vers | Effet |
|---|---|---|
| `valider()` | SAISIE → VALIDEE | Pour chaque ligne : `Piece.entrer_stock(qte)` + `Piece.prix_achat = prix_unitaire` → `FactureAchatValidee` |
| `marquer_payee(mode, ref)` | VALIDEE → PAYEE | `FactureAchatPayee` |
| `annuler()` | SAISIE → ANNULEE | Si VALIDEE → `Piece.sortir_stock(qte)` (correction) → `FactureAchatAnnulee` |

#### Events domaine

```python
FactureAchatValidee(facture_id, fournisseur_id, montant_ttc)
FactureAchatPayee(facture_id, fournisseur_id, montant, mode)
FactureAchatAnnulee(facture_id)
```

### Application — `FactureAchatService`

| Méthode | Permission |
|---|---|
| `list_factures_achat(session)` | `VIEW_STOCK` |
| `get_facture_achat(session, id)` | `VIEW_STOCK` |
| `creer_facture_achat(session, fournisseur_id, numero_fourn, date, lignes, commande_id, notes)` | `MANAGE_STOCK` |
| `valider(session, facture_id)` | `MANAGE_STOCK` |
| `marquer_payee(session, facture_id, mode, reference)` | `MANAGE_STOCK` |
| `annuler(session, facture_id)` | `MANAGE_STOCK` |

### GUI

| Fenêtre | Description |
|---|---|
| `FactureAchatListWindow` | Table : N° fournisseur, notre N°, date, fournisseur, montant TTC, statut |
| `FactureAchatFormWindow` | Création/édition : sélection fournisseur, saisie lignes (picker pièces), date, écheance |
| `FactureAchatDetailWindow` | Détail en lecture ; boutons Valider / Marquer payée / Annuler |

**Lien avec Commande** : si la facture est liée à une `CommandeFournisseur`, les lignes sont pré-remplies
depuis la commande (modifiables avant validation).

### Sidebar

Ajouter un bouton « Fact. Ach. » (couleur `#8B4513`, icône "A") sous la section Stock,
avec `Permission.MANAGE_STOCK`.

### DB nouvelles tables

```
factures_achat
  id, fournisseur_id, numero_fournisseur, notre_numero, date_facture,
  date_echeance, statut, commande_id, notes, taux_tva, montant_ht, montant_ttc

lignes_achat
  id, facture_achat_id (FK), piece_id (FK), designation,
  quantite, prix_unitaire
```

---

## Feature 3 — Gestion des Charges du Garage

### Contexte

Loyer, électricité, salaires, assurances… Le patron veut un tableau de bord mensuel de ses charges
fixes et variables. Les charges payées alimentent un journal simple (pas de comptabilité double entrée).

### Domaine

#### `CategorieCharge` (StrEnum)

`LOYER | ELECTRICITE | EAU | SALAIRES | ASSURANCE | CARBURANT | MATERIEL | ENTRETIEN | AUTRE`

#### `PeriodiciteCharge` (StrEnum)

`UNIQUE | MENSUELLE | TRIMESTRIELLE | SEMESTRIELLE | ANNUELLE`

#### `ChargeGarage` (AggregateRoot)

| Champ | Type |
|---|---|
| `categorie` | CategorieCharge |
| `description` | str |
| `montant` | Decimal |
| `date_charge` | datetime |
| `date_echeance` | datetime \| None |
| `periodicite` | PeriodiciteCharge |
| `statut` | `SAISIE \| PAYEE \| ANNULEE` |
| `mode_paiement` | str \| None |
| `reference_document` | str |

**Règle** : une charge `MENSUELLE` peut générer une charge récurrente automatique pour le mois suivant
(bouton « Reconduire »).

#### Events domaine

```python
ChargeSaisie(charge_id, montant, categorie)
ChargePayee(charge_id, montant, mode_paiement)
ChargeAnnulee(charge_id)
```

### Application — `ChargeService`

| Méthode | Permission |
|---|---|
| `list_charges(session, periode_debut, periode_fin)` | `MANAGE_SETTINGS` |
| `creer_charge(session, ...)` | `MANAGE_SETTINGS` |
| `marquer_payee(session, charge_id, mode, reference)` | `MANAGE_SETTINGS` |
| `annuler(session, charge_id)` | `MANAGE_SETTINGS` |
| `reconduire(session, charge_id)` | `MANAGE_SETTINGS` |
| `total_charges_periode(session, debut, fin)` | `MANAGE_SETTINGS` |

### GUI

| Fenêtre | Description |
|---|---|
| `ChargesWindow` | Liste filtrable par mois/catégorie ; KPIs : total mois, total payé, total en attente |
| `ChargeFormWindow` | Saisie/édition d'une charge |

**Rapport** : « Bilan Charges vs CA » — charges du mois vs chiffre d'affaires facturé → dans le menu Rapports.

### Sidebar

Ajouter « Charges » (couleur `#795548`, icône "€") dans la section Facturation,
avec `Permission.MANAGE_SETTINGS`.

### DB nouvelle table

```
charges_garage
  id, categorie, description, montant, date_charge, date_echeance,
  periodicite, statut, mode_paiement, reference_document
```

---

## Feature 4 — Multi-Dossier / Multi-Instance (Sage-like)

### Contexte

Sage permet de créer un « nouveau dossier comptable » (= nouvelle base de données) pour :
- un **nouvel exercice** (2025, 2026…),
- une **nouvelle société** (client multi-site),
- une **copie de travail** à des fins de test.

Le démarrage de l'application affiche un **sélecteur de dossiers** si plusieurs bases existent,
exactement comme Sage au lancement.

### Architecture

#### Fichiers DB multiples

```
%USERPROFILE%\.garage_reparation\
  ├── garage.db                     ← dossier par défaut (migration transparente)
  ├── exercice_2025.db
  ├── exercice_2026.db
  ├── garage_agence_tunis.db
  └── dossiers.json                 ← index des dossiers connus
```

#### `dossiers.json` — index persisté

```json
[
  {
    "id": "uuid",
    "nom": "Exercice 2026",
    "chemin": "exercice_2026.db",
    "societe": "Garage Central Tunis",
    "cree_le": "2026-01-01T00:00:00",
    "dernier_acces": "2026-06-24T10:30:00"
  }
]
```

#### `DossierManager` (nouveau module `settings.py` ou `dossier_manager.py`)

```python
class DossierManager:
    def list_dossiers() -> list[DossierInfo]
    def creer_dossier(nom, societe, chemin_db) -> DossierInfo
        # 1. Crée le fichier .db
        # 2. Lance DatabaseInitializer (create_all + seed complet)
        # 3. Ajoute l'entrée dans dossiers.json
    def supprimer_dossier(id) -> None   # supprime l'entrée JSON (pas le fichier DB)
    def get_chemin_db(id) -> Path
```

#### Flux au démarrage

```
main.py
  ├── GarageApplication()
  ├── _check_licence()
  │
  ├── DossierManager.list_dossiers()
  │     ├── 0 ou 1 dossier  →  démarrage direct (comportement actuel)
  │     └── N > 1 dossiers  →  DossierSelectorDialog
  │                               └── sélection → résolution APP_DATA_DIR + DB_PATH
  │
  └── bootstrap(db_path) → AppContext
```

#### `DossierSelectorDialog`

Fenêtre de sélection en plein écran (avant login) :

```
┌─────────────────────────────────────────────────────────┐
│  Alfa Computers — Gestion Réparation Voiture            │
│  ─────────────────────────────────────────────────────  │
│  Sélectionnez un dossier ou créez-en un nouveau         │
│                                                         │
│  ┌───────────────────────────────────────┐              │
│  │ Exercice 2026  (Garage Central)       │ [Ouvrir]     │
│  │ Dernier accès : 24/06/2026 10:30      │              │
│  ├───────────────────────────────────────┤              │
│  │ Exercice 2025  (Garage Central)       │ [Ouvrir]     │
│  │ Dernier accès : 03/01/2026 09:00      │              │
│  └───────────────────────────────────────┘              │
│                                                         │
│  [+ Nouveau dossier]         [Parcourir…]  [Quitter]    │
└─────────────────────────────────────────────────────────┘
```

#### `NouveauDossierDialog`

Formulaire de création :

| Champ | Détail |
|---|---|
| Nom du dossier | ex. « Exercice 2027 » |
| Nom de la société | pré-rempli depuis la société courante (modifiable) |
| Fichier DB | chemin auto-suggéré dans `~/.garage_reparation/` (modifiable) |
| Copier depuis | None \| dossier existant (cloner le paramétrage sans les données) |

Cloner = copier `app_settings`, `societe`, `roles`, `users` — sans clients, véhicules, dossiers, factures.

#### Paramétrage — `AppSettings` étendu

```python
# settings.py — résolution dynamique :
def resolve_db_path(dossier_id: str | None) -> Path:
    if dossier_id:
        return DossierManager().get_chemin_db(dossier_id)
    return _resolve_app_data_dir() / "garage.db"   # comportement actuel
```

`bootstrap(db_path: str | None = None)` accepte un chemin explicite passé depuis `main.py`
après sélection du dossier.

#### Permissions

Aucune nouvelle permission — la création de dossiers est protégée par `Permission.MANAGE_DB_SNAPSHOTS`
(déjà réservée à `superadmin`).

#### Migration transparente

Si `dossiers.json` est absent → `DossierManager` l'initialise automatiquement avec une entrée
pointant vers `garage.db` existant. L'utilisateur ne voit aucun changement au premier démarrage.

---

## Feature 5 — Sidebar responsive (écrans 15")

### Problème

Sur un écran 1366 × 768 (15" standard) :
- Hauteur utile après chrome : ≈ 700 px
- 14 boutons actuels × 60 px = 840 px → débordement garanti

Avec Sprint 05 : +3 boutons (Fact. Ach., Charges, Numérot.) → 17 × 60 = 1020 px.

### Solution — Mode compact + scroll

#### Deux modes

| Mode | Hauteur bouton | Largeur sidebar | Icône | Texte |
|---|---|---|---|---|
| **Plein** (défaut ≥ 900 px) | 60 px | 88 px | 28 × 28 px | sous l'icône, 10 px |
| **Compact** (auto < 900 px) | 38 px | 52 px | 20 × 20 px | tooltip uniquement |

#### Comportement

1. Au démarrage : `screen_height = QApplication.primaryScreen().size().height()`
   - < 900 px → compact activé automatiquement
   - ≥ 900 px → plein
2. Bouton bascule `[◀]` / `[▶]` en tête de sidebar — toggle manuel.
3. Préférence persistée : `app_settings["sidebar.compact"]` = `"true"` / `"false"`.
4. Sidebar enveloppée dans `QScrollArea` (scroll vertical si contenu > hauteur disponible).

#### Changements dans `main_window.py`

```python
class _NavButton(QToolButton):
    def set_compact(self, compact: bool) -> None:
        if compact:
            self.setIconSize(QSize(20, 20))
            self.setFixedHeight(38)
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            self.setToolTip(self._label)
        else:
            self.setIconSize(QSize(28, 28))
            self.setFixedHeight(60)
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            self.setToolTip("")
```

```python
# Sidebar wrappée dans QScrollArea
scroll = QScrollArea()
scroll.setWidget(container)
scroll.setWidgetResizable(True)
scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
scroll.setFixedWidth(sidebar_width)
dock.setWidget(scroll)
```

---

## Feature 6 — Arabe & RTL (i18n)

### Contexte

L'application cible des garages tunisiens. Une interface en arabe (arabe tunisien / MSA) est
stratégiquement différenciante et répond aux exigences légales pour certains clients.
L'arabe est une langue **RTL (droite à gauche)** — Qt gère le retournement automatique de la mise en
page (`QApplication.setLayoutDirection(Qt.LayoutDirection.RightToLeft)`) mais plusieurs points
nécessitent un soin particulier.

### Architecture i18n existante

```
tools/i18n/tr.py          — tr(context, key) → QCoreApplication.translate()
resources/i18n/
  ├── fr.ts / fr.qm       — Français (langue par défaut, complète)
  └── (ar.ts / ar.qm)     ← à créer
```

### Ce qui est à ajouter

#### 1. Fichier de traduction arabe `ar.ts`

Généré avec `pylupdate6` depuis les sources (tous les appels `tr()`), traduit manuellement ou
via DeepL/Google Translate avec révision.

Priorité de traduction (ordre décroissant) :
1. Menus & titres de fenêtres
2. Libellés de champs de saisie
3. Messages d'erreur et confirmations
4. Rapports HTML (titre, sous-titre, en-têtes colonnes)

#### 2. Support RTL dans `app.py`

```python
def _apply_locale(self, locale_code: str) -> None:
    if locale_code == "ar":
        QApplication.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._load_translation("ar")
    else:
        QApplication.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self._load_translation("fr")
```

Appelé au démarrage depuis `app_settings["app.locale"]` et depuis `SettingsWindow` sans redémarrage
(les fenêtres MDI déjà ouvertes se retournent automatiquement via Qt).

#### 3. Police arabe

Ajouter `Amiri` ou `Cairo` (polices libres) dans `assets/fonts/` et les charger conditionnellement :

```python
if locale_code == "ar":
    QApplication.setFont(QFont("Cairo", 10))
```

Fallback : `"Segoe UI"` (Windows 10+ inclut des polices arabes correctes sous ce nom).

#### 4. QSS RTL

Certaines règles CSS Qt ne s'inversent pas automatiquement :
- `border-left` / `border-right` → inverser manuellement si le style est directionnel
- `padding-left` / `padding-right` dans `light.qss` → ajouter un bloc `[layoutDirection="RightToLeft"]` override

```css
/* light.qss — ajout bloc RTL */
QWidget[layoutDirection="2"] QGroupBox::title { /* 2 = RightToLeft */
    left: auto;
    right: 8px;
}
```

#### 5. Rapports HTML avec contenu arabe

Le moteur de rapport utilise `QTextBrowser` (HTML). Pour l'arabe :

```html
<!-- En-tête du rapport en mode AR -->
<html dir="rtl" lang="ar">
<body style="direction:rtl; font-family:'Cairo', 'Arial', sans-serif;">
```

Le `build_html()` dans `report_viewer_window.py` accepte un paramètre `direction: str = "ltr"`.

#### 6. Sélecteur de langue dans `SettingsWindow`

Onglet « Affichage » :

| Champ | Valeur |
|---|---|
| Langue de l'interface | Français / عربي (radio buttons) |
| Direction | Auto (déduite de la langue) |

Changement appliqué immédiatement (sans redémarrage) via `QApplication.setLayoutDirection`.

#### 7. Numéros localisés

Les numéros arabes orientaux (٠١٢٣…) sont optionnels et désactivés par défaut.
Ajouter une clé `app_settings["app.numerals"]` = `"western"` / `"eastern"`.
Le formatage monétaire TND reste inchangé (format français 3 décimales).

### Clés `app_settings` nouvelles

```
app.locale             "fr"         (fr | ar)
app.numerals           "western"    (western | eastern)
```

### Fichiers affectés

| Fichier | Modification |
|---|---|
| `tools/i18n/tr.py` | Inchangé — `QCoreApplication.translate()` supporte déjà n'importe quelle locale |
| `gui/app.py` | `_apply_locale()`, chargement police arabe |
| `assets/styles/light.qss` | Bloc RTL overrides |
| `gui/reports/report_viewer_window.py` | `build_html(direction=)` |
| `gui/admin/settings_window.py` | Onglet langue |
| `resources/i18n/ar.ts` | **À créer** (traductions arabes) |
| `assets/fonts/Cairo-Regular.ttf` | **À ajouter** (polices libres, licence OFL) |

### Pas de nouvelle table DB — uniquement `app_settings`

---

## Feature 7 — Report Designer (self-service, style Crystal Reports)

### Contexte

L'application génère des rapports HTML statiques codés en dur dans chaque `*_report_window.py`.
Un client veut personnaliser : logo, couleurs, champs affichés, ordre des colonnes, pied de page légal.
Le **Report Designer** est un éditeur de modèles de documents stockés dans des fichiers JSON,
chargés à la demande par le moteur de rapport existant.

### Architecture

#### Modèle de rapport — `ReportTemplate` (JSON)

```json
{
  "id": "uuid",
  "nom": "Facture Standard",
  "type_document": "facture",
  "version": 1,
  "is_default": true,
  "sections": {
    "header": {
      "show_logo": true,
      "logo_align": "left",
      "show_societe": true,
      "show_slogan": false,
      "couleur_bande": "#0055a5",
      "couleur_texte_bande": "#ffffff"
    },
    "info_document": {
      "champs": ["numero", "date_emission", "statut", "echeance"]
    },
    "client": {
      "champs": ["nom_prenom", "telephone", "adresse"],
      "titre": "FACTURÉ À"
    },
    "lignes": {
      "colonnes": [
        {"champ": "index",         "titre": "#",        "largeur": 30,  "align": "center"},
        {"champ": "designation",   "titre": "Désignation", "largeur": -1, "align": "left"},
        {"champ": "quantite",      "titre": "Qté",      "largeur": 50,  "align": "right"},
        {"champ": "prix_unitaire", "titre": "P.U.",     "largeur": 110, "align": "right"},
        {"champ": "montant",       "titre": "Total HT", "largeur": 110, "align": "right"}
      ]
    },
    "totaux": {
      "show_ht": true,
      "show_tva": true,
      "show_ttc": true,
      "show_paye": true,
      "show_reste": true
    },
    "footer": {
      "texte_legal": "Merci de votre confiance. Tout litige sera réglé devant les tribunaux compétents.",
      "show_page_number": true,
      "couleur": "#6E6E73"
    }
  },
  "css_custom": ""
}
```

Stockage : `%USERPROFILE%\.garage_reparation\report_templates\{type_document}\{id}.json`

Types de documents supportés : `facture | dossier | bon_travail | facture_achat | bilan_charges`

#### `ReportTemplateManager`

```python
class ReportTemplateManager:
    def list_templates(type_doc: str) -> list[ReportTemplateMeta]
    def get_template(id: str) -> ReportTemplate
    def save_template(t: ReportTemplate) -> None
    def delete_template(id: str) -> None
    def get_default(type_doc: str) -> ReportTemplate
    def set_default(type_doc: str, id: str) -> None
    def duplicate(id: str, new_nom: str) -> ReportTemplate
    def export_template(id: str, dest_path: Path) -> None   # sauvegarde JSON portabl
    def import_template(src_path: Path) -> ReportTemplate   # importe depuis fichier
```

#### Moteur de rendu adapté — `TemplateRenderer`

```python
class TemplateRenderer:
    def render_facture(template: ReportTemplate, facture: Facture, ctx: AppContext) -> str
    def render_dossier(template: ReportTemplate, dossier: DossierReparation, ctx) -> str
    def render_bon_travail(template: ReportTemplate, dossier, ctx) -> str
```

Le `TemplateRenderer` remplace les fonctions `_render()` codées en dur dans chaque
`*_report_window.py`. Les `_render()` existantes deviennent des wrappers :

```python
def _render(facture, ctx, session):
    template = ReportTemplateManager().get_default("facture")
    return TemplateRenderer().render_facture(template, facture, ctx)
```

Rétrocompatibilité totale : si aucun template n'est défini, le moteur utilise un template
par défaut embarqué (identique au rendu actuel).

### GUI — Report Designer

#### `ReportDesignerWindow` (MDI sub-window)

Interface en trois panneaux :

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Concepteur de Documents — Facture Standard                              │
├─────────────────┬──────────────────────────────┬─────────────────────────┤
│  MODÈLES        │  ÉDITEUR                      │  APERÇU                 │
│  ─────────────  │  ─────────────────────────── │  ─────────────────────  │
│  Facture Std ←  │  ▼ En-tête                   │  [Rendu HTML live]      │
│  Facture Pro    │    ☑ Logo    ○ Gauche ○ Droite│                         │
│  Facture Arabe  │    ☑ Société                  │  Alfa Computers         │
│  + Nouveau      │    ☐ Slogan                   │  ───────────────────    │
│  ─────────────  │    Couleur bande: [■ #0055a5] │  Facture N° F2026-0042  │
│  Dossier Std    │  ▼ Colonnes lignes            │  Date : 24/06/2026      │
│  BT Standard    │    [↑] # | Désignation |      │  ...                    │
│                 │    [↓] Qté | P.U. | Total     │                         │
│                 │    [+ Ajouter colonne]         │                         │
│                 │  ▼ Pied de page               │                         │
│                 │    [Texte légal ............]  │                         │
│                 │                               │                         │
│                 │  [Enregistrer] [Dupliquer]    │  [Imprimer] [PDF]       │
│                 │  [Exporter] [Importer] [Défaut]│                         │
└─────────────────┴──────────────────────────────┴─────────────────────────┘
```

**Aperçu en direct** : chaque modification dans l'éditeur met à jour le `QTextBrowser` dans les
500 ms (debounce avec `QTimer.singleShot(500, self._refresh_preview)`).

#### `ReportTemplatesListWindow`

Vue liste simple : nom du modèle, type, date de modification, par défaut (étoile).
Boutons : Nouveau, Modifier, Dupliquer, Exporter, Importer, Supprimer, Définir comme défaut.

### Permissions

| Action | Permission |
|---|---|
| Voir les modèles | `MANAGE_SETTINGS` |
| Créer / modifier | `MANAGE_SETTINGS` |
| Exporter / importer | `MANAGE_SETTINGS` |
| Supprimer | `MANAGE_SETTINGS` |

### Pas de nouvelle table DB

Les modèles sont des fichiers JSON dans `~/.garage_reparation/report_templates/`.
Avantages : portables, versionnables avec git, aucune migration DB.

### Fichiers nouveaux

| Fichier | Rôle |
|---|---|
| `tools/report_engine/template_model.py` | `ReportTemplate`, `ReportTemplateMeta` dataclasses |
| `tools/report_engine/template_manager.py` | `ReportTemplateManager` (CRUD fichiers JSON) |
| `tools/report_engine/template_renderer.py` | `TemplateRenderer` — HTML depuis template + données |
| `gui/reports/report_designer_window.py` | `ReportDesignerWindow` (3 panneaux) |
| `gui/reports/report_templates_list_window.py` | `ReportTemplatesListWindow` |

### Seed de templates par défaut

Au premier démarrage, si le répertoire `report_templates/` est vide, le moteur copie les templates
embarqués depuis `resources/report_templates/` (inclus dans le bundle PyInstaller) vers
`~/.garage_reparation/report_templates/`.

---

## Couche Application — récapitulatif

| Service | Permissions | Nouveau |
|---|---|---|
| `NumerotationService` | `MANAGE_SETTINGS` (config) | ✅ |
| `FactureAchatService` | `VIEW_STOCK`, `MANAGE_STOCK` | ✅ |
| `ChargeService` | `MANAGE_SETTINGS` | ✅ |
| `DossierManager` | (non-service, utilitaire `settings`) | ✅ |
| `ReportTemplateManager` | `MANAGE_SETTINGS` (via GUI seulement) | ✅ |
| `TemplateRenderer` | (tool, sans permission propre) | ✅ |

**Nouvelles permissions** :

```python
# À ajouter dans Permission (StrEnum)
MANAGE_DB_INSTANCES = auto()    # créer / supprimer des dossiers DB
```

Incluse dans `superadmin` uniquement (par défaut).

---

## GUI — récapitulatif fenêtres nouvelles

| Fenêtre | Module | Description |
|---|---|---|
| `NumerotationWindow` | `gui/admin/numerotation_window.py` | Onglet dans SettingsWindow |
| `FactureAchatListWindow` | `gui/stock/facture_achat_list_window.py` | Liste factures achat |
| `FactureAchatFormWindow` | `gui/stock/facture_achat_form_window.py` | Saisie/édition |
| `FactureAchatDetailWindow` | `gui/stock/facture_achat_detail_window.py` | Détail + actions |
| `ChargesWindow` | `gui/facturation/charges_window.py` | Liste + KPIs charges |
| `ChargeFormWindow` | `gui/facturation/charge_form_window.py` | Saisie/édition charge |
| `DossierSelectorDialog` | `gui/dossier_selector_dialog.py` | Sélecteur au démarrage |
| `NouveauDossierDialog` | `gui/dossier_selector_dialog.py` | Création nouveau dossier |
| `BilancChargesWindow` | `gui/reports/bilan_charges_window.py` | Rapport charges vs CA |
| `ReportDesignerWindow` | `gui/reports/report_designer_window.py` | Concepteur de documents |
| `ReportTemplatesListWindow` | `gui/reports/report_templates_list_window.py` | Gestion modèles |

---

## DB — récapitulatif schéma

### Nouvelles tables

```sql
CREATE TABLE factures_achat (
    id TEXT PRIMARY KEY,
    fournisseur_id TEXT NOT NULL,
    numero_fournisseur TEXT NOT NULL DEFAULT '',
    notre_numero TEXT UNIQUE NOT NULL,
    date_facture DATETIME NOT NULL,
    date_echeance DATETIME,
    statut TEXT NOT NULL DEFAULT 'saisie',
    commande_id TEXT,
    notes TEXT NOT NULL DEFAULT '',
    taux_tva REAL NOT NULL DEFAULT 19.0,
    montant_ht REAL NOT NULL DEFAULT 0,
    montant_ttc REAL NOT NULL DEFAULT 0
);

CREATE TABLE lignes_achat (
    id TEXT PRIMARY KEY,
    facture_achat_id TEXT NOT NULL REFERENCES factures_achat(id),
    piece_id TEXT NOT NULL REFERENCES pieces(id),
    designation TEXT NOT NULL,
    quantite INTEGER NOT NULL DEFAULT 1,
    prix_unitaire REAL NOT NULL
);

CREATE TABLE charges_garage (
    id TEXT PRIMARY KEY,
    categorie TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    montant REAL NOT NULL,
    date_charge DATETIME NOT NULL,
    date_echeance DATETIME,
    periodicite TEXT NOT NULL DEFAULT 'unique',
    statut TEXT NOT NULL DEFAULT 'saisie',
    mode_paiement TEXT,
    reference_document TEXT NOT NULL DEFAULT ''
);
```

### Pas de table pour les modèles de rapport

Les `ReportTemplate` sont des fichiers JSON — pas de table DB.

### Migrations `_COLUMN_MIGRATIONS`

Aucune colonne à ajouter sur des tables existantes — les nouvelles tables sont créées via `Base.metadata.create_all`.

### `app_settings` — nouvelles clés seed

```json
"settings": {
  "numerotation.facture.prefixe":          "F{ANNEE}-",
  "numerotation.facture.prochain":         "1",
  "numerotation.facture.longueur":         "4",
  "numerotation.facture.reset_annuel":     "true",
  "numerotation.facture.dernier_annee":    "2026",

  "numerotation.dossier.prefixe":          "REP-",
  "numerotation.dossier.prochain":         "1",
  "numerotation.dossier.longueur":         "4",
  "numerotation.dossier.reset_annuel":     "false",

  "numerotation.bon_travail.prefixe":      "BT{ANNEE}/",
  "numerotation.bon_travail.prochain":     "1",
  "numerotation.bon_travail.longueur":     "4",
  "numerotation.bon_travail.reset_annuel": "true",

  "numerotation.facture_achat.prefixe":    "FA-",
  "numerotation.facture_achat.prochain":   "1",
  "numerotation.facture_achat.longueur":   "4",
  "numerotation.facture_achat.reset_annuel": "false",

  "sidebar.compact":                       "false",
  "app.locale":                            "fr",
  "app.numerals":                          "western"
}
```

---

## Ordre d'implémentation recommandé

```
1. NumerotationService          (aucune dépendance externe)
   └── Mettre à jour seed_data.json (clés numerotation.*)
   └── Remplacer repo.next_numero() par NumerotationService
   └── NumerotationWindow (onglet dans SettingsWindow)

2. Sidebar responsive           (indépendant, rapide)
   └── _NavButton.set_compact()
   └── QScrollArea autour du container
   └── Bouton toggle + persistance app_settings

3. FactureAchat                 (dépend du stock existant)
   └── Domaine : FactureAchat, LigneAchat, events
   └── Infrastructure : FactureAchatModel, repo
   └── Service : FactureAchatService
   └── GUI : List + Form + Detail
   └── Sidebar + Menu Stock

4. ChargeGarage                 (indépendant du reste)
   └── Domaine : ChargeGarage, events
   └── Infrastructure : ChargeModel, repo
   └── Service : ChargeService
   └── GUI : ChargesWindow + ChargeFormWindow
   └── Rapport BilancCharges
   └── Sidebar + Menu Facturation

5. Multi-Dossier / DossierManager
   └── dossier_manager.py (DossierInfo, DossierManager)
   └── bootstrap() accepte db_path explicite
   └── DossierSelectorDialog + NouveauDossierDialog
   └── main.py : flux sélection avant login
   └── Migration transparente (dossiers.json auto-créé)

6. Report Designer              (dépend du moteur HTML existant)
   └── tools/report_engine/template_model.py
   └── tools/report_engine/template_manager.py
   └── tools/report_engine/template_renderer.py
   └── Seed templates par défaut dans resources/report_templates/
   └── ReportDesignerWindow + ReportTemplatesListWindow
   └── Wrappers dans *_report_window.py existants

7. Arabe & RTL                  (dépend de 6 — build_html direction)
   └── ar.ts — traduction (pylupdate6 + traduction manuelle)
   └── assets/fonts/Cairo-Regular.ttf
   └── app.py : _apply_locale()
   └── light.qss : bloc RTL
   └── report_viewer_window.py : build_html(direction=)
   └── SettingsWindow : onglet langue
   └── seed_data.json : clés app.locale + app.numerals
```

---

## Dépendances / Risques

| Risque | Mitigation |
|---|---|
| Doublon numéro si deux sessions simultanées | `NumerotationService.generer_numero` → `SELECT + UPDATE` dans une seule transaction SQLite avec `BEGIN EXCLUSIVE` |
| Annulation FactureAchat après validation (retour stock) | Vérifier que `sortir_stock` ne descend pas en dessous de 0 ; sinon bloquer l'annulation |
| Corruption `dossiers.json` | Lecture tolérante ; régénérer automatiquement depuis les `.db` du répertoire |
| Migration `garage.db` existant → entrée dans `dossiers.json` | `DossierManager.__init__` auto-import si `garage.db` présent et `dossiers.json` absent |
| Cloner un dossier copie les mdp en clair | bcrypt hash — OK, pas de fuite ; mais les utilisateurs gardent leurs mots de passe |
| RTL + QSS styles directionnels | Tester sur Windows en arabe ; `QApplication.setLayoutDirection` suffit dans 95% des cas |
| Rendu HTML arabe dans `QTextBrowser` | `QTextBrowser` supporte les scripts arabes via Qt HTML renderer ; les polices embarquées garantissent l'affichage |
| Template JSON corrompu | `ReportTemplateManager` valide le JSON au chargement ; en cas d'erreur, bascule sur le template par défaut embarqué |
| Trop de champs configurables → UX complexe | Limiter le Report Designer aux sections listées ; ne pas exposer le CSS brut sauf dans un onglet « Avancé » caché |
