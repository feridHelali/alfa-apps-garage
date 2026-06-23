# =============================================================================
# build.ps1 -- Gestion Reparation Voiture
# Alfa Computers Apps
#
# Usage:
#   .\build.ps1                          # x64, version from pyproject.toml
#   .\build.ps1 -Version 1.0.0
#   .\build.ps1 -SkipAssets              # skip SVG -> ICO/BMP step
#
# Note: x86 is not supported -- PyQt6 / Qt6 dropped 32-bit entirely.
#
# Prerequisites:
#   - Python 3.13 x64 in PATH (or via py launcher)
#   - pyinstaller in the venv / pip install pyinstaller
#   - Inno Setup 6  (ISCC in PATH or default install paths)
#   - UPX optional  (speeds up EXE compression)
# =============================================================================

param(
    [ValidateSet("x64")]
    [string]$Arch    = "x64",

    [string]$Version = "",         # default: read from pyproject.toml

    [switch]$SkipAssets,           # skip prepare_assets.py + generate_licences.py
    [switch]$SkipInstaller,        # PyInstaller only, skip Inno Setup
    [switch]$Clean                 # force clean dist/build dirs before building
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
function Write-Step([string]$n, [string]$msg) {
    Write-Host "`n[$n] $msg" -ForegroundColor Yellow
}
function Write-OK([string]$msg)   { Write-Host "  [OK]   $msg" -ForegroundColor Green }
function Write-Warn([string]$msg) { Write-Host "  [WARN] $msg" -ForegroundColor Cyan  }
function Write-Fail([string]$msg) { Write-Host "  [FAIL] $msg" -ForegroundColor Red   }

function Find-Iscc {
    $isccCmd = Get-Command iscc -ErrorAction SilentlyContinue
    if ($isccCmd) { return $isccCmd.Source }
    foreach ($p in @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe",
        "C:\Program Files (x86)\Inno Setup 6\iscc.exe",
        "C:\Program Files\Inno Setup 6\iscc.exe"
    )) { if (Test-Path $p) { return $p } }
    return $null
}

function Find-Python {
    # Returns [PSCustomObject]@{Exe=...; Tag=...} or $null.
    # PSCustomObject avoids PowerShell's single-element array unwrapping.
    $venvPy = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPy) {
        return [PSCustomObject]@{ Exe = $venvPy; Tag = $null }
    }
    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) {
        & py -3.13-64 -c "import sys; print(sys.version)" 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            return [PSCustomObject]@{ Exe = "py"; Tag = "-3.13-64" }
        }
    }
    return $null
}

function Invoke-Python($interpreter, [string[]]$scriptArgs) {
    if ($interpreter.Exe -eq "py") {
        & py $interpreter.Tag @scriptArgs | Out-Host
    } else {
        & $interpreter.Exe @scriptArgs | Out-Host
    }
    return $LASTEXITCODE
}

# ---------------------------------------------------------------------------
# Resolve version from pyproject.toml if not supplied
# ---------------------------------------------------------------------------
if (-not $Version) {
    $toml = Get-Content "pyproject.toml" -Raw
    if ($toml -match 'version\s*=\s*"([^"]+)"') {
        $Version = $Matches[1]
    } else {
        throw "Cannot parse version from pyproject.toml"
    }
}

$banner = "Gestion Reparation Voiture  v$Version  [$Arch]"
Write-Host ("=" * ($banner.Length + 4)) -ForegroundColor Cyan
Write-Host "  $banner"  -ForegroundColor Cyan
Write-Host ("=" * ($banner.Length + 4)) -ForegroundColor Cyan

# ---------------------------------------------------------------------------
# Step 0: Prepare assets (SVG -> ICO, BMP)
# ---------------------------------------------------------------------------
Write-Step "0" "Preparing assets..."
if ($SkipAssets) {
    Write-Warn "Skipped (-SkipAssets)."
} else {
    $py64 = Find-Python
    if (-not $py64) {
        Write-Warn "Python x64 not found -- skipping asset + licence generation."
    } else {
        if (Test-Path "assets\icons\app_icon.svg") {
            $rc = Invoke-Python $py64 @("scripts\prepare_assets.py")
            if ($rc -ne 0) { throw "prepare_assets.py failed (exit $rc)" }
            Write-OK "SVG assets prepared (ico + bmp)."
        } else {
            Write-Warn "assets\icons\app_icon.svg not found -- skipping icon generation."
        }

        # Generate licence keys if not already present
        if (-not (Test-Path "licences\licence_keys.txt")) {
            $rc = Invoke-Python $py64 @("scripts\generate_licences.py")
            if ($rc -ne 0) { throw "generate_licences.py failed (exit $rc)" }
            Write-OK "100 licence keys generated -> licences\licence_keys.txt"
        } else {
            Write-Warn "licences\licence_keys.txt already exists -- skipping keygen (delete to regenerate)."
        }
    }
}

