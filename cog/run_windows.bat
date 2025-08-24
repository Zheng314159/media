@echo off
setlocal
cd /d %~dp0

set VENV=F:\media\.venv\Scripts\python.exe

echo --- Running TTS Prediction on Windows ---
%VENV% run_windows.py

echo.
echo --- Prediction Complete ---
pause
endlocal
