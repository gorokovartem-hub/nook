$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Create the virtual environment and install requirements first:"
    Write-Host "  py -m venv .venv"
    Write-Host "  .\.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller"
    exit 1
}

& ".venv\Scripts\python.exe" -m PyInstaller --clean --noconfirm "nook-en.spec"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "English build created in: dist\Nook-English"
Write-Host "Executable: dist\Nook-English\Nook-English.exe"
