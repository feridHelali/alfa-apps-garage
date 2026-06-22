# =============================================================================
# build.ps1 — Gestion Réparation Voiture v1.0.0
# Alfa Computers Apps
#
# Usage:
#   .\build.ps1                          # x64 only, version from pyproject.toml
#   .\build.ps1 -Arch both               # x64 + x86
#   .\build.ps1 -Arch x86 -Version 1.0.0
#   .\build.ps1 -SkipAssets              # skip SVG → ICO/BMP step
#
# Prerequisites:
#   • Python 3.13 x64 in PATH (or via py launcher)
#   • Python 3.13 x86 for -Arch x86 or -Arch both  (py -3.13-32)
#   • pyinstaller in the venv / pip install pyinstaller
#   • Inno Setup 6  (ISCC in PATH or default install paths)
#   • UPX optional  (speeds up EXE compression)
# =============================================================================

param(
    [ValidateSet("x64", "x86", "both")]
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
function Write-OK([string]$msg)   { Write-Host "  ✓ $msg" -ForegroundColor Green  }
function Write-Warn([string]$msg) { Write-Host "  ⚠ $msg" -ForegroundColor Cyan   }
function Write-Fail([string]$msg) { Write-Host "  ✗ $msg" -ForegroundColor Red    }

function Find-Iscc {
    $fromPath = (Get-Command iscc -ErrorAction SilentlyContinue)?.Source
    if ($fromPath) { return $fromPath }
    @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe",
        "C:\Program Files (x86)\Inno Setup 6\iscc.exe",
        "C:\Program Files\Inno Setup 6\iscc.exe"
    ) | ForEach-Object { if (Test-Path $_) { return $_ } }
    return $null
}

function Find-Python([string]$bits) {
    # Try py launcher first (most reliable)
    $pyTag = if ($bits -eq "32") { "-3.13-32" } else { "-3.13-64" }
    $py = (Get-Command py -ErrorAction SilentlyContinue)?.Source
    if ($py) {
        $out = & py $pyTag -c "import sys; print(sys.version)" 2>&1
        if ($LASTEXITCODE -eq 0) { return @("py", $pyTag) }
    }
    # Fallback: plain python (only valid for x64 builds)
    if ($bits -eq "64") {
        $python = (Get-Command python -ErrorAction SilentlyContinue)?.Source
        if ($python) { return @($python) }
    }
    return $null
}

function Invoke-Python([string[]]$interpreter, [string[]]$args) {
    if ($interpreter[0] -eq "py") {
        $allArgs = @($interpreter[1]) + $args
        & py @allArgs
    } else {
        & $interpreter[0] @args
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

$banner = "Gestion Réparation Voiture  v$Version  [$Arch]"
Write-Host ("=" * ($banner.Length + 4)) -ForegroundColor Cyan
Write-Host "  $banner"  -ForegroundColor Cyan
Write-Host ("=" * ($banner.Length + 4)) -ForegroundColor Cyan

# ---------------------------------------------------------------------------
# Step 0: Prepare assets (SVG → ICO, BMP)
# ---------------------------------------------------------------------------
Write-Step "0" "Preparing assets…"
if ($SkipAssets) {
    Write-Warn "Skipped (--SkipAssets)."
} else {
    $py64 = Find-Python "64"
    if (-not $py64) {
        Write-Warn "Python x64 not found — skipping asset + licence generation."
    } else {
        if (Test-Path "assets\icons\app_icon.svg") {
            $rc = Invoke-Python $py64 @("scripts\prepare_assets.py")
            if ($rc -ne 0) { throw "prepare_assets.py failed (exit $rc)" }
            Write-OK "SVG assets prepared (ico + bmp)."
        } else {
            Write-Warn "assets\icons\app_icon.svg not found — skipping icon generation."
        }

        # Generate licence keys if not already present
        if (-not (Test-Path "licences\licence_keys.txt")) {
            $rc = Invoke-Python $py64 @("scripts\generate_licences.py")
            if ($rc -ne 0) { throw "generate_licences.py failed (exit $rc)" }
            Write-OK "100 licence keys generated → licences\licence_keys.txt"
        } else {
            Write-Warn "licences\licence_keys.txt already exists — skipping keygen (delete to regenerate)."
        }
    }
}

# ---------------------------------------------------------------------------
# Step 1: Determine architectures to build
# ---------------------------------------------------------------------------
$archs = if ($Arch -eq "both") { @("x64", "x86") } else { @($Arch) }

# ---------------------------------------------------------------------------
# Step 2: Clean old dist/build (if requested or both arches)
# ---------------------------------------------------------------------------
if ($Clean) {
    Write-Step "1" "Cleaning dist\ and build\ …"
    foreach ($a in $archs) {
        if (Test-Path "dist\$a")  { Remove-Item -Recurse -Force "dist\$a"  }
        if (Test-Path "build\$a") { Remove-Item -Recurse -Force "build\$a" }
    }
    Write-OK "Done."
}

# ---------------------------------------------------------------------------
# Step 3: PyInstaller per architecture
# ---------------------------------------------------------------------------
$builtArchs = @()

foreach ($a in $archs) {
    Write-Step "PyInstaller" "Building $a …"

    $bits = if ($a -eq "x64") { "64" } else { "32" }
    $interpreter = Find-Python $bits
    if (-not $interpreter) {
        Write-Warn "Python $bits-bit not found — skipping $a build."
        continue
    }

    # Verify the interpreter is actually the right bitness
    $detectedBits = Invoke-Python $interpreter @("-c", "import struct; print(struct.calcsize('P')*8)") 2>&1
    if ($detectedBits -ne $bits) {
        Write-Warn "Interpreter reports ${detectedBits}-bit, expected ${bits}-bit — skipping $a."
        continue
    }

    $distPath  = "dist\$a"
    $buildPath = "build\$a"

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

    Write-OK "$a build → $distPath\GarageReparation"
    $builtArchs += $a
}

if ($builtArchs.Count -eq 0) {
    throw "No architectures were built — check Python installations."
}

# ---------------------------------------------------------------------------
# Step 4: Inno Setup per built architecture
# ---------------------------------------------------------------------------
if ($SkipInstaller) {
    Write-Step "Installer" "Skipped (--SkipInstaller)."
} else {
    $iscc = Find-Iscc
    if (-not $iscc) {
        Write-Warn "Inno Setup (ISCC) not found — skipping installer build."
        Write-Warn "Install from: https://jrsoftware.org/isinfo.php"
    } else {
        Write-Step "Inno Setup" "Building installer(s) with $iscc …"
        New-Item -ItemType Directory -Force "installer\Output" | Out-Null

        foreach ($a in $builtArchs) {
            Write-Host "  Building $a installer…" -ForegroundColor White

            $rc = & $iscc `
                "installer\setup.iss" `
                "/DAppVersion=$Version" `
                "/DArch=$a"
            if ($rc -ne 0) { throw "Inno Setup $a failed (exit $rc)" }

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
