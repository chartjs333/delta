@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo   Starting DeltaReduce Clinical Decision Support Prototype
echo ============================================================

python -u server.py
pause
