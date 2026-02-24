@echo off
title Byg Fil-Organisator Installer
color 0A
cls

echo.
echo  ================================================================
echo    BYGGER FIL-ORGANISATOR  ^|  Dette tager 2-5 minutter
echo  ================================================================
echo.

:: ── Find Python ────────────────────────────────────────────────────
set PY=
py --version >nul 2>&1
if %errorlevel% == 0 ( set PY=py & goto :python_ok )
python --version >nul 2>&1
if %errorlevel% == 0 ( set PY=python & goto :python_ok )

echo  FEJL: Python er ikke installeret!
echo  Hent det fra: https://www.python.org/downloads/
echo  (Saet flueben ved "Add Python to PATH" under installation)
echo.
pause & exit /b 1

:python_ok
for /f "tokens=*" %%i in ('%PY% --version 2^>^&1') do echo  Python fundet: %%i
echo.

:: ── Installér PyInstaller ──────────────────────────────────────────
echo  [1/3]  Installerer/opdaterer PyInstaller...
%PY% -m pip install pyinstaller send2trash --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo  FEJL: Kunne ikke installere PyInstaller!
    pause & exit /b 1
)
echo         OK
echo.

:: ── Byg .exe med PyInstaller ──────────────────────────────────────
echo  [2/3]  Bygger .exe fil (vent venligst - dette tager et par minutter)...
echo.

if exist "dist\FilOrganisator" rmdir /s /q "dist\FilOrganisator"
if exist "build\FilOrganisator" rmdir /s /q "build\FilOrganisator"

%PY% -m PyInstaller ^
    --onedir ^
    --windowed ^
    --name "FilOrganisator" ^
    --collect-data reverse_geocoder ^
    --hidden-import PIL._tkinter_finder ^
    --hidden-import exifread ^
    --noconfirm ^
    --clean ^
    "den Simple version\organisator.py"

if %errorlevel% neq 0 (
    echo.
    echo  FEJL: PyInstaller fejlede!
    echo  Proev at koere:  %PY% -m pip install pyinstaller pillow exifread reverse_geocoder
    echo  ... og prøv igen.
    pause & exit /b 1
)

echo.
echo  .exe fil klar i:  dist\FilOrganisator\FilOrganisator.exe
echo.

:: ── Lav installer med Inno Setup ─────────────────────────────────
echo  [3/3]  Leder efter Inno Setup...

set ISCC=
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
if exist "C:\Program Files\Inno Setup 6\ISCC.exe"       set ISCC=C:\Program Files\Inno Setup 6\ISCC.exe
if exist "C:\Program Files (x86)\Inno Setup 5\ISCC.exe" set ISCC=C:\Program Files (x86)\Inno Setup 5\ISCC.exe
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe

if "%ISCC%" == "" (
    echo.
    echo  ┌──────────────────────────────────────────────────────────┐
    echo  │  Inno Setup ikke fundet.                                 │
    echo  │                                                          │
    echo  │  Din .exe er klar (uden installer) i:                    │
    echo  │    dist\FilOrganisator\FilOrganisator.exe                │
    echo  │                                                          │
    echo  │  Vil du have en rigtig installer?                        │
    echo  │  1. Download Inno Setup fra: https://jrsoftware.org/     │
    echo  │  2. Installér det                                        │
    echo  │  3. Koer denne fil igen                                  │
    echo  └──────────────────────────────────────────────────────────┘
    echo.
    echo  Vil du aabne download-siden for Inno Setup? (J/N)
    choice /c JN /n >nul
    if %errorlevel% == 1 start https://jrsoftware.org/isdl.php
    echo.
    pause & exit /b 0
)

echo         Fundet! Bygger installer...
echo.

if not exist "Output" mkdir Output

"%ISCC%" installer.iss

if %errorlevel% == 0 (
    echo.
    echo  ================================================================
    echo    SUCCES!
    echo    Installer klar:  Output\FilOrganisator_Setup.exe
    echo    Del denne fil med hvem som helst - de skal bare dobbeltklikke!
    echo  ================================================================
) else (
    echo.
    echo  FEJL under installer-bygning!
    echo  Tjek at installer.iss findes i samme mappe.
)

echo.
pause
