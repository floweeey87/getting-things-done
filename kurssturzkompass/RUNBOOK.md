# Kurssturzkompass – Quartalszahlen-Automatisierung (Runbook)

Dieses Runbook beschreibt einen einzelnen automatisierten Lauf. Ziel: Sobald ein
Unternehmen aus der Watchlist neue Quartalszahlen veröffentlicht hat, wird der
zugehörige Bewertungsartikel auf kurssturzkompass.de vollständig neu geschrieben
und über den Content-Sync-Mechanismus (gleicher Bridge-Vertrag wie bei
powerstation-helden) bereitgestellt.

## Verzeichnisstruktur

```
kurssturzkompass/
  RUNBOOK.md                    – dieses Dokument
  config/watchlist.json         – Unternehmen, die überwacht werden (Pflege durch Betreiber)
  templates/bewertung-artikel.md– Pflichtaufbau des Bewertungsartikels
  articles/article-NNN/part-XX.html – Quell-HTML des jeweils neu geschriebenen Artikels
  scripts/build_manifest.py     – baut manifest.json + ready.json aus einem Artikelverzeichnis
  content-sync/manifest.json    – versionierter Auslieferungsstand (Bridge liest hier)
  content-sync/ready.json       – Zeiger auf das aktuell auszuliefernde Update
  content-sync/earnings-progress.json – Verlaufsprotokoll aller Läufe
```

## Ablauf eines Laufs (genau in dieser Reihenfolge)

### 0. Setup
- `git fetch origin master && git checkout master && git pull origin master`
- Alle Pfade sind relativ zu `kurssturzkompass/`.

### 1. Watchlist prüfen
- `config/watchlist.json` lesen.
- Keine aktiven Unternehmen (`"active": true`) vorhanden → Lauf ohne Änderungen
  beenden. Nichts committen.

### 2. Neue Quartalszahlen erkennen
Für jedes aktive Unternehmen:
- Erwartetes Berichtsfenster bestimmen: Quartalsende laut `fiscal_year_end`
  plus `reporting_lag_days`.
- Ist `last_processed_quarter` bereits das jüngste abgeschlossene Quartal → überspringen.
- Sonst per Websuche prüfen, ob der Quartalsbericht inzwischen veröffentlicht ist
  (Suchbegriffe: `<Name> Quartalszahlen Q<x> <Jahr>`, `<Name> quarterly results`,
  IR-Pressemitteilung). Nur veröffentlichte, belegbare Zahlen zählen –
  Terminankündigungen reichen nicht.

**Pro Lauf wird höchstens EIN Unternehmen verarbeitet** (gleiches Prinzip wie im
PSH-Projekt: ein Artikel pro Lauf, sauber versioniert). Liegen mehrere neue
Berichte vor, das Unternehmen mit dem ältesten Veröffentlichungsdatum zuerst;
die übrigen kommen in den Folgeläufen dran.

Kein Unternehmen mit neuen Zahlen → Lauf ohne Änderungen beenden.

### 3. Zahlen recherchieren
Primärquelle ist immer die IR-Pressemitteilung bzw. der Quartalsbericht des
Unternehmens. Mindestens erfassen:
- Umsatz (Ist vs. Vorjahresquartal, wenn verfügbar vs. Analystenerwartung)
- Ergebnis: EBIT/EBITDA und EPS (bereinigt und unbereinigt, falls ausgewiesen)
- Guidance / Ausblick (bestätigt, angehoben, gesenkt)
- Sondereffekte, Einmalposten, wichtige operative Kennzahlen der Branche
- Kursreaktion nach Veröffentlichung (Größenordnung genügt, mit Datum)
- Aktuelle Bewertungskennzahlen (KGV, ggf. KUV/EV-EBITDA), soweit belegbar

Jede Zahl braucht eine Quelle. Nicht belegbare Zahlen werden weggelassen oder
ausdrücklich als Schätzung markiert.

