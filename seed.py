# -*- coding: utf-8 -*-
"""Legt Demo-Daten an: Beispiel-Gutachten (PDF) + Projekt, Themen, Stakeholder, Beiträge."""
import os
import sqlite3
from datetime import date

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "cockpit.db")
UPLOAD_DIR = os.path.join(BASE, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

GUTACHTEN_TEXT = [
    ("1. Immissionsschutz",
     "Prognostizierte Schallimmission betragen an der nächsten Wohnbebauung Hoxberger Straße "
     "maximal 39,8 dB(A) nachts und liegen damit 5,2 dB(A) unter dem Grenzwert der TA Lärm. "
     "Eine Schallprognose nach DIN ISO 9613-2 wurde für alle 6 geplanten Standorte durchgeführt."),
    ("2. Schattenwurf und Disko-Effekt",
     "Der rotationsbedingte Schattenwurf trifft drei Wohngebäude am Ortsrand für maximal "
     "28 Stunden pro Jahr (astronomisch maximal 30 Minuten pro Tag). Eine Abschaltautomatik "
     "bei Disko-Effekten ist vorgesehen."),
    ("3. Artenschutz",
     "Die Kartierung 2024 ergab Vorkommen des Rotmilans im Umkreis von 2,4 km. Für die "
     "Zwergfledermaus wurden Quartiere in den Alleen nördlich der A8 nachgewiesen. Es werden "
     "Abschaltalgorithmen sowie eine Anpassung des Standorts WEA-4 empfohlen."),
    ("4. Verkehr und Anlieferung",
     "Die Baustellenzufahrt erfolgt ausschließlich über die Kreisstraße K12 mit "
     "Schwertransportbegleitung. Insgesamt sind 340 Schwertransporte über 9 Monate zu erwarten. "
     "Eine temporäre Verkehrsführung am Dorfteich ist geplant."),
    ("5. regionale Wertschöpfung",
     "Die Gemeinde erhält Pachteinnahmen von ca. 180.000 € pro Jahr; die jährliche Gewerbesteuer "
     "wird auf 420.000 € geschätzt. Ein Bürgerbeteiligungsmodell mit 20 % Anteil am Bürgerwindpark "
     "ist in Vorbereitung."),
]


def erstelle_demo_pdf():
    pfad = os.path.join(UPLOAD_DIR, "demo_gutachten.pdf")
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(pfad, pagesize=A4)
    story = [Paragraph("Umwelt- und Immissionsgutachten (Auszug) – Windpark Hoxberg II",
                       styles["Title"]), Spacer(1, 12)]
    for kapitel, text in GUTACHTEN_TEXT:
        story.append(Paragraph(kapitel, styles["Heading2"]))
        story.append(Paragraph(text, styles["BodyText"]))
        story.append(Spacer(1, 8))
    doc.build(story)
    return pfad


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(open(os.path.join(BASE, "schema.sql"), encoding="utf-8").read())

    pfad = erstelle_demo_pdf()
    conn.execute("INSERT INTO dokumente (name, datei, version, ausgewertet, hochgeladen_am) "
                 "VALUES (?,?,?,?,?)",
                 ("demo_gutachten.pdf", "demo_gutachten.pdf", 1, 0, date.today().isoformat()))

    conn.execute("INSERT INTO steckbrief (id, projektname, beschreibung, ort, leistung, freigegeben) "
                 "VALUES (1,?,?,?,?,0)",
                 ("Windpark Hoxberg II",
                  "Repowering von 3 Altanlagen zu 6 modernen Windenergieanlagen nordöstlich von Hoxberg. "
                  "Die Planung befindet sich in der Vorprüfung; die Beteiligung der Bürgerinnen und "
                  "Bürger beginnt mit diesem Projektraum.",
                  "Gemeinde Hoxberg, Landkreis Kaiserslautern",
                  "ca. 24 MW (6 × 4,0 MW)"))

    themen = [
        ("Lärm & Schallschutz", "feststehend",
         "Nach der Schallprognose werden die TA-Lärm-Grenzwerte an allen Wohngebäuden eingehalten. "
         "Die Werte liegen mindestens 5 dB(A) darunter.", "Umweltgutachten, Kap. 1", 1),
        ("Schattenwurf & Disko", "feststehend",
         "Betroffen sind drei Wohngebäude mit max. 28 Stunden pro Jahr. Eine Abschaltautomatik ist "
         "fest eingeplant.", "Umweltgutachten, Kap. 2", 1),
        ("Standort WEA-4 (Artenschutz)", "gestaltbar",
         "Wegen Rotmilan- und Fledermausnachweisen wird der Standort WEA-4 geprüft und verschoben. "
         "Hier sind Anregungen aus der Bürgerschaft ausdrücklich erwünscht.", "Umweltgutachten, Kap. 3", 1),
        ("Baustellenverkehr K12", "in Prüfung",
         "Route, Anzahl der Transporte und die Verkehrsführung am Dorfteich werden gerade mit der "
         "Gemeinde abgestimmt.", "Umweltgutachten, Kap. 4", 1),
        ("Regionale Wertschöpfung & Bürgerbeteiligung", "gestaltbar",
         "Pachteinnahmen, Gewerbesteuer und ein Bürgerbeteiligungsmodell mit 20 % Anteil. Die "
         "Ausgestaltung der Teilhabe ist offen.", "Wirtschaftlichkeitsberechnung, Kap. 5", 0),
    ]
    for titel, status, beschreibung, quelle, frei in themen:
        conn.execute("INSERT INTO themen (titel, status, beschreibung, quelle, freigegeben) "
                     "VALUES (?,?,?,?,?)", (titel, status, beschreibung, quelle, frei))

    stakeholder = [
        ("Gemeinde Hoxberg (Bürgermeisteramt)", "Kommune / Zustimmung", 1),
        ("Anwohner Hoxberger Straße", "Betroffen: Schattenwurf", 2),
        ("NABU Regionalverband", "Naturschutz / Artenschutz", 3),
        ("Landwirtschaftsbetrieb Weber", "Flächeneigentümer", 5),
        ("Bürgerenergie-Genossenschaft Westpfalz", "Potenzieller Teilhaber", 5),
    ]
    for name, rolle, thema in stakeholder:
        conn.execute("INSERT INTO stakeholder (name, rolle, thema_id) VALUES (?,?,?)",
                     (name, rolle, thema))

    beitraege = [
        ("frage", "Wird der Standort WEA-4 näher an den Ort verlegt, wenn der Rotmilan dort brütet?",
         "Fam. Schneider", "in Bearbeitung",
         "Antwort aus Artenschutzkapitel vorbereiten und mit Gutachter abstimmen",
         "M. Weber", "", "", 0, 3),
        ("vorschlag", "Bitte prüft eine Umpflanzung der Allee nördlich der A8 als Ausgleichsmaßnahme.",
         "NABU Regionalverband", "neu", "", "", "", "", 0, 3),
        ("frage", "Wie hoch ist die Pachteinnahme für die Gemeinde und wer entscheidet über die Verwendung?",
         "Gemeinderat Hoxberg", "entschieden",
         "Zahlen aus Wirtschaftlichkeitsberechnung aufbereiten",
         "A. Keiser",
         "Die Gemeinde erhält ca. 180.000 € Pacht pro Jahr; über die Verwendung entscheidet der "
         "Gemeinderat im Haushaltsverfahren.",
         "Die Zahlen stammen aus der Wirtschaftlichkeitsberechnung (Kap. 5) und wurden mit dem "
         "Bürgermeisteramt abgestimmt.", 1, 5),
    ]
    for art, text, autor, status, aufgabe, verantw, entscheidung, begruendung, rueck, thema in beitraege:
        conn.execute(
            "INSERT INTO beitraege (art, text, autor, eingereicht_am, status, aufgabe, "
            "verantwortlich, entscheidung, begruendung, rueckmeldung_freigegeben, thema_id) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (art, text, autor, date.today().isoformat(), status, aufgabe, verantw,
             entscheidung, begruendung, rueck, thema))

    conn.commit()
    conn.close()
    print(f"Demo-Daten angelegt: {DB_PATH}")
    print(f"Demo-Gutachten: {pfad}")


if __name__ == "__main__":
    main()
