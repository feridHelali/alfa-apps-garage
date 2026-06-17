# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Gestion Réparation Voiture** — Desktop MDI app for auto repair garage management.
Brand: **Alfa Computers Apps** | Stack: **Python 3.13 / PyQt6 / SQLite (WAL)** | Target: **Windows 32/64-bit**
Architecture: **DDD + TDD + SOLID**, strict layer isolation.

## Commands

```bash
# Install (editable, src layout)
pip install -e ".[dev]"

# Run
python main.py

# Tests
pytest                        # all tests
pytest tests/domain/          # domain layer only
pytest -k test_dossier        # single test pattern
pytest --tb=short -q          # compact output

# Lint / format
ruff check src tests
ruff format src tests

# Type check
mypy src
```

Python version is pinned to **3.13** (see `.python-version`).

## Source layout

```
src/garage_app/
├── domain/           # Pure Python — NO external imports
│   ├── shared/       # Entity, AggregateRoot, DomainEvent, Money(TND), exceptions
│   ├── auth/         # User, Permission (StrEnum), UserSession, ROLE_PERMISSIONS
│   ├── societe/      # Singleton company info + licence
│   ├── planification/# Client, Vehicule, RendezVous
│   ├── atelier/      # DossierReparation (central state machine), events
│   ├── stock/        # Piece, Fournisseur, CommandeFournisseur
│   ├── facturation/  # Facture, SessionCaisse, CreditClient
│   └── audit/        # AuditEntry, LogCategory, LogLevel
├── infrastructure/
│   ├── db/           # engine.py (WAL, FK ON), session.py, models, initializer, seed_runner
│   ├── repositories/ # SqlAlchemy*Repository (implement domain ABCs)
│   └── events/       # InMemoryEventBus
├── application/      # Services with @require_permission decorator
│   ├── audit_service.py      # Write/read forensic audit log
│   ├── db_management_service.py  # VACUUM, integrity, snapshots (superadmin)
│   └── ...
├── gui/
│   ├── app.py        # GarageApplication — sets font, loads QSS, sets org name
│   ├── main_window.py# QMainWindow + QMdiArea, RBAC-filtered menus
│   ├── auth/         # LoginWindow (QDialog, SVG logo)
│   ├── planification/
│   ├── atelier/      # DossierListWindow, DossierWindow (tabs)
│   ├── stock/
│   ├── facturation/
│   └── admin/        # SocieteWindow, SnapshotWindow, SettingsWindow,
│                     # DbManagementWindow, AuditLogWindow
├── tools/
│   ├── i18n/tr.py    # tr(context, key) → QCoreApplication.translate()
│   └── report_engine/# TemplateLoader, DataBinder, (QtPainter renderer WIP)
├── settings.py       # AppSettings dataclass, DB_PATH = ~/.garage_reparation/garage.db
└── bootstrap.py      # AppContext DI wiring
```

## Key Architecture Rules

**Layer dependencies (strict — never break these):**
- `domain/` imports only stdlib
- `infrastructure/` imports `domain/` + SQLAlchemy
- `application/` imports `domain/` + `infrastructure/`
- `gui/` imports `application/` + `domain/` + PyQt6; NEVER imports SQLAlchemy
- `tools/` imports only stdlib + PyQt6; NO domain imports

**RBAC — two layers, both mandatory:**
1. `@require_permission(Permission.X)` on application service methods (first arg after `self` must be `UserSession`)
2. `action.setVisible(session.can(Permission.X))` in GUI menus (client-side UX guard)

**WindowRegistry:** `WindowRegistry.open_or_activate(WindowClass, ctx, session)` — ensures one MDI sub-window per type.

**Domain events:** `AggregateRoot._raise_event()` + `pull_events()` → published to `InMemoryEventBus` by service layer after `repo.save()`.

## Default credentials (seed)

| User | Password | Role |
|---|---|---|
| `admin` | `Admin@2025!` | admin |
| `superadmin` | `SuperAdmin@2025!` | superadmin |

## Currency

Default: **TND (Tunisian Dinar)** — `Money(amount, currency="TND")`.
Format (fr): `1 234,567 DT` (3 decimal places for millimes).
Other supported: EUR (€), USD ($), CAD (CA$).

## Audit & DB Management

- `AuditService` — write: call-anywhere; read: superadmin only (`Permission.MANAGE_USERS`)
- `DbManagementService` — VACUUM, WAL checkpoint, integrity check, snapshot CRUD (`Permission.MANAGE_DB_SNAPSHOTS`)
- GUI: `AdminMenu → Journal d'audit` / `Gestion de la base de données`
- All DB actions are logged to `audit_log` table (category `DB`)

## Theme

`assets/styles/light.qss` — Windows-classic gray palette.
- Chrome: `#d4d0c8`, widget bg: `#f0f0f0`, accent: `#0055a5`, table alt rows: `#f4f2ee`
- App font: Segoe UI 10pt (fallback: Arial)

## Brand

Alfa Computers Apps — SVG logo at `assets/brand/alfa_computers_logo.svg`.
Tagline: "Solutions de Gestion sur Mesure".

## Design Documents

```
designDocs/
├── 00_Inception/
│   ├── 01_sprint.md                    Sprint 01 goals
│   ├── 02_sub_sprint_01_domain.md      Domain layer details + state machine
│   ├── 03_sub_sprint_02_infrastructure.md
│   ├── 04_sub_sprint_03_presentation.md MDI GUI pattern
│   ├── 05_sub_sprint_04_tools_reports.md
│   └── event_storming.md
├── 01_Sprint_Stock_Fournisseurs/
│   └── 01_sprint_stock_fournisseurs.md  Sprint 02 plan
└── 02_Sprint_Facturation_Caisse/
    └── 01_sprint_facturation_caisse.md  Sprint 03 plan
```

## Installer

Build with `build.ps1`:
1. PyInstaller → `dist/garage_reparation/` (onedir)
2. Inno Setup → `installer/Output/GarageReparationSetup_x64.exe`