# ---------------------------------------------------------------------------
# Step 1: Clean old dist/build (if requested)
# ---------------------------------------------------------------------------
if ($Clean) {
    Write-Step "1" "Cleaning dist\ and build\ ..."
    if (Test-Path "dist\x64")  { Remove-Item -Recurse -Force "dist\x64"  }
    if (Test-Path "build\x64") { Remove-Item -Recurse -Force "build\x64" }
    Write-OK "Done."
}

# ---------------------------------------------------------------------------
# Step 2: PyInstaller
# ---------------------------------------------------------------------------
$builtArchs = @()

foreach ($a in @("x64")) {
    Write-Step "PyInstaller" "Building $a ..."

    $interpreter = Find-Python
    if (-not $interpreter) {
        throw "Python x64 not found -- install Python 3.13 x64 or create the .venv."
    }

    # Verify the interpreter is 64-bit
    if ($interpreter.Exe -eq "py") {
        $detectedBits = ((& py $interpreter.Tag -c "import struct; print(struct.calcsize('P')*8)") -join "").Trim()
    } else {
        $detectedBits = ((& $interpreter.Exe -c "import struct; print(struct.calcsize('P')*8)") -join "").Trim()
    }
    if ($detectedBits -ne "64") {
        throw "Interpreter reports ${detectedBits}-bit -- expected 64-bit. Check your Python installation."
    }

    $distPath    = "dist\x64"
    $distOutPath = "dist\x64\GarageReparation"
    $buildPath   = "build\x64"

    # Remove previous output folder so PyInstaller never hits a locked-file error
    if (Test-Path $distOutPath) {
        try {
            Remove-Item -Recurse -Force $distOutPath -ErrorAction Stop
        } catch {
            throw "Cannot delete $distOutPath -- close GarageReparation.exe and retry. ($($_.Exception.Message))"
        }
    }

    New-Item -ItemType Directory -Force $distPath  | Out-Null
    New-Item -ItemType Directory -Force $buildPath | Out-Null

    $pyiArgs = @(
        "-m", "PyInstaller",
        "garage_app.spec",
        "--distpath", $distPath,
        "--workpath", $buildPath,
        "--noconfirm"
    )

    $rc = Invoke-Python $interpreter $pyiArgs
    if ($rc -ne 0) { throw "PyInstaller $a failed (exit $rc)" }

    Write-OK "$a build -> $distPath\GarageReparation"
    $builtArchs += $a
}

if ($builtArchs.Count -eq 0) {
    throw "No architectures were built -- check Python installations."
}

# ---------------------------------------------------------------------------
# Step 4: Inno Setup per built architecture
# ---------------------------------------------------------------------------
if ($SkipInstaller) {
    Write-Step "Installer" "Skipped (-SkipInstaller)."
} else {
    $iscc = Find-Iscc
    if (-not $iscc) {
        Write-Warn "Inno Setup (ISCC) not found -- skipping installer build."
        Write-Warn "Install from: https://jrsoftware.org/isinfo.php"
    } else {
        Write-Step "Inno Setup" "Building installer(s) with $iscc ..."
        New-Item -ItemType Directory -Force "installer\Output" | Out-Null

        foreach ($a in $builtArchs) {
            Write-Host "  Building $a installer..." -ForegroundColor White

            & $iscc "installer\setup.iss" "/DAppVersion=$Version" "/DArch=$a"
            if ($LASTEXITCODE -ne 0) { throw "Inno Setup $a failed (exit $LASTEXITCODE)" }

            $outFile = "installer\Output\GarageReparationSetup_${Version}_${a}.exe"
            if (Test-Path $outFile) {
                $size = [math]::Round((Get-Item $outFile).Length / 1MB, 1)
                Write-OK "$outFile  (${size} MB)"
            } else {
                Write-OK "$a installer built."
            }
        }
    }
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "  BUILD COMPLETE  v$Version" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Cyan

foreach ($a in $builtArchs) {
    Write-Host "  App ($a) :  dist\$a\GarageReparation\GarageReparation.exe" -ForegroundColor White
    if (-not $SkipInstaller) {
        $out = "installer\Output\GarageReparationSetup_${Version}_${a}.exe"
        if (Test-Path $out) {
            Write-Host "  Setup($a):  $out" -ForegroundColor White
        }
    }
}
Write-Host ""
