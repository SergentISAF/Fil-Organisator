@echo off
title Fil-Organisator - Forbereder...
color 0A
cls

echo.
echo  ================================================
echo    FIL-ORGANISATOR  ^|  USB-udgave
echo  ================================================
echo.

:: TRIN 1: Check om Python er installeret
echo  [1/4]  Tjekker Python...

py --version >nul 2>&1
if %errorlevel% == 0 (
    for /f "tokens=*" %%i in ('py --version 2^>^&1') do set PY_VER=%%i
    echo         Fundet: %PY_VER%
    goto :check_pakker
)

python --version >nul 2>&1
if %errorlevel% == 0 (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PY_VER=%%i
    echo         Fundet: %PY_VER%
    set PYTHON_CMD=python
    goto :check_pakker
)

:: Python ikke fundet
cls
echo.
echo  ================================================
echo    PYTHON ER IKKE INSTALLERET
echo  ================================================
echo.
echo  For at bruge Fil-Organisatoren skal du
echo  installere Python.
echo.
echo  SAADAN GOER DU:
echo.
echo  1. Ga ind paa:  https://www.python.org/downloads/
echo.
echo  2. Klik paa den store gule knap "Download Python"
echo.
echo  3. Aaben den downloadede fil
echo.
echo  4. VIGTIGT: Saet flueben ved:
echo     [x]  Add Python to PATH
echo          (i bunden af installationsvinduet)
echo.
echo  5. Klik  "Install Now"
echo.
echo  6. Naar installationen er faerdig - koer denne fil igen
echo.
echo  ------------------------------------------------
echo.

choice /c JN /m "  Vil du have mig til at aabne Python-siden i browseren? (J/N)"
if %errorlevel% == 1 (
    start https://www.python.org/downloads/
    echo.
    echo  Siden aabnes nu i din browser...
)

echo.
echo  Tryk en tast for at lukke...
pause >nul
exit


:: TRIN 2: Installer manglende pakker
:check_pakker
echo.
echo  [2/4]  Tjekker noedvendige pakker...

if not defined PYTHON_CMD set PYTHON_CMD=py

:: Check Pillow
%PYTHON_CMD% -c "import PIL" >nul 2>&1
if %errorlevel% neq 0 (
    echo         Pillow mangler - installerer...
    %PYTHON_CMD% -m pip install Pillow --quiet --disable-pip-version-check
    if %errorlevel% neq 0 (
        echo.
        echo  FEJL: Kunne ikke installere Pillow.
        echo  Proev manuelt:  py -m pip install Pillow
        echo.
        pause
        exit
    )
    echo         Pillow installeret!
) else (
    echo         Pillow:  OK
)

:: Check tqdm
%PYTHON_CMD% -c "import tqdm" >nul 2>&1
if %errorlevel% neq 0 (
    echo         tqdm mangler - installerer...
    %PYTHON_CMD% -m pip install tqdm --quiet --disable-pip-version-check
    if %errorlevel% neq 0 (
        echo.
        echo  FEJL: Kunne ikke installere tqdm.
        echo  Proev manuelt:  py -m pip install tqdm
        echo.
        pause
        exit
    )
    echo         tqdm installeret!
) else (
    echo         tqdm:  OK
)

:: Check exifread (til RAW-billeder: CR2, NEF, ARW osv.)
%PYTHON_CMD% -c "import exifread" >nul 2>&1
if %errorlevel% neq 0 (
    echo         exifread mangler - installerer...
    %PYTHON_CMD% -m pip install exifread --quiet --disable-pip-version-check
    if %errorlevel% neq 0 (
        echo.
        echo  FEJL: Kunne ikke installere exifread.
        echo  Proev manuelt:  py -m pip install exifread
        echo.
        pause
        exit
    )
    echo         exifread installeret!
) else (
    echo         exifread:  OK
)

:: Check reverse_geocoder (til GPS-sortering af billeder)
%PYTHON_CMD% -c "import reverse_geocoder" >nul 2>&1
if %errorlevel% neq 0 (
    echo         reverse_geocoder mangler - installerer...
    %PYTHON_CMD% -m pip install reverse_geocoder --quiet --disable-pip-version-check
    if %errorlevel% neq 0 (
        echo.
        echo  FEJL: Kunne ikke installere reverse_geocoder.
        echo  Proev manuelt:  py -m pip install reverse_geocoder
        echo.
        pause
        exit
    )
    echo         reverse_geocoder installeret!
) else (
    echo         reverse_geocoder:  OK
)

:: TRIN 3: Start selve programmet
echo.
echo  [3/4]  Starter Fil-Organisator...
echo.
echo  ================================================
echo.

cd /d "%~dp0"

net session >nul 2>&1
if %errorlevel% == 0 (
    %PYTHON_CMD% organisator.py
) else (
    powershell -Command "Start-Process cmd -ArgumentList '/c cd /d ""%~dp0"" && py organisator.py && pause' -Verb RunAs"
)
