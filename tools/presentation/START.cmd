@echo off
pwsh -NoProfile -File "%~dp0presentation-start.ps1" start
if errorlevel 1 (
  echo Start failed. Please read the error above and README.md.
  pause
  exit /b 1
)
start "" "http://127.0.0.1:8870/?lang=en"
