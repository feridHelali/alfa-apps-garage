# Release Rebuild Guide
## Gestion Réparation Voiture — Alfa Computers Apps

**Author:** Ferid HELALI — helaliferid@gmail.com — +216 22 45 79 16  
**Site:** https://alfa-computers.com

---

## Every-Release Checklist

Follow these steps in order each time you cut a new release.

---

### 1. Bump the version

Edit **`pyproject.toml`** — one line:
```toml
version = "1.1.0"   # ← new version
```

The version propagates everywhere automatically:
- `build.ps1` reads it from `pyproject.toml` at build time
- Inno Setup receives it as `/DAppVersion=...`
- `settings.py` exposes it as `APP_VERSION` at runtime

---

### 2. Update the changelog / release notes

Document what changed in your commit message or a `CHANGELOG.md`.  
Keep it brief: one line per user-visible change.

---

### 3. (Optional) Regenerate licence keys

Only needed if you want a new batch of keys for this release:
```powershell
# Delete old batch first so the build step creates a fresh one
Remove-Item licences\licence_keys.txt

# Or generate a named batch directly:
python scripts/generate_licences.py --count 200 --out licences/v1.1.0_keys.txt
```

**Keep `licences/` out of version control** — treat it like a secrets folder.

---

### 4. Run the full build

```powershell
# Standard x64 release (recommended)
.\build.ps1

# With explicit version (overrides pyproject.toml)
.\build.ps1 -Version 1.1.0

# Both architectures
.\build.ps1 -Arch both

# Clean rebuild (removes dist\ and build\ first)
.\build.ps1 -Clean

# All flags combined
.\build.ps1 -Version 1.1.0 -Arch both -Clean
```

What the build does automatically:
| Step | Script | Output |
|---|---|---|
| Render SVG → ICO + wizard BMPs | `scripts/prepare_assets.py` | `assets/icons/app_icon.ico`, `installer/*.bmp` |
| Generate licence keys (if missing) | `scripts/generate_licences.py` | `licences/licence_keys.txt` |
| Bundle app + deps | PyInstaller + `garage_app.spec` | `dist/x64/GarageReparation/` |
| Build wizard installer | Inno Setup + `installer/setup.iss` | `installer/Output/GarageReparationSetup_<ver>_x64.exe` |

---

### 5. Test the installer

Run the produced installer on a **clean machine** (or a VM snapshot):

```
installer\Output\GarageReparationSetup_1.1.0_x64.exe
```

**Wizard pages to verify:**

| Page | What to check |
|---|---|
| Welcome | Correct version shown |
| Licence Key | Enter a key from `licences/licence_keys.txt` — Next only enables when format is valid |
| Install Dir | Default is `%ProgramFiles%\Alfa Computers Apps\...` |
| Data Dir | Default is `%USERPROFILE%\.garage_reparation` |
| Components | DB Browser for SQLite listed as optional |
| Finish | "Launch application" checkbox works |

**After install — verify in the app:**
1. Licence dialog does NOT appear (key was written by installer)
2. Login screen loads
3. Login with `admin` / `Admin@2025!`
4. All menus accessible

---

### 6. Tag the release in Git

```bash
git tag -a v1.1.0 -m "Release 1.1.0"
git push origin v1.1.0
```

---

### 7. Distribute

Ship the installer file:
```
installer\Output\GarageReparationSetup_1.1.0_x64.exe   (32 MB approx)
```

Send matching licence keys from `licences/licence_keys.txt` to each customer.

---

## Prerequisites (one-time setup)

| Tool | Install |
|---|---|
| Python 3.13 x64 | Ships with project venv — `.venv\Scripts\python.exe` |
| PyInstaller | Already in `.venv` via `pip install -e ".[build]"` |
| Inno Setup 6 | https://jrsoftware.org/isinfo.php (free) |
| DB Browser for SQLite (optional) | `.\scripts\download_dbbrowser.ps1` |

---

## Troubleshooting

### `py -3.13-64` not found
`build.ps1` now prefers `.venv\Scripts\python.exe` automatically — no action needed.

### PyInstaller missing module warning
Add to `hiddenimports` in `garage_app.spec` and rebuild.

### Inno Setup "file not found" error
Run `.\scripts\prepare_assets.py` first to regenerate `app_icon.ico` and the wizard BMPs, or use `.\build.ps1` which does this automatically.

### Licence key rejected in installer
Confirm the key is from `licences/licence_keys.txt` — copy/paste exactly, format `ALFA-XXXX-XXXX-XXXX-XXXX`.

### App shows licence dialog after install
The installer writes `licence.key` to the app directory. Check that `{app}\licence.key` exists and contains a valid key.

---

## File Map

```
build.ps1                        ← entry point for every release build
garage_app.spec                  ← PyInstaller bundle definition
installer/
  setup.iss                      ← Inno Setup wizard script
  wizard_image.bmp               ← generated — do not edit manually
  wizard_small_image.bmp         ← generated — do not edit manually
  tools/DBBrowserForSQLite/      ← optional; populate with download_dbbrowser.ps1
  Output/
    GarageReparationSetup_*.exe  ← final installer — ship this

scripts/
  prepare_assets.py              ← SVG → ICO + BMP (run once per logo change)
  generate_licences.py           ← key batch generator
  download_dbbrowser.ps1         ← fetch DB Browser portable (run once)

assets/icons/app_icon.ico        ← generated — committed after first run
licences/licence_keys.txt        ← PRIVATE — never commit
src/garage_app/
  settings.py                    ← APP_VERSION constant + data dir resolver
  domain/societe/licence.py      ← key algorithm (validate_key / generate_key)
  gui/licence_dialog.py          ← activation dialog (first-launch fallback)
```
