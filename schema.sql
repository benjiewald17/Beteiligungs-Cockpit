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
