$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\pip.exe install -r requirements.txt
.\.venv\Scripts\pip.exe install -r requirements-optional.txt

Write-Host "Setup concluido. Rode: .\scripts\run_gui_windows.ps1"
