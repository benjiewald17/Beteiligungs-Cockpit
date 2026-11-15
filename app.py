# -*- coding: utf-8 -*-
"""Beteiligungs-Cockpit für Windpark-Projektteams – MVP-Prototyp.

Zwei Ansichten, ein Datenkern:
- /cockpit    internes Projektteam (Stakeholder, Themen, Beiträge, Freigaben)
- /projekt    öffentlicher Projektraum (nur freigegebene Inhalte)

KI: ki.py – nutzt eine LLM-API (z. B. Mistral), wenn MISTRAL_API_KEY gesetzt ist,
sonst eine Heuristik. Nichts geht ungeprüft öffentlich (Freigabe-Prinzip).
"""
import os
import sqlite3
from datetime import date
from flask import Flask, g, request, redirect, url_for, render_template, flash, abort

import ki

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cockpit.db")
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "prototyp-secret-nicht-produktiv")

STATUS_THEMEN = ["feststehend", "in Prüfung", "gestaltbar"]
STATUS_BEITRAG = ["neu", "in Bearbeitung", "beantwortet", "entschieden"]


# ---------- Datenbank ----------
def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS dokumente (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    datei TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    ausgewertet INTEGER NOT NULL DEFAULT 0,
    hochgeladen_am TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS aussagen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dokument_id INTEGER NOT NULL REFERENCES dokumente(id),
    kapitel TEXT,
    text TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS themen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titel TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'in Prüfung',
    beschreibung TEXT NOT NULL DEFAULT '',
    quelle TEXT NOT NULL DEFAULT '',
    freigegeben INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS stakeholder (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    rolle TEXT NOT NULL DEFAULT '',
    thema_id INTEGER REFERENCES themen(id)
);
CREATE TABLE IF NOT EXISTS beitraege (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    art TEXT NOT NULL,
    text TEXT NOT NULL,
    autor TEXT NOT NULL DEFAULT 'Anonym',
    eingereicht_am TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'neu',
    aufgabe TEXT NOT NULL DEFAULT '',
    verantwortlich TEXT NOT NULL DEFAULT '',
    entscheidung TEXT NOT NULL DEFAULT '',
    begruendung TEXT NOT NULL DEFAULT '',
    rueckmeldung_freigegeben INTEGER NOT NULL DEFAULT 0,
    thema_id INTEGER REFERENCES themen(id)
);
CREATE TABLE IF NOT EXISTS steckbrief (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    projektname TEXT NOT NULL,
    beschreibung TEXT NOT NULL DEFAULT '',
    ort TEXT NOT NULL DEFAULT '',
    leistung TEXT NOT NULL DEFAULT '',
    freigegeben INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS freigabe_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    objekt TEXT NOT NULL,
    objekt_id INTEGER NOT NULL,
    person TEXT NOT NULL,
    zeitpunkt TEXT NOT NULL
);
"""


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


# ---------- Hilfen ----------
def log_freigabe(objekt, objekt_id, person="Projektleitung"):
    db().execute(
        "INSERT INTO freigabe_log (objekt, objekt_id, person, zeitpunkt) VALUES (?,?,?,?)",
        (objekt, objekt_id, person, date.today().isoformat()))
    db().commit()


def beitrag_public(beitrag):
    """Ein Beitrag ist öffentlich sichtbar, sobald er eingereicht wurde;
    die Rückmeldung (Entscheidung/Begründung) nur nach Freigabe."""
    return {
        "id": beitrag["id"],
        "art": beitrag["art"],
        "text": beitrag["text"],
        "autor": beitrag["autor"],
        "eingereicht_am": beitrag["eingereicht_am"],
        "status": beitrag["status"],
        "rueckmeldung": (beitrag["entscheidung"] or beitrag["begruendung"])
                        and beitrag["rueckmeldung_freigegeben"],
        "entscheidung": beitrag["entscheidung"] if beitrag["rueckmeldung_freigegeben"] else "",
        "begruendung": beitrag["begruendung"] if beitrag["rueckmeldung_freigegeben"] else "",
    }


# ---------- Cockpit ----------
@app.route("/")
def index():
    return redirect(url_for("cockpit"))


@app.route("/cockpit")
def cockpit():
    d = db()
    stats = {
        "dokumente": d.execute("SELECT COUNT(*) c FROM dokumente").fetchone()["c"],
        "themen": d.execute("SELECT COUNT(*) c FROM themen").fetchone()["c"],
        "themen_offen": d.execute(
            "SELECT COUNT(*) c FROM themen WHERE status != 'feststehend'").fetchone()["c"],
        "beitraege_neu": d.execute(
            "SELECT COUNT(*) c FROM beitraege WHERE status = 'neu'").fetchone()["c"],
        "beitraege_offen": d.execute(
            "SELECT COUNT(*) c FROM beitraege WHERE status IN ('neu','in Bearbeitung')").fetchone()["c"],
        "freigaben_offen": d.execute(
            "SELECT COUNT(*) c FROM themen WHERE freigegeben = 0").fetchone()["c"]
            + d.execute("SELECT COUNT(*) c FROM steckbrief WHERE freigegeben = 0").fetchone()["c"],
    }
    aufgaben = d.execute(
        "SELECT * FROM beitraege WHERE status IN ('neu','in Bearbeitung') ORDER BY id DESC").fetchall()
    return render_template("cockpit_dashboard.html", stats=stats, aufgaben=aufgaben)


@app.route("/cockpit/unterlagen", methods=["GET", "POST"])
def unterlagen():
    d = db()
    if request.method == "POST":
        if "auswerten" in request.form:
            dok_id = int(request.form["auswerten"])
            dok = d.execute("SELECT * FROM dokumente WHERE id=?", (dok_id,)).fetchone()
            pfad = os.path.join(UPLOAD_DIR, dok["datei"])
            ergebnis = ki.auswerten(pfad, dok["name"])
            for a in ergebnis["aussagen"]:
                d.execute("INSERT INTO aussagen (dokument_id, kapitel, text) VALUES (?,?,?)",
                          (dok_id, a.get("kapitel", ""), a["text"]))
            for t in ergebnis["themen"]:
                exists = d.execute("SELECT id FROM themen WHERE titel=?", (t["titel"],)).fetchone()
                if not exists:
                    d.execute(
                        "INSERT INTO themen (titel, status, beschreibung, quelle) VALUES (?,?,?,?)",
                        (t["titel"], "in Prüfung", t.get("beschreibung", ""), dok["name"] + " (KI-Entwurf)"))
            d.execute("UPDATE dokumente SET ausgewertet=1 WHERE id=?", (dok_id,))
            d.commit()
            flash("KI-Auswertung abgeschlossen. Themen-Entwürfe warten auf Prüfung.")
            return redirect(url_for("themen"))
        if "datei" in request.files and request.files["datei"].filename:
            f = request.files["datei"]
            name = f.filename
            ziel = os.path.join(UPLOAD_DIR, name)
            f.save(ziel)
            version = 1
            alt = d.execute("SELECT version FROM dokumente WHERE name=?", (name,)).fetchone()
            if alt:
                version = alt["version"] + 1
            d.execute("INSERT INTO dokumente (name, datei, version, hochgeladen_am) VALUES (?,?,?,?)",
                      (name, name, version, date.today().isoformat()))
            d.commit()
            flash(f"„{name}“ hochgeladen (Version {version}).")
        return redirect(url_for("unterlagen"))
    docs = d.execute(
        "SELECT d.*, (SELECT COUNT(*) FROM aussagen a WHERE a.dokument_id = d.id) n_aussagen "
        "FROM dokumente d ORDER BY d.id DESC").fetchall()
    return render_template("cockpit_unterlagen.html", docs=docs)


@app.route("/cockpit/themen", methods=["GET", "POST"])
def themen():
    d = db()
    if request.method == "POST":
        tid = int(request.form["thema_id"])
        if "status" in request.form:
            d.execute("UPDATE themen SET status=? WHERE id=?", (request.form["status"], tid))
        if "freigeben" in request.form:
            d.execute("UPDATE themen SET freigegeben=1 WHERE id=?", (tid,))
            log_freigabe("thema", tid)
            flash("Thema öffentlich freigegeben (protokolliert).")
        if "beschreibung" in request.form:
            d.execute("UPDATE themen SET beschreibung=?, quelle=? WHERE id=?",
                      (request.form["beschreibung"], request.form["quelle"], tid))
        d.commit()
        return redirect(url_for("themen"))
    rows = d.execute(
        "SELECT t.*, (SELECT COUNT(*) FROM beitraege b WHERE b.thema_id = t.id) n_beitraege "
        "FROM themen t ORDER BY t.id").fetchall()
    docs = d.execute("SELECT name FROM dokumente").fetchall()
    return render_template("cockpit_themen.html", themen=rows, docs=docs,
                           status_themen=STATUS_THEMEN)


@app.route("/cockpit/stakeholder", methods=["GET", "POST"])
def stakeholder():
    d = db()
    if request.method == "POST":
        if "loeschen" in request.form:
            d.execute("DELETE FROM stakeholder WHERE id=?", (request.form["loeschen"],))
        else:
            thema_id = int(request.form["thema_id"]) if request.form.get("thema_id") else None
            d.execute("INSERT INTO stakeholder (name, rolle, thema_id) VALUES (?,?,?)",
                      (request.form["name"], request.form.get("rolle", ""), thema_id))
        d.commit()
        return redirect(url_for("stakeholder"))
    rows = d.execute(
        "SELECT s.*, t.titel thema_titel FROM stakeholder s "
        "LEFT JOIN themen t ON t.id = s.thema_id ORDER BY s.id").fetchall()
    themen = d.execute("SELECT id, titel FROM themen ORDER BY titel").fetchall()
    return render_template("cockpit_stakeholder.html", stakeholder=rows, themen=themen)


@app.route("/cockpit/beitraege", methods=["GET", "POST"])
def beitraege():
    d = db()
    if request.method == "POST":
        bid = int(request.form["beitrag_id"])
        b = d.execute("SELECT * FROM beitraege WHERE id=?", (bid,)).fetchone()
        if not b:
            abort(404)
        felder = {}
        if request.form.get("status"):
            felder["status"] = request.form["status"]
        if "aufgabe" in request.form:
            felder["aufgabe"] = request.form["aufgabe"]
            felder["verantwortlich"] = request.form.get("verantwortlich", "")
        if "entscheidung" in request.form:
            felder["entscheidung"] = request.form["entscheidung"]
            felder["begruendung"] = request.form["begruendung"]
        for k, v in felder.items():
            d.execute(f"UPDATE beitraege SET {k}=? WHERE id=?", (v, bid))
        if "rueckmeldung_freigeben" in request.form:
            d.execute("UPDATE beitraege SET rueckmeldung_freigegeben=1 WHERE id=?", (bid,))
            log_freigabe("beitrag", bid)
            flash("Rückmeldung öffentlich freigegeben (protokolliert).")
        d.commit()
        return redirect(url_for("beitrag_detail", beitrag_id=bid))
    rows = d.execute(
        "SELECT b.*, t.titel thema_titel FROM beitraege b "
        "LEFT JOIN themen t ON t.id = b.thema_id ORDER BY b.id DESC").fetchall()
    return render_template("cockpit_beitraege.html", beitraege=rows, status_beitrag=STATUS_BEITRAG)


@app.route("/cockpit/beitraege/<int:beitrag_id>", methods=["GET"])
def beitrag_detail(beitrag_id):
    b = db().execute(
        "SELECT b.*, t.titel thema_titel FROM beitraege b "
        "LEFT JOIN themen t ON t.id = b.thema_id WHERE b.id=?", (beitrag_id,)).fetchone()
    if not b:
        abort(404)
    return render_template("cockpit_beitrag_detail.html", b=b, status_beitrag=STATUS_BEITRAG)


@app.route("/cockpit/steckbrief", methods=["GET", "POST"])
def steckbrief():
    d = db()
    row = d.execute("SELECT * FROM steckbrief WHERE id=1").fetchone()
    if request.method == "POST":
        if "freigeben" in request.form:
            d.execute("UPDATE steckbrief SET freigegeben=1 WHERE id=1")
            log_freigabe("steckbrief", 1)
            flash("Projektsteckbrief öffentlich freigegeben (protokolliert).")
        else:
            d.execute("UPDATE steckbrief SET projektname=?, beschreibung=?, ort=?, leistung=? WHERE id=1",
                      (request.form["projektname"], request.form["beschreibung"],
                       request.form["ort"], request.form["leistung"]))
            flash("Entwurf gespeichert – noch nicht öffentlich.")
        d.commit()
        return redirect(url_for("steckbrief"))
    return render_template("cockpit_steckbrief.html", s=row)


# ---------- Öffentlicher Projektraum ----------
@app.route("/projekt")
def projekt():
    d = db()
    s = d.execute("SELECT * FROM steckbrief WHERE id=1 AND freigegeben=1").fetchone()
    themen = d.execute(
        "SELECT * FROM themen WHERE freigegeben=1 ORDER BY "
        "CASE status WHEN 'gestaltbar' THEN 0 WHEN 'in Prüfung' THEN 1 ELSE 2 END, titel").fetchall()
    n_beitraege = d.execute("SELECT COUNT(*) c FROM beitraege").fetchone()["c"]
    n_rueck = d.execute(
        "SELECT COUNT(*) c FROM beitraege WHERE rueckmeldung_freigegeben=1").fetchone()["c"]
    return render_template("projekt_start.html", s=s, themen=themen,
                           n_beitraege=n_beitraege, n_rueck=n_rueck)


@app.route("/projekt/beitrag", methods=["POST"])
def beitrag_neu():
    text = request.form.get("text", "").strip()
    if text:
        d = db()
        thema_id = int(request.form["thema_id"]) if request.form.get("thema_id") else None
        d.execute(
            "INSERT INTO beitraege (art, text, autor, eingereicht_am, thema_id) VALUES (?,?,?,?,?)",
            (request.form.get("art", "frage"), text,
             request.form.get("autor") or "Anonym", date.today().isoformat(), thema_id))
        d.commit()
        flash("Danke! Ihr Beitrag wurde eingereicht. Sie können seinen Verbleib hier verfolgen.")
    return redirect(url_for("beitrag_verfolgen", beitrag_id=db().execute(
        "SELECT last_insert_rowid() i").fetchone()["i"]))


@app.route("/projekt/beitrag/<int:beitrag_id>")
def beitrag_verfolgen(beitrag_id):
    b = db().execute("SELECT * FROM beitraege WHERE id=?", (beitrag_id,)).fetchone()
    if not b:
        abort(404)
    return render_template("projekt_beitrag.html", b=beitrag_public(b))


@app.route("/projekt/thema/<int:thema_id>")
def projekt_thema(thema_id):
    d = db()
    t = d.execute("SELECT * FROM themen WHERE id=? AND freigegeben=1", (thema_id,)).fetchone()
    if not t:
        abort(404)
    beitraege = [beitrag_public(b) for b in d.execute(
        "SELECT * FROM beitraege WHERE thema_id=? ORDER BY id DESC", (thema_id,)).fetchall()]
    return render_template("projekt_thema.html", t=t, beitraege=beitraege)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
