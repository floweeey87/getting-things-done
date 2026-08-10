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
  scripts/earnings_due.py       – ermittelt, welches Unternehmen fällig ist (Quartalslogik)
  scripts/validate_article.py   – prüft einen fertigen Artikel gegen die Pflichtregeln
  scripts/build_manifest.py     – baut manifest.json + ready.json aus einem Artikelverzeichnis
  content-sync/manifest.json    – versionierter Auslieferungsstand (Bridge liest hier)
  content-sync/ready.json       – Zeiger auf das aktuell auszuliefernde Update
  content-sync/earnings-progress.json – Verlaufsprotokoll aller Läufe
```

## Ablauf eines Laufs (genau in dieser Reihenfolge)

### 0. Setup
- `git fetch origin master && git checkout master && git pull origin master`
- Alle Pfade sind relativ zu `kurssturzkompass/`.

### 1. Fälligkeit ermitteln
```
python3 kurssturzkompass/scripts/earnings_due.py
```
Das Skript liest `config/watchlist.json`, berechnet je Unternehmen aus
`fiscal_year_end` und `reporting_lag_days` das jüngste Quartal, dessen
Berichtsfenster abgelaufen ist, und vergleicht es mit `last_processed_quarter`.
Die Datumsrechnung gehört bewusst ins Skript und nicht in den Prompt, damit
jeder Lauf zum selben Ergebnis kommt.

Ausgabe „Kein Unternehmen fällig“ → Lauf ohne Änderungen und ohne Commit
beenden. Sonst mit dem genannten Unternehmen weiterarbeiten (bei mehreren
Fälligen nennt das Skript das mit dem ältesten offenen Quartal zuerst).

### 2. Veröffentlichung bestätigen
„Fällig“ heißt nur: Der Bericht müsste inzwischen vorliegen. Ob er
tatsächlich veröffentlicht wurde, per Websuche prüfen (Suchbegriffe:
`<Name> Quartalszahlen Q<x> <Jahr>`, `<Name> quarterly results`,
IR-Pressemitteilung). Nur veröffentlichte, belegbare Zahlen zählen –
Terminankündigungen reichen nicht.

Bericht noch nicht veröffentlicht → Lauf ohne Änderungen beenden; das
Unternehmen bleibt fällig und kommt im nächsten Lauf erneut dran.

**Pro Lauf wird höchstens EIN Unternehmen verarbeitet** (gleiches Prinzip wie im
PSH-Projekt: ein Artikel pro Lauf, sauber versioniert).

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

### 5. Artikel prüfen
```
python3 kurssturzkompass/scripts/validate_article.py article-NNN
```
Prüft die Pflichtbestandteile (Kurzantwort, Kernfakten, Fazit, Primärquellen,
Datenstand, Risikohinweis, Quellen-Links, Mindestlänge) und schlägt bei
Formulierungen an, die als Empfehlung oder Versprechen gelesen werden können
(Kursziel, „garantiert“, „jetzt kaufen“ …). Exit-Code ungleich 0 → Artikel
korrigieren und erneut prüfen. **Erst bei Exit-Code 0 weiter zu Schritt 6.**

### 6. Manifest bauen
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

### 7. Fortschritt festhalten
- In `config/watchlist.json` beim verarbeiteten Unternehmen
  `last_processed_quarter` und `last_processed_at` (ISO-Zeitstempel) setzen.
  `last_processed_quarter` muss exakt das Label aus `earnings_due.py`
  verwenden (Format `Q<x>-<Jahr>`, Jahr = Geschäftsjahr, in dem es endet) –
  sonst erkennt der nächste Lauf das Quartal nicht wieder.
- In `content-sync/earnings-progress.json` einen Eintrag unter `runs` ergänzen:
  `{"slug", "quarter", "manifest_version", "report_date", "status": "rewritten",
  "verified_manifest": true}` sowie `updated_at` und `notes` aktualisieren.

### 8. Committen und pushen
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
