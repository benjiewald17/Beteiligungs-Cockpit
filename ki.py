# -*- coding: utf-8 -*-
"""KI-Auswertung der Projektunterlagen.

Zwei Betriebsarten:
1. MISTRAL_API_KEY gesetzt -> echte LLM-Auswertung über die Mistral-API (EU-Anbieter).
   Jede Ausgabe erhält Quellenverweis; Entwürfe landen ungeprüft nur im Cockpit.
2. Ohne Key -> Heuristik (Stichwort-basiert), damit der Prototyp sofort lauffähig ist.

Rückgabeformat (beide Modi): {"themen": [...], "aussagen": [{"kapitel","text"}]}
"""
import json
import os
import re
import urllib.request

MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
MODEL = os.environ.get("KI_MODELL", "mistral-small-latest")

THEMEN_LEXIKON = [
    ("Lärm & Schallschutz", ["lärm", "schall", "immission", "schallschutz", "db(a)"]),
    ("Schattenwurf & Disko", ["schattenwurf", "disco", "blitzende", "rotationsverschattung"]),
    ("Vogel- & Fledermausschutz", ["vogel", "fledermaus", "artenschutz", "brutzeit", "kartierung"]),
    ("Verkehr & Anlieferung", ["verkehr", "anlieferung", "baustellenzufahrt", "schwertransport"]),
    ("Natur & Wasser", ["natur", "gewässer", "boden", "ausgleichsmaßnahme", "ökologie"]),
    ("Wertschöpfung & Teilhabe", ["wertschöpfung", "pacht", "beteiligung", "gewerbesteuer", "bürgersolar"]),
    ("Abstand & Sicherheitsbereiche", ["abstand", "sicherheitsbereich", "hinweisabstand"]),
    ("Repowering & Rückbau", ["repowering", "rückbau", "altanlage", "betriebsdauer"]),
]

ZUSAMMENFASSUNG_SATZ = re.compile(r"[^.!?]+[.!?]")


def lade_text(pfad):
    text = ""
    if pfad.lower().endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(pfad)
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
    else:
        with open(pfad, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    return text


def heuristik(text, dateiname):
    niedrig = text.lower()
    themen, aussagen = [], []
    for titel, schlagworte in THEMEN_LEXIKON:
        treffer = [s for s in schlagworte if s in niedrig]
        if not treffer:
            continue
        idx = niedrig.find(treffer[0])
        start = max(0, idx - 120)
        ausschnitt = " ".join(text[start:idx + 260].split())
        themen.append({
            "titel": titel,
            "beschreibung": f"Im Dokument „{dateiname}“ erwähnt (Stichworte: {', '.join(treffer[:3])}). "
                            f"Auszug: „{ausschnitt[:220]} …“",
        })
        aussagen.append({"kapitel": "Automatisch erkannt", "text": ausschnitt[:400]})
    if not themen:
        saetze = ZUSAMMENFASSUNG_SATZ.findall(text)
        aussagen.append({"kapitel": "Einleitung",
                         "text": " ".join(s.strip() for s in saetze[:3])[:400] or "(kein Text extrahierbar)"})
        themen.append({"titel": "Allgemeine Projektinformationen",
                       "beschreibung": "Noch kein konkretes Thema erkannt – bitte prüfen und zuordnen."})
    return {"themen": themen[:6], "aussagen": aussagen[:6]}


PROMPT = """Du bereitest Projektunterlagen eines Windparkvorhabens für die Öffentlichkeitsbeteiligung vor.
Antworte NUR mit JSON in diesem Format (deutsch, sachlich, keine Erfindungen – nur Inhalte aus dem Text):
{{"themen": [{{"titel": "...", "beschreibung": "max. 2 Sätze für Laien verständlich"}}],
 "aussagen": [{{"kapitel": "...", "text": "wörtlich relevante Aussage, max. 400 Zeichen"}}]}}
Maximal 6 Themen und 6 Aussagen.

Dokumentname: {name}
Text:
{text}"""


def llm_auswertung(text, dateiname, api_key):
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": PROMPT.format(name=dateiname, text=text[:12000])}],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")
    req = urllib.request.Request(
        MISTRAL_URL, data=body, method="POST",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        inhalt = json.loads(resp.read())["choices"][0]["message"]["content"]
    daten = json.loads(inhalt)
    return {"themen": daten.get("themen", [])[:6], "aussagen": daten.get("aussagen", [])[:6]}


def auswerten(pfad, dateiname):
    """Einstiegspunkt: liefert Themen- und Aussagen-Entwürfe (nur Cockpit, nie öffentlich)."""
    api_key = os.environ.get("MISTRAL_API_KEY")
    text = lade_text(pfad)
    if not text.strip():
        text = "(kein Text extrahierbar – ggf. gescanntes PDF, OCR nötig)"
    if api_key:
        try:
            return llm_auswertung(text, dateiname, api_key)
        except Exception as exc:  # Prototyp: sauber auf Heuristik fallen
            print(f"[KI] LLM-Aufruf fehlgeschlagen ({exc}) – Heuristik wird verwendet.")
    return heuristik(text, dateiname)
