@echo off
chcp 65001 >nul
title baziren - Setup
setlocal enabledelayedexpansion

echo ============================================
echo  baziren - first-time setup
echo ============================================
echo.

REM ---- Check Python ----
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo  [FAIL] Python not found. Install from: https://www.python.org/
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo  [OK] %%v
echo.

REM ---- Create .venv ----
set "VENV=%~dp0.venv"
if exist "%VENV%\Scripts\python.exe" (
    echo  [OK] .venv already exists
) else (
    echo  ... Creating .venv
    python -m venv "%VENV%"
    if !errorlevel! neq 0 (
        echo  [FAIL] Could not create virtual environment
        pause
        exit /b 1
    )
    echo  [OK] .venv created
)
echo.

REM ---- Run Python installer ----
echo  ... Running setup script
echo.
"%VENV%\Scripts\python" "%~dp0setup_env.py"

if %errorlevel% neq 0 (
    echo.
    echo  [FAIL] Setup script encountered errors
) else (
    echo.
    echo  [OK] Setup complete
)

echo.
pause
