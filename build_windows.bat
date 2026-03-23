@echo off
setlocal EnableDelayedExpansion

echo.
echo  ToulMap - Build e Packaging Windows
echo  =====================================
echo.

python --version > nul 2>&1
if errorlevel 1 (
    echo [ERRORE] Python non trovato nel PATH.
    echo Scaricalo da https://python.org e spunta "Add to PATH".
    pause & exit /b 1
)
echo [OK] Python trovato.

echo.
echo [1/4] Installazione dipendenze Python...
pip install PyQt5 reportlab pyinstaller --quiet
if errorlevel 1 (
    echo [ERRORE] Installazione dipendenze fallita.
    pause & exit /b 1
)
echo [OK] Dipendenze installate.

echo.
echo [2/4] Compilazione con PyInstaller...
if exist dist\ToulMap rmdir /s /q dist\ToulMap
if exist build\ToulMap rmdir /s /q build\ToulMap

python -m PyInstaller toulmap.spec --noconfirm
if errorlevel 1 (
    echo [ERRORE] PyInstaller ha fallito.
    pause & exit /b 1
)
echo [OK] Eseguibile creato in dist\ToulMap\

if not exist "dist\ToulMap\ToulMap.exe" (
    echo [ERRORE] ToulMap.exe non trovato in dist\ToulMap\
    pause & exit /b 1
)

echo.
echo [3/4] Creazione installer con Inno Setup...

set ISCC=
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set ISCC=C:\Program Files\Inno Setup 6\ISCC.exe

if "%ISCC%"=="" (
    echo [AVVISO] Inno Setup non trovato.
    echo          Scaricalo da https://jrsoftware.org/isinfo.php
    echo          Poi esegui manualmente: iscc toulmap_installer.iss
    goto :skip_inno
)

if not exist installer_output mkdir installer_output
"%ISCC%" toulmap_installer.iss
if errorlevel 1 (
    echo [ERRORE] Inno Setup ha fallito.
    pause & exit /b 1
)
echo [OK] Installer creato in installer_output\

:skip_inno

echo.
echo [4/4] Build completato.
echo.
echo  File prodotti:
echo    dist\ToulMap\ToulMap.exe  -- eseguibile standalone
if exist "installer_output\ToulMap_Setup_v1.0.exe" (
    echo    installer_output\ToulMap_Setup_v1.0.exe  -- installer
)
echo.
pause
