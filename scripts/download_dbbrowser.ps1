# download_dbbrowser.ps1
# Downloads DB Browser for SQLite portable and extracts it for the installer.
# Run once from the project root before building:
#   .\scripts\download_dbbrowser.ps1

param(
    [string]$Version = "3.13.1"
)

$destDir = "installer\tools\DBBrowserForSQLite"
$zipUrl  = "https://github.com/sqlitebrowser/sqlitebrowser/releases/download/v$Version/DB.Browser.for.SQLite-v$Version-win64.zip"
$zipPath = "$env:TEMP\DBBrowser_$Version.zip"

Write-Host "Downloading DB Browser for SQLite v$Version ..." -ForegroundColor Cyan

if (-not (Test-Path $destDir)) {
    New-Item -ItemType Directory -Force $destDir | Out-Null
}

try {
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing
} catch {
    Write-Host "Download failed: $_" -ForegroundColor Red
    Write-Host "Download manually from: https://sqlitebrowser.org/dl/" -ForegroundColor Yellow
    Write-Host "Extract to: $destDir" -ForegroundColor Yellow
    exit 1
}

Write-Host "Extracting..." -ForegroundColor Yellow
Expand-Archive -Path $zipPath -DestinationPath "$env:TEMP\DBBrowser_extract" -Force

# Move contents to target dir
$extracted = Get-ChildItem "$env:TEMP\DBBrowser_extract" | Select-Object -First 1
if ($extracted) {
    Copy-Item "$($extracted.FullName)\*" $destDir -Recurse -Force
} else {
    Copy-Item "$env:TEMP\DBBrowser_extract\*" $destDir -Recurse -Force
}

Remove-Item $zipPath -Force
Remove-Item "$env:TEMP\DBBrowser_extract" -Recurse -Force

Write-Host "DB Browser for SQLite extracted to: $destDir" -ForegroundColor Green
Write-Host "It will be included as an optional component in the next installer build." -ForegroundColor Green
