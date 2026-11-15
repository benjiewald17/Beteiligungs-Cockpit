@echo off
chcp 65001 >nul
title Beteiligungs-Cockpit

set PY=python
where python >nul 2>nul || set PY=py

cd /d "%~dp0"
if not exist "requirements.txt" (
  echo ============================================
  echo   FEHLER: Dateien fehlen in diesem Ordner!
  echo ============================================
  echo.
  echo   Du hast start.bat vermutlich DIREKT IM ZIP-FENSTER gestartet.
  echo   So geht es richtig:
  echo.
  echo   1. ZIP-Datei doppelklicken -^> Button "Alle extrahieren" klicken
  echo   2. In den NEU ENSTANDENEN Ordner gehen (Beteiligungs-Cockpit-main)
  echo   3. DORT start.bat doppelklicken
  echo.
  echo   Wichtig: Im Ordner muessen app.py, seed.py und requirements.txt
  echo   zusammen mit start.bat liegen.
  echo.
  pause
  goto ende
)

echo ============================================
echo   Beteiligungs-Cockpit wird gestartet ...
echo ============================================
echo.

echo [1/3] Installiere Benoetigtes (nur beim ersten Mal, ca. 1 Minute) ...
%PY% -m pip install -r requirements.txt --quiet
if errorlevel 1 goto fehler

echo [2/3] Lege Demo-Daten an ...
%PY% seed.py
if errorlevel 1 goto fehler

echo [3/3] Starte Cockpit ...
echo.
echo   ==> Browser oeffnen:  http://localhost:5000
echo   ==> Cockpit (Team):   http://localhost:5000/cockpit
echo   ==> Oeffentlich:      http://localhost:5000/projekt
echo.
echo   WICHTIG: Dieses Fenster bitte OFFEN lassen, solange du arbeitest!
echo            Beenden: Fenster schliessen oder Strg+C
echo.
start "" http://localhost:5000/cockpit
%PY% app.py
goto ende

:fehler
echo.
echo FEHLER: Etwas hat nicht geklappt.
echo Moeglichste Ursache: Python ist nicht installiert oder
echo der Haken "Add Python to PATH" wurde beim Installieren vergessen.
echo Bitte Python von https://www.python.org/downloads/ installieren
echo (Haken bei "Add Python to PATH" setzen!) und dieses Fenster neu oeffnen.
pause

:ende
pause
