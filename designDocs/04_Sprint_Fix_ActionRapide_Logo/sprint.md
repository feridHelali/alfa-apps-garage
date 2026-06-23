# Sprint 04 — Fix Action Rapide + Logo Polish

**Date:** 2026-06-23  
**Status:** Done

---

## Goals

1. Fix DB insertion crash when generating a Facture from **Bon de Travail Rapide** (Action Rapide).
2. Improve logo rendering in the **Login window** (crisp SVG).
3. Robustify invoice number sequencing.

---

## Bugs Fixed

### Bug 1 — `NOT NULL constraint failed: factures.date_emission`

**Root cause:** `Facture.emettre()` never set `date_emission`, leaving it `None`.  
`facture_repository.save()` relied on SQLAlchemy's deferred Python-side `default=lambda: datetime.now()`,
which does not fire reliably on all SQLAlchemy/SQLite version combos when the attribute is explicitly
`None` at INSERT time.

**Fix (two locations):**

- `domain/facturation/facture.py` — `emettre()` now sets `self.date_emission = datetime.now()`.
- `infrastructure/repositories/facture_repository.py` — `save()` INSERT branch now passes
  `date_emission=f.date_emission or datetime.now(timezone.utc)` explicitly to `FactureModel(...)`.

### Bug 2 — `UNIQUE constraint failed: factures.numero` (potential)

**Root cause:** `next_numero()` used `COUNT(*) + 1`.  
If any facture row was deleted (or a previous INSERT was rolled back after the numero was generated),
`COUNT` under-counts and the generated numero collides with an already-existing row.

**Fix:** `next_numero()` now queries all `F<year>-NNNN` values for the current year, parses the
numeric suffix, and returns `max + 1`. Gaps in the sequence are harmless; uniqueness is guaranteed.

---

## Improvement — Login Window Logo

**Before:** `QPixmap(svg_path)` — Qt's generic pixmap loader produces a blurry or empty image
for SVG files at small sizes.

**After:** `QSvgRenderer` renders the SVG directly to a 220×72 `QPixmap` with antialiasing,
identical to the approach already used in `splash_screen.py`.  
Dialog size adjusted to 380×440 to accommodate the wider logo area.

---

## Files Changed

| File | Change |
|---|---|
| `src/garage_app/domain/facturation/facture.py` | `emettre()` sets `self.date_emission` |
| `src/garage_app/infrastructure/repositories/facture_repository.py` | explicit `date_emission` in INSERT; MAX-based `next_numero()` |
| `src/garage_app/gui/auth/login_window.py` | SVG logo via `QSvgRenderer`; dialog 380×440 |
| `designDocs/04_Sprint_Fix_ActionRapide_Logo/sprint.md` | this file |

---

## How to Build the Installer (cross-reference)

See `designDocs/03_Multi_architecture_installer/sprint.md` for the installer sprint goals.  
The build script is `build.ps1` at the project root.

**Quick steps:**
```powershell
# 1. Ensure PyInstaller is installed in the venv
pip install pyinstaller

# 2. Run the build script (produces 32-bit AND 64-bit installers)
.\build.ps1

# Output: installer/Output/GarageReparationSetup_x64.exe  (and _x86.exe)
```

The script:
1. Calls PyInstaller with `garage_reparation.spec` → `dist/garage_reparation/` (onedir bundle)
2. Calls Inno Setup (`iscc`) with `installer/garage_reparation.iss` → final `.exe` wizard installer
3. Includes the Alfa Computers logo in the installer wizard pages and icons

> If you need to build for both 32-bit and 64-bit, run the script once in a 32-bit Python venv and once in a 64-bit Python venv, or set the `TARGET_ARCH` env var as documented in `build.ps1`.
