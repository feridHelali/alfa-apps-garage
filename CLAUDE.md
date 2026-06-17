# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Desktop application for managing an auto repair garage ("Garage de Réparation de Voiture"), built with **Python 3.13 / PyQt / H2 database**. Architecture follows DDD, TDD, and SOLID principles. The app is a Multi-Document Interface (MDI) targeting Windows (32/64-bit installer).

## Commands

```bash
# Run the application
python main.py

# Install dependencies (once added)
pip install -e .
```

Python version is pinned to **3.13** (see `.python-version`).

## Architecture

The system is modeled as a classic kernel-layered architecture:

```
Domain Layer (Kernel)   — pure business logic, aggregates, domain events, value objects
GUI Layer               — PyQt MDI windows, forms, dialogs (Master/Detail pattern for 1:N relations)
Persistence Layer       — H2 database adapter; repository implementations
Tools/Utilities         — shared helpers, i18n (fr/en), report engine
```

### Core Domain Model

The central aggregate is **`DossierRéparation` (RepairOrder)** — a state machine:

```
Créé → Diagnostic → EnAttenteDevis → EnCours → Qualité → Prêt → Clôturé
```

It owns three internal entity lists: `LignesDiagnostic`, `OpérationsMécaniques`, and `PiècesRequises`.

Key invariants enforced inside the aggregate:
- Total dossier amount = sum of parts + labor lines.
- Status cannot advance to `Prêt` while any task remains incomplete.
- `OrdreDeRéparation` cannot be created unless `StatutDevis == DevisApprouvé`.
- `FactureGénérée` requires prior `ContrôleQualitéValidé`.
- Vehicle keys cannot be released until `PaiementEncaissé` (except fleet/30-day accounts).

### Bounded Contexts (planned modules)

| Context | Responsibility |
|---|---|
| Planification & Réception | Agenda, clients, vehicle intake |
| Diagnostic & Atelier | Tech sheets, mechanic assignment, task tracking |
| Approvisionnement (Stock) | Parts catalog, stock alerts, supplier orders |
| Facturation & Comptabilité | Quotes, taxes, invoices, payment terminals |

### Cross-cutting Concerns

- **Authentication / RBAC**: roles are `superadmin`, `admin`, `technician`.
- **i18n**: French/English, user-configurable.
- **Reports**: built-in generator (Crystal Report style), formats stored as JSON, supports invoices and reports.
- **Société management**: company identity, logo, license info — acts as the application license anchor.
- **DB Snapshots**: managed by superadmin.
- **Seed DB**: required for first-run bootstrapping.

## Design Documents

`designDocs/00_Inception/` contains:
- `event_storming.md` — full domain event map, commands, actors, and business rules.
- `sprint.md` — inception sprint goals and feature backlog.

Reference these when implementing domain logic to stay aligned with the agreed event model.
