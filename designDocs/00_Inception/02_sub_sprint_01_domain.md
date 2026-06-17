# 02 — Sub-Sprint 01 : Couche Domaine (DDD Kernel)

**Sprint parent :** `01_sprint.md`
**Statut :** ✅ Implémenté (scaffold)

---

## Objectif

Implémenter la couche domaine pure (aucune dépendance externe), les agrégats, les événements et les invariants métier.

---

## Architecture de la couche

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 320" width="700" height="320">
  <rect width="700" height="320" fill="#f8f8f8" rx="8"/>
  <!-- Shared Kernel -->
  <rect x="10" y="10" width="680" height="60" rx="5" fill="#e8f4fd" stroke="#0055a5" stroke-width="1.5"/>
  <text x="350" y="30" text-anchor="middle" font-family="monospace" font-size="12" font-weight="bold" fill="#0055a5">Shared Kernel</text>
  <text x="350" y="50" text-anchor="middle" font-family="monospace" font-size="10" fill="#555">Entity · AggregateRoot · ValueObject · DomainEvent · Repository (ABC) · Exceptions · Money(TND)</text>

  <!-- BC boxes -->
  <rect x="10"  y="90" width="155" height="210" rx="5" fill="#fff3e0" stroke="#f57c00" stroke-width="1.5"/>
  <text x="87"  y="110" text-anchor="middle" font-weight="bold" font-size="11" fill="#f57c00">Planification</text>
  <text x="87"  y="128" text-anchor="middle" font-size="9" fill="#555">Client</text>
  <text x="87"  y="142" text-anchor="middle" font-size="9" fill="#555">Vehicule</text>
  <text x="87"  y="156" text-anchor="middle" font-size="9" fill="#555">RendezVous ★</text>
  <text x="87"  y="170" text-anchor="middle" font-size="9" fill="#555">FicheReception</text>

  <rect x="175" y="90" width="165" height="210" rx="5" fill="#e8f5e9" stroke="#2e7d32" stroke-width="2"/>
  <text x="257" y="110" text-anchor="middle" font-weight="bold" font-size="11" fill="#2e7d32">Atelier ★★</text>
  <text x="257" y="128" text-anchor="middle" font-size="9" fill="#555">DossierReparation ★★★</text>
  <text x="257" y="142" text-anchor="middle" font-size="9" fill="#555">StatutDossier (enum)</text>
  <text x="257" y="156" text-anchor="middle" font-size="9" fill="#555">LigneDiagnostic</text>
  <text x="257" y="170" text-anchor="middle" font-size="9" fill="#555">OperationMecanique</text>
  <text x="257" y="184" text-anchor="middle" font-size="9" fill="#555">PieceRequise</text>

  <rect x="350" y="90" width="155" height="210" rx="5" fill="#fce4ec" stroke="#c62828" stroke-width="1.5"/>
  <text x="427" y="110" text-anchor="middle" font-weight="bold" font-size="11" fill="#c62828">Stock</text>
  <text x="427" y="128" text-anchor="middle" font-size="9" fill="#555">Piece ★</text>
  <text x="427" y="142" text-anchor="middle" font-size="9" fill="#555">Fournisseur</text>
  <text x="427" y="156" text-anchor="middle" font-size="9" fill="#555">CommandeFournisseur</text>

  <rect x="515" y="90" width="175" height="210" rx="5" fill="#ede7f6" stroke="#4527a0" stroke-width="1.5"/>
  <text x="602" y="110" text-anchor="middle" font-weight="bold" font-size="11" fill="#4527a0">Facturation</text>
  <text x="602" y="128" text-anchor="middle" font-size="9" fill="#555">Facture ★</text>
  <text x="602" y="142" text-anchor="middle" font-size="9" fill="#555">SessionCaisse ★</text>
  <text x="602" y="156" text-anchor="middle" font-size="9" fill="#555">CreditClient</text>
  <text x="602" y="170" text-anchor="middle" font-size="9" fill="#555">Paiement (TND/EUR/USD/CAD)</text>

  <text x="350" y="315" text-anchor="middle" font-size="9" fill="#808080">★ Aggregate Root   ★★ Core BC   ★★★ Central State Machine</text>
</svg>
```

---

## Machine à états : DossierReparation

```
CREE → DIAGNOSTIC → EN_ATTENTE_DEVIS → EN_COURS → QUALITE → PRET → CLOTURE
```

| Transition | Méthode | Règle métier |
|---|---|---|
| CREE → DIAGNOSTIC | `lancer_diagnostic()` | — |
| DIAGNOSTIC → EN_ATTENTE_DEVIS | `soumettre_au_devis()` | ≥1 panne identifiée |
| EN_ATTENTE_DEVIS → EN_COURS | `approuver_devis(id)` | Règle Strict-Accord |
| EN_COURS → EN_ATTENTE_DEVIS | `signaler_nouvelle_panne()` | Règle Avenant-Obligatoire |
| EN_COURS → QUALITE | `terminer_reparation()` | 0 tâche incomplète |
| QUALITE → PRET | `valider_controle_qualite()` | Règle Garantie-Qualité |
| PRET → CLOTURE | `generer_facture(id, ttc)` | QualitéValidée obligatoire |

---

## Devise par défaut : TND (Dinar Tunisien)

- `Money(amount, currency="TND")` — format : `1 234,567 DT`
- Autres devises supportées : EUR (€), USD ($), CAD (CA$)
- La devise est configurable par Société et par Facture.

---

## Fichiers implémentés

- `src/garage_app/domain/shared/` — Kernel complet
- `src/garage_app/domain/planification/` — Client, Vehicule, RendezVous
- `src/garage_app/domain/atelier/` — DossierReparation + tous les events
- `src/garage_app/domain/stock/` — Piece + events
- `src/garage_app/domain/facturation/` — Facture, SessionCaisse, CreditClient
- `src/garage_app/domain/auth/` — User, Permission (RBAC), UserSession
- `src/garage_app/domain/societe/` — Societe (singleton)
