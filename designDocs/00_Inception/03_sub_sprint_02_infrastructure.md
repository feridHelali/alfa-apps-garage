# 03 — Sub-Sprint 02 : Couche Infrastructure

**Sprint parent :** `01_sprint.md`
**Statut :** ✅ Implémenté (scaffold)

---

## Objectif

Implémenter la persistance (SQLAlchemy/SQLite), les repositories, l'event bus et le bootstrap DI.

---

## Architecture de persistance

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 280" width="700" height="280">
  <rect width="700" height="280" fill="#f8f8f8" rx="8"/>

  <!-- Application layer -->
  <rect x="10" y="10" width="680" height="40" rx="4" fill="#e3f2fd" stroke="#1565c0" stroke-width="1"/>
  <text x="350" y="35" text-anchor="middle" font-family="monospace" font-size="11" fill="#1565c0">Application Services (DossierService, FactureService…) — Ports (Repository ABCs)</text>

  <!-- Arrow down -->
  <line x1="350" y1="50" x2="350" y2="70" stroke="#666" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Infrastructure -->
  <rect x="10" y="70" width="680" height="120" rx="4" fill="#fff8e1" stroke="#f57f17" stroke-width="1.5"/>
  <text x="350" y="92" text-anchor="middle" font-weight="bold" font-size="12" fill="#f57f17">Infrastructure Layer</text>

  <!-- DB -->
  <rect x="30"  y="100" width="200" height="75" rx="3" fill="#fff" stroke="#ccc"/>
  <text x="130" y="118" text-anchor="middle" font-size="10" font-weight="bold">DB (SQLite / SQLAlchemy)</text>
  <text x="130" y="133" text-anchor="middle" font-size="9" fill="#555">engine.py — WAL mode, FK ON</text>
  <text x="130" y="147" text-anchor="middle" font-size="9" fill="#555">session.py — scoped context mgr</text>
  <text x="130" y="161" text-anchor="middle" font-size="9" fill="#555">initializer.py → seed_runner.py</text>

  <!-- Repos -->
  <rect x="250" y="100" width="200" height="75" rx="3" fill="#fff" stroke="#ccc"/>
  <text x="350" y="118" text-anchor="middle" font-size="10" font-weight="bold">Repositories (Adapters)</text>
  <text x="350" y="133" text-anchor="middle" font-size="9" fill="#555">SqlAlchemyClientRepository</text>
  <text x="350" y="147" text-anchor="middle" font-size="9" fill="#555">SqlAlchemyDossierRepository</text>
  <text x="350" y="161" text-anchor="middle" font-size="9" fill="#555">SqlAlchemy*Repository × 10</text>

  <!-- Event bus -->
  <rect x="470" y="100" width="200" height="75" rx="3" fill="#fff" stroke="#ccc"/>
  <text x="570" y="118" text-anchor="middle" font-size="10" font-weight="bold">Event Bus</text>
  <text x="570" y="133" text-anchor="middle" font-size="9" fill="#555">InMemoryEventBus</text>
  <text x="570" y="147" text-anchor="middle" font-size="9" fill="#555">subscribe / publish / publish_all</text>
  <text x="570" y="161" text-anchor="middle" font-size="9" fill="#555">Handlers: stock check on devis OK</text>

  <!-- SQLite file -->
  <rect x="270" y="210" width="160" height="50" rx="4" fill="#e8eaf6" stroke="#3949ab"/>
  <text x="350" y="232" text-anchor="middle" font-size="10" font-weight="bold" fill="#3949ab">garage.db (SQLite)</text>
  <text x="350" y="248" text-anchor="middle" font-size="9" fill="#555">~/.garage_reparation/garage.db</text>
  <line x1="130" y1="175" x2="290" y2="210" stroke="#999" stroke-width="1" stroke-dasharray="4"/>
  <line x1="350" y1="190" x2="350" y2="210" stroke="#999" stroke-width="1" stroke-dasharray="4"/>

  <defs><marker id="arr" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">
    <path d="M0,0 L8,4 L0,8 Z" fill="#666"/>
  </marker></defs>
</svg>
```

---

## Schéma tables principales

| Table | Description |
|---|---|
| `users` + `roles` | Auth RBAC |
| `societe` | Singleton entreprise (licence) |
| `clients` + `vehicules` | 1:N |
| `dossiers_reparation` | Aggregate root central |
| `lignes_diagnostic` | N:1 dossier |
| `operations_mecaniques` | N:1 dossier |
| `pieces_requises` | N:1 dossier |
| `pieces` + `fournisseurs` | Catalogue stock |
| `devis` + `factures` + `lignes_facture` | Facturation |
| `report_templates` | JSON templates rapports |
| `app_settings` | Clé/valeur paramètres |
| `snapshots` | Historique snapshots BDD |

---

## Seed au premier lancement

1. `DatabaseInitializer.initialize()` détecte si `users` existe → sinon crée tout
2. `SeedRunner` charge `resources/seed/seed_data.json`
3. Insère : rôles + permissions, user `admin/Admin@2025!`, Société démo, 2 templates rapports
4. **Idempotent** : skip si déjà présent
