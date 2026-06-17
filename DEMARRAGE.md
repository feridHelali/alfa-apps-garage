# Démarrage — Gestion Réparation Voiture

Guide pour exécuter et tester l'application avant de générer l'installeur.

---

## Prérequis

| Outil | Version | Téléchargement |
|---|---|---|
| Python | **3.13** | https://www.python.org/downloads/ |
| uv (gestionnaire de paquets) | ≥ 0.5 | `pip install uv` ou https://docs.astral.sh/uv/ |
| Git | — | https://git-scm.com/ |

> Sur Windows, vérifier que Python 3.13 est dans le `PATH`.

---

## 1. Installation des dépendances

```powershell
# Cloner ou dézipper le projet, puis :
cd D:\68_Gestion_Reparation_Voiture_Mahmoud_Baklouti

# Installer l'environnement virtuel + toutes les dépendances (prod + dev)
uv sync --all-extras
```

Le premier `uv sync` prend ~2-3 minutes (téléchargement de PyQt6 ~90 Mo).
Les suivants sont instantanés grâce au cache.

---

## 2. Lancer l'application

```powershell
uv run python main.py
```

**Au premier lancement :**
- La base de données `%USERPROFILE%\.garage_reparation\garage.db` est créée automatiquement.
- Les données initiales (rôles, utilisateur admin, société démo, templates rapports) sont insérées.

**Identifiants par défaut :**

| Utilisateur | Mot de passe | Rôle |
|---|---|---|
| `admin` | `Admin@2025!` | Administrateur |
| `superadmin` | `SuperAdmin@2025!` | Super-Administrateur |

---

## 3. Exécuter les tests unitaires

```powershell
# Tous les tests
uv run python -m pytest

# Tests d'un module spécifique
uv run python -m pytest tests/domain/
uv run python -m pytest tests/application/

# Test unique
uv run python -m pytest tests/domain/test_dossier_reparation.py -k test_full_happy_path

# Sortie compacte
uv run python -m pytest -q --tb=short
```

**Résultat attendu : 50 passed**

### Couverture des tests

| Module | Tests | Ce qui est couvert |
|---|---|---|
| `domain/atelier` | 8 | Machine à états DossierReparation (happy path + invariants) |
| `domain/facturation` | 4 | Calculs montants, paiements, double-paiement |
| `domain/shared` | 5 | Money (TND/EUR), Immatriculation SIV |
| `application/audit` | 9 | AuditService (écriture + lecture avec contrôle d'accès) |
| `application/db_mgmt` | 12 | DbManagementService (stats, VACUUM, snapshots, RBAC) |
| `application/rbac` | 3 | Décorateur @require_permission |
| `tools/report_engine` | 5 | TemplateLoader round-trip, DataBinder |

---

## 4. Inspecter la base de données

Pendant le développement, utilisez **DB Browser for SQLite** pour inspecter la BDD directement :

```
Chemin BDD : %USERPROFILE%\.garage_reparation\garage.db
```

**Téléchargement :** https://sqlitebrowser.org/dl/  
Choisir la version **Portable** (pas d'installation nécessaire).

---

## 5. Vérification rapide avant build

```powershell
# 1. Tests : tous verts
uv run python -m pytest -q

# 2. Lint (aucune erreur critique)
uv run ruff check src tests

# 3. Démarrage de l'application
uv run python main.py
```

Si l'application démarre et affiche la fenêtre de connexion, l'environnement est prêt pour le build.

---

## 6. Générer l'installeur Windows

> Voir `build.ps1` et `installer\setup.iss` pour les détails.

Prérequis supplémentaires : **Inno Setup 6** (https://jrsoftware.org/isinfo.php)

```powershell
.\build.ps1
# → installer\Output\GarageReparationSetup_0.1.0_x64.exe
```

---

## Structure de l'environnement de développement

```
D:\68_Gestion_Reparation_Voiture_Mahmoud_Baklouti\
├── .venv\              ← Environnement virtuel (créé par uv sync)
├── src\garage_app\     ← Code source
├── tests\              ← Tests pytest (50 tests)
├── designDocs\         ← Documentation architecture et sprints
├── assets\             ← Thème QSS, logo SVG, icônes
├── resources\          ← Seed JSON, i18n .ts
├── main.py             ← Point d'entrée
├── pyproject.toml      ← Configuration projet
└── DEMARRAGE.md        ← Ce fichier
```
