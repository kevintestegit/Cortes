$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if (!(Test-Path ".\.venv\Scripts\python.exe")) {
  Write-Error "Ambiente virtual nao encontrado. Rode: .\scripts\setup_windows.ps1"
}

.\.venv\Scripts\python.exe app.py
