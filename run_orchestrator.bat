@echo off
echo Starting Rust-DFIR Orchestrator...
echo.
cd /d "%~dp0"
python run_orchestrator.py
pause
