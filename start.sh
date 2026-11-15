#!/usr/bin/env bash
# Beteiligungs-Cockpit starten (macOS/Linux): im Terminal  ./start.sh
set -e
cd "$(dirname "$0")"

PY=python3
command -v python3 >/dev/null 2>&1 || PY=python

echo "[1/3] Installiere Pakete (nur beim ersten Mal) ..."
"$PY" -m pip install -r requirements.txt --quiet

echo "[2/3] Lege Demo-Daten an ..."
"$PY" seed.py

echo "[3/3] Starte Cockpit ..."
echo "  ==> http://localhost:5000/cockpit   (Team)"
echo "  ==> http://localhost:5000/projekt   (öffentlich)"
echo "  Beenden mit Strg+C"
( sleep 2; open http://localhost:5000/cockpit 2>/dev/null || xdg-open http://localhost:5000/cockpit 2>/dev/null || true ) &
exec "$PY" app.py
