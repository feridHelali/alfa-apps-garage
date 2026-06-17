# 04 — Sub-Sprint 03 : Couche Présentation (PyQt6 MDI)

**Sprint parent :** `01_sprint.md`
**Statut :** ✅ Scaffold implémenté — détail des fenêtres à compléter (Sprint 02)

---

## Architecture MDI

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 340" width="700" height="340">
  <rect width="700" height="340" fill="#f0f0f0" rx="6"/>

  <!-- Main window chrome -->
  <rect x="10" y="10" width="680" height="320" rx="4" fill="#d4d0c8" stroke="#808080" stroke-width="2"/>

  <!-- Title bar -->
  <rect x="10" y="10" width="680" height="24" rx="4" fill="#0055a5"/>
  <text x="350" y="26" text-anchor="middle" font-size="11" fill="white" font-weight="bold">Gestion Réparation Voiture — Alfa Computers Apps</text>

  <!-- Menu bar -->
  <rect x="10" y="34" width="680" height="20" fill="#d4d0c8" stroke="#a0a0a0" stroke-width="0.5"/>
  <text x="30"  y="48" font-size="9" fill="#1a1a1a">Réception</text>
  <text x="100" y="48" font-size="9" fill="#1a1a1a">Atelier</text>
  <text x="155" y="48" font-size="9" fill="#1a1a1a">Stock</text>
  <text x="200" y="48" font-size="9" fill="#1a1a1a">Facturation</text>
  <text x="270" y="48" font-size="9" fill="#1a1a1a">Administration</text>
  <text x="370" y="48" font-size="9" fill="#1a1a1a">Fenêtres</text>

  <!-- Toolbar -->
  <rect x="10" y="54" width="680" height="22" fill="#d4d0c8" stroke="#a0a0a0" stroke-width="0.5"/>
  <rect x="16" y="57" width="50" height="16" rx="2" fill="#e0dcd4" stroke="#a0a0a0"/>
  <text x="41"  y="68" text-anchor="middle" font-size="8">Clients</text>
  <rect x="72" y="57" width="54" height="16" rx="2" fill="#e0dcd4" stroke="#a0a0a0"/>
  <text x="99" y="68" text-anchor="middle" font-size="8">Dossiers</text>
  <rect x="132" y="57" width="40" height="16" rx="2" fill="#e0dcd4" stroke="#a0a0a0"/>
  <text x="152" y="68" text-anchor="middle" font-size="8">Stock</text>
  <rect x="178" y="57" width="50" height="16" rx="2" fill="#e0dcd4" stroke="#a0a0a0"/>
  <text x="203" y="68" text-anchor="middle" font-size="8">Factures</text>

  <!-- MDI area -->
  <rect x="14" y="80" width="672" height="225" fill="#c8c0b4"/>

  <!-- Sub-window 1: Clients -->
  <rect x="20" y="88" width="300" height="160" fill="#f8f8f8" stroke="#808080" stroke-width="2"/>
  <rect x="20" y="88" width="300" height="18" fill="#0055a5"/>
  <text x="170" y="100" text-anchor="middle" font-size="9" fill="white" font-weight="bold">Clients</text>
  <rect x="24" y="110" width="140" height="130" fill="#fff" stroke="#c0c0c0"/>
  <text x="94" y="124" text-anchor="middle" font-size="8" font-weight="bold">Liste (Master)</text>
  <rect x="168" y="110" width="148" height="130" fill="#f4f2ee" stroke="#c0c0c0"/>
  <text x="242" y="124" text-anchor="middle" font-size="8" font-weight="bold">Détail (Form)</text>

  <!-- Sub-window 2: Dossiers -->
  <rect x="200" y="130" width="320" height="165" fill="#f8f8f8" stroke="#808080" stroke-width="2"/>
  <rect x="200" y="130" width="320" height="18" fill="#0055a5"/>
  <text x="360" y="142" text-anchor="middle" font-size="9" fill="white" font-weight="bold">Dossier Réparation — AB-123-CD</text>
  <!-- Status badge -->
  <rect x="208" y="154" width="80" height="14" rx="6" fill="#198754"/>
  <text x="248" y="164" text-anchor="middle" font-size="8" fill="white">Prêt</text>
  <!-- Tabs -->
  <rect x="208" y="173" width="60" height="12" fill="#0055a5" rx="2"/>
  <text x="238" y="182" text-anchor="middle" font-size="7" fill="white">Diagnostic</text>
  <rect x="272" y="173" width="60" height="12" fill="#d4d0c8" rx="2"/>
  <text x="302" y="182" text-anchor="middle" font-size="7">Opérations</text>
  <rect x="336" y="173" width="50" height="12" fill="#d4d0c8" rx="2"/>
  <text x="361" y="182" text-anchor="middle" font-size="7">Pièces</text>

  <!-- Status bar -->
  <rect x="10" y="305" width="680" height="18" fill="#d4d0c8" stroke="#a0a0a0" stroke-width="0.5"/>
  <text x="20"  y="317" font-size="8" fill="#404040">Prêt</text>
  <text x="580" y="317" font-size="8" fill="#404040">Super Administrateur [SUPERADMIN]</text>
</svg>
```

---

## Pattern Master/Detail (1:N)

```
QMdiSubWindow
└── MasterDetailWidget (QSplitter)
    ├── Master (SearchableTableWidget — QTableView + QLineEdit recherche)
    └── Detail (QFormLayout avec champs de saisie)
```

Sélection d'une ligne master → signal `currentRowChanged` → refresh du panneau détail.

## WindowRegistry

Garantit **une seule instance** par type de fenêtre MDI.
`open_or_activate(WindowClass, ctx, session)` réactive l'existante au lieu d'en ouvrir une deuxième.

## Thème

Fichier : `assets/styles/light.qss`
Palette Windows-classic : `#f0f0f0` fond, `#d4d0c8` chrome, `#0055a5` accent bleu.

## Login

- `LoginWindow(QDialog)` — logo SVG Alfa Computers + champs username/password
- Signal `logged_in(UserSession)` → `MainWindow` construit avec la session
- Credentials par défaut seed : `admin` / `Admin@2025!`
