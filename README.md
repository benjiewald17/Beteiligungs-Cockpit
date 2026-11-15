# Beteiligungs-Cockpit für Windpark-Projektteams – MVP-Prototyp

Aus vorhandenen Projektinformationen wird ein strukturierter, nachvollziehbarer
Beteiligungsprozess. Zwei Ansichten, ein Datenkern:

- **`/cockpit`** – internes Projektteam: Unterlagen + KI-Auswertung, Themen &
  Handlungsspielräume (feststehend / in Prüfung / gestaltbar), Stakeholder,
  Beiträge → Aufgabe → Status → Entscheidung → Begründung, Freigabe-Workflow.
- **`/projekt`** – öffentlicher Projektraum: nur **freigegebene** Inhalte,
  Beiträge ohne Registrierung, Verbleib jedes Beitrags sichtbar.

Grundprinzip: **KI strukturiert, Menschen prüfen und entscheiden.** Jede Freigabe
wird protokolliert (`freigabe_log`).

## Schnellstart

```bash
pip install -r requirements.txt
python seed.py        # Demo-Daten + Beispiel-Gutachten (PDF) anlegen
python app.py         # http://localhost:5000
```

Demo-Zugänge:
- Cockpit: <http://localhost:5000/cockpit>
- Öffentlicher Raum: <http://localhost:5000/projekt>

## KI anbinden (optional)

Ohne Konfiguration läuft die Auswertung mit einer Stichwort-Heuristik.
Für echte KI-Auswertung einen EU-Anbieter nutzen, z. B. Mistral:

```bash
export MISTRAL_API_KEY="..."          # https://console.mistral.ai
export KI_MODELL="mistral-small-latest"   # optional
python app.py
```

Die Auswertung liefert Themen- und Aussagen-Entwürfe mit Quellenverweis –
**Entwürfe nur im Cockpit**, öffentlich erst nach manueller Freigabe.

## Architektur (bewusst schlank)

| Baustein | Umsetzung |
|---|---|
| Backend | Flask + SQLite (eine Datei, kein Server-Setup) |
| Frontend | Jinja2-Templates + ein Stylesheet, keine Build-Pipeline |
| KI | LLM-API (Mistral o. ä.) über `ki.py`, Fallback-Heuristik |
| Dokumente | Upload nach `uploads/`, Textextraktion via pypdf |
| Freigaben | `freigegeben`-Flags + `freigabe_log` (wer, wann, was) |

## Produktionspfad (nach Pilot)

1. SQLite → PostgreSQL (Datenmodell unverändert übernehmbar)
2. Rollen & Login fürs Projektteam (z. B. SSO), AV-Vertrag + EU-Hosting
3. RAG über alle Unterlagen statt Einzeldokument-Analyse
4. Karten (OpenStreetMap), E-Mail-Benachrichtigungen, Portfolio-Ansicht

## Kern-Workflow

Frage/Vorschlag → Aufgabe → Status → Entscheidung → Begründung → öffentliche Rückmeldung.
Diese Kette ist das Herzstück und unterscheidet das Cockpit von reinen Dialog-Tools.