### 4. Bewertungsartikel neu schreiben
- Aufbau strikt nach `templates/bewertung-artikel.md`.
- Vollständige Neufassung des Artikels zum Slug aus der Watchlist – kein Patch,
  kein Anhängen. Der Artikel ersetzt beim Sync die Live-Fassung komplett.
- Quell-HTML unter `articles/article-NNN/` ablegen (NNN = fortlaufend,
  nächste freie Nummer; bei >ca. 40.000 Zeichen in part-01.html, part-02.html …
  aufteilen).
- Sprachliche Regeln: Deutsch, sachlich, keine Kursziele als Versprechen,
  Herstellerangaben/Unternehmensangaben klar von eigener Einordnung trennen.
- Pflicht am Artikelende: Risikohinweis/Disclaimer (keine Anlageberatung) und
  Abschnitt „Primärquellen und Datenstand“ mit Links und Datum.

### 5. Manifest bauen
```
python3 kurssturzkompass/scripts/build_manifest.py \
  --source-dir article-NNN \
  --slug <slug> \
  --title "<Artikeltitel>" \
  --excerpt "<Meta-Beschreibung, max. ~160 Zeichen>"
```
Das Skript erhöht die Version, schreibt `content-sync/manifest.json` und
`content-sync/ready.json` und prüft die SHA256-Summe. Ausgabe kontrollieren:
Version, Slug und Titel müssen in beiden Dateien übereinstimmen.

### 6. Fortschritt festhalten
- In `config/watchlist.json` beim verarbeiteten Unternehmen
  `last_processed_quarter` (Format `Q<x>-<Jahr>`) und `last_processed_at`
  (ISO-Zeitstempel) setzen.
- In `content-sync/earnings-progress.json` einen Eintrag unter `runs` ergänzen:
  `{"slug", "quarter", "manifest_version", "report_date", "status": "rewritten",
  "verified_manifest": true}` sowie `updated_at` und `notes` aktualisieren.

### 7. Committen und pushen
Getrennte, klar benannte Commits (Muster wie im PSH-Projekt), z. B.:
1. `Add KSK <name> Q<x>-<Jahr> valuation rewrite` (Artikelquellen)
2. `Build KSK content manifest version <N>` (manifest + ready)
3. `Track KSK <name> earnings update completion` (watchlist + progress)

Push: `git push -u origin master`; bei Netzwerkfehlern bis zu 4-mal mit
exponentiellem Backoff (2s/4s/8s/16s) wiederholen.

## Watchlist-Schema

```json
{
  "schema": 1,
  "companies": [
    {
      "slug": "beispiel-ag-aktie",
      "name": "Beispiel AG",
      "ticker": "BSP",
      "isin": "DE0000000000",
      "exchange": "XETRA",
      "fiscal_year_end": "12-31",
      "reporting_lag_days": 45,
      "last_processed_quarter": null,
      "last_processed_at": null,
      "active": true,
      "notes": "optional: Besonderheiten, IR-URL"
    }
  ]
}
```

- `slug` muss exakt dem WordPress-Slug des Bewertungsartikels auf
  kurssturzkompass.de entsprechen – die Bridge ordnet darüber zu.
- `fiscal_year_end` steuert die Quartalsgrenzen (abweichende Geschäftsjahre,
  z. B. „09-30“, werden korrekt behandelt).
- `reporting_lag_days` ist die typische Zeit zwischen Quartalsende und
  Veröffentlichung; vorher wird gar nicht erst gesucht.

## Leitplanken
- Niemals Zahlen erfinden oder aus dem Gedächtnis „ergänzen“ – nur belegte Werte.
- Pro Lauf maximal ein Artikel; `manifest.json` ist zugleich der Rollback-Punkt.
- Keine Anlageberatung, keine Kauf-/Verkaufsempfehlungen als Aufforderung,
  Disclaimer ist Pflichtbestandteil jedes Artikels.
- Bei widersprüchlichen Quellen: Primärquelle (IR) gewinnt; Widerspruch in den
  `notes` des Progress-Eintrags dokumentieren.
