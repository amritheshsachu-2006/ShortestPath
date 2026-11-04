@echo off
title Shortest Path Finder
echo ========================================================
echo   SHORTEST PATH FINDER USING GRAPH ALGORITHMS
echo   Starting web application automatically...
echo ========================================================
cd /d "%~dp0"

echo Opening browser at http://127.0.0.1:5000 ...
start "" http://127.0.0.1:5000

if exist "venv\Scripts\python.exe" (
    echo Using virtual environment...
    "venv\Scripts\python.exe" app.py
) else (
    echo Using system Python...
    python app.py
)
pause

