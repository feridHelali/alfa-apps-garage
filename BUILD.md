# Build Guide — Gestion Réparation Voiture v1.0.0

**Alfa Computers Apps** — Ferid HELALI  
Contact: helaliferid@gmail.com | +216 22 45 79 16  
Site: https://alfa-computers.com

---

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python 3.13 x64 | 3.13+ | For x64 build + asset generation |
| Python 3.13 x86 | 3.13+ | For x86 build only (`py -3.13-32`) |
| PyInstaller | ≥ 6.10 | `pip install pyinstaller` |
| Inno Setup 6 | 6.x | https://jrsoftware.org/isinfo.php |
| UPX (optional) | any | Speeds up EXE compression |

Install Python deps:
```powershell
pip install -e ".[dev,build]"
```

---

## Quick Start

```powershell
# x64 release (default)
.\build.ps1

# x64 + x86 (requires 32-bit Python installed)
.\build.ps1 -Arch both

# Custom version
.\build.ps1 -Version 1.0.0 -Arch x64

# Skip asset regeneration (faster rebuilds)
.\build.ps1 -SkipAssets

# App bundle only, no Inno Setup
.\build.ps1 -SkipInstaller

# Clean everything before build
.\build.ps1 -Clean
```

---

## Build Steps (what build.ps1 does)

### Step 0 — Prepare Assets
Runs `scripts/prepare_assets.py` using PyQt6 to render SVGs:

| Output | Source | Size |
|---|---|---|
| `assets/icons/app_icon.ico` | `assets/icons/app_icon.svg` | 16–256 px multi-size |
| `installer/wizard_image.bmp` | `assets/brand/alfa_computers_logo.svg` | 164×314 (Inno wizard panel) |
| `installer/wizard_small_image.bmp` | same | 55×55 (Inno top-right) |

Also runs `scripts/generate_licences.py` if `licences/licence_keys.txt` does not exist.

### Step 1 — PyInstaller (per architecture)

```
pyinstaller garage_app.spec
  --distpath dist\x64          # or dist\x86
  --workpath build\x64
  --noconfirm
```

Output: `dist\x64\GarageReparation\GarageReparation.exe`

The spec bundles:
- `assets/` — QSS stylesheet, SVG icons, brand logo
- `resources/` — seed data JSON, i18n TS files
- Hidden imports: `sqlalchemy.dialects.sqlite`, `bcrypt`, PyQt6 SVG/Print modules

### Step 2 — Inno Setup (per architecture)

```
iscc installer\setup.iss /DAppVersion=1.0.0 /DArch=x64
```

Output: `installer/Output/GarageReparationSetup_1.0.0_x64.exe`

---

## Installer Wizard Pages

The installer presents the following pages in order:

1. **Welcome** — app name, version, publisher
2. **Licence Key** — user enters `ALFA-XXXX-XXXX-XXXX-XXXX`; validated offline via CRC32 checksum
3. **Select Destination Directory** — default `%ProgramFiles%\Alfa Computers Apps\Gestion Réparation Voiture`
4. **Select Data Directory** — default `%USERPROFILE%\.garage_reparation`; chosen path written to `data_dir.cfg`
5. **Select Components** — Main app (fixed) + DB Browser for SQLite (optional)
6. **Select Additional Tasks** — Desktop shortcut, startup entry
7. **Ready to Install**
8. **Installing…**
9. **Finish** — option to launch immediately

On finish, the installer writes:
- `{app}\licence.key` — the entered licence key (app skips its own activation dialog)
- `{app}\data_dir.cfg` — chosen data directory path (app reads at startup)

---

## Licence Key System

### Format
```
ALFA-G1-G2-G3-CHCK
```
- `G1`, `G2`, `G3`: 4 random uppercase alphanumeric characters each
- `CHCK`: last 4 hex characters of `CRC32(G1+G2+G3)` — tamper-evident offline checksum

### Validation
Both the installer (Pascal/Inno) and the application (Python) validate the checksum independently — no server required.

### Generating Keys
```powershell
python scripts/generate_licences.py             # 100 keys → licences/licence_keys.txt
python scripts/generate_licences.py --count 500 --out licences/batch2.txt
```

Generated keys are in `licences/licence_keys.txt`. **Keep this file private.**

### App Activation Flow
1. App starts → checks `licence.key` next to EXE (bundled) or project root (dev)
2. If valid → proceed to login
3. If missing/invalid → show `LicenceDialog` asking for key entry
4. On correct entry → writes `licence.key` and proceeds

---

## DB Browser for SQLite (optional installer component)

The installer includes DB Browser for SQLite as an optional component. To include it:

```powershell
# Download and extract portable version automatically:
.\scripts\download_dbbrowser.ps1

# Then rebuild the installer:
.\build.ps1 -SkipAssets
```

Manual alternative: download portable ZIP from https://sqlitebrowser.org/dl/ and extract to `installer/tools/DBBrowserForSQLite/`.

When included, it installs to `{app}\tools\DBBrowserForSQLite\` and gets Start Menu + optional desktop shortcuts.

---

## Data Directory

The application stores all persistent data under a single directory:

```
%USERPROFILE%\.garage_reparation\     (default)
├── garage.db                          SQLite database (WAL mode)
└── snapshots\                         Database snapshots (admin feature)
```

This path is configurable via the installer. The chosen path is written to `{app}\data_dir.cfg`. If the file does not exist, the app falls back to the default.

---

## Architecture Notes

| Build | Python | Installer flag | Runs on |
|---|---|---|---|
| x64 | `py -3.13-64` | `ArchitecturesInstallIn64BitMode=x64compatible` | Windows x64 only |
| x86 | `py -3.13-32` | *(none — 32-bit runs on both)* | Windows x86 + x64 via WoW64 |

---

## Output Files

```
dist\
  x64\GarageReparation\GarageReparation.exe     Application bundle
  x86\GarageReparation\GarageReparation.exe

installer\Output\
  GarageReparationSetup_1.0.0_x64.exe           Windows installer
  GarageReparationSetup_1.0.0_x86.exe

licences\
  licence_keys.txt                               100 generated keys (PRIVATE)

assets\icons\app_icon.ico                        Generated app icon
installer\wizard_image.bmp                       Installer wizard panel
installer\wizard_small_image.bmp                 Installer small image
```

---

## Sprint 03 — Delivered

| # | Item | Status |
|---|---|---|
| 1 | Version bumped to 1.0.0 | Done |
| 2 | Multi-arch build (x64 + x86 via `-Arch both`) | Done |
| 3 | `build.ps1` with `-Arch`, `-Version`, `-Clean`, `-SkipAssets`, `-SkipInstaller` | Done |
| 4 | SVG → ICO (multi-size) + wizard BMP via `prepare_assets.py` | Done |
| 5 | Inno Setup modern wizard with Alfa logo | Done |
| 6 | Installer: custom installation directory selection | Done |
| 7 | Installer: custom data directory selection | Done |
| 8 | Installer: licence key page with offline CRC32 validation | Done |
| 9 | Licence key algorithm (`ALFA-G1-G2-G3-CRC`) + 100 keys generated | Done |
| 10 | App licence activation dialog (`LicenceDialog`) | Done |
| 11 | `data_dir.cfg` + `settings.py` bundled-path resolver | Done |
| 12 | DB Browser for SQLite optional component + download helper | Done |
| 13 | `scripts/download_dbbrowser.ps1` portable DB Browser fetch | Done |
| 14 | Publisher contact info in installer (Ferid HELALI, email, phone, site) | Done |
