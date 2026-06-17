# build.ps1 — Build Windows installer for Gestion Réparation Voiture
# Prerequisites: PyInstaller, Inno Setup (iscc in PATH)
# Usage: .\build.ps1

param(
    [string]$Version = "0.1.0"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "=== Gestion Réparation Voiture — Build $Version ===" -ForegroundColor Cyan

# 1. Clean
Write-Host "`n[1/3] Cleaning..." -ForegroundColor Yellow
if (Test-Path dist) { Remove-Item -Recurse -Force dist }
if (Test-Path build) { Remove-Item -Recurse -Force build }

# 2. PyInstaller
Write-Host "`n[2/3] Running PyInstaller..." -ForegroundColor Yellow
pyinstaller garage_app.spec --noconfirm
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed (exit $LASTEXITCODE)" }

# 3. Inno Setup
Write-Host "`n[3/3] Running Inno Setup..." -ForegroundColor Yellow
$iscc = (Get-Command iscc -ErrorAction SilentlyContinue)?.Source
if (-not $iscc) {
    # Common install paths
    $candidates = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    )
    $iscc = ($candidates | Where-Object { Test-Path $_ } | Select-Object -First 1)
}
if (-not $iscc) { throw "Inno Setup (iscc) not found. Install from https://jrsoftware.org/isinfo.php" }

& $iscc "installer\setup.iss" "/DAppVersion=$Version"
if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed (exit $LASTEXITCODE)" }

Write-Host "`n=== Build complete ===" -ForegroundColor Green
Write-Host "Installer: installer\Output\GarageReparationSetup_${Version}_x64.exe" -ForegroundColor Green
