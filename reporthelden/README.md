# ReportHelden — Google-Ads-Kundenreports aus dem CSV-Export

**CSV rein, fertiger Kundenreport raus.** ReportHelden verwandelt einen normalen Google-Ads-Kampagnen-Export in einen deutschsprachigen, kundenfertigen Performance-Report — inklusive automatisch generierter Zusammenfassung und Empfehlungen.

Positionierung siehe [MARKET-OPPORTUNITY.md](../MARKET-OPPORTUNITY.md): der Angriff auf Per-Client-Abos von AgencyAnalytics ($20/Kunde/Monat), DashThis & Co. — mit drei Differenzierern, die kein Incumbent hat:

1. **Local-first & DSGVO-nativ:** läuft komplett offline (nur Python-Standardbibliothek). Kundendaten verlassen nie den Rechner — kein Cloud-Upload, kein AV-Vertrag, keine US-Datenübertragung.
2. **AI-nativ:** Der Report enthält den Kommentar („was ist passiert, warum, was tun"), nicht nur Charts. Aktuell regelbasiert und deterministisch; ein optionaler Claude-Feinschliff ist der nächste Ausbauschritt.
3. **CSV-first:** keine Google-Ads-API, kein Developer-Token, kein OAuth — die Einstiegshürde der Incumbents wird schlicht umgangen.

## Nutzung

**Ohne Terminal (empfohlen für die Beta):**

```bash
python3 reporthelden/app.py
```

Öffnet eine lokale Drag-&-Drop-Oberfläche im Browser (nur localhost, keine Datenübertragung).
CSV-Exporte hineinziehen, Kundennamen eintragen, Report erstellen. Liegt eine `agentur.json`
neben `app.py`, wird sie automatisch als White-Label-Konfiguration verwendet.

**Per Kommandozeile:**

```bash
# Einzelne Monate
python3 reporthelden/build_report.py aktuell.csv vorperiode.csv --kunde "Beispiel GmbH" -o report.html

# Ordner mit Monats-Exporten -> automatisch Mehrmonats-Trends
python3 reporthelden/build_report.py exports/ --kunde "Beispiel GmbH"

# White-Label (Logo, Farben, Agenturname) und KI-Feinschliff
python3 reporthelden/build_report.py exports/ --brand agentur.json --ai

# Zusaetzlich als PDF (nutzt installiertes Chrome/Edge headless, ohne Druckdialog)
python3 reporthelden/build_report.py exports/ --pdf
```

- `aktuell.csv` — Kampagnenbericht aus **Google Ads** (Berichte → Kampagnen → CSV) oder **Meta Ads** (Werbeanzeigenmanager → Exportieren). Die Quelle wird automatisch am Header erkannt; Google braucht `Kampagne, Kosten` (plus Impressionen/Klicks/Conversions), Meta `Kampagnenname, Ausgegebener Betrag` (plus Link-Klicks/Ergebnisse/Conversion-Wert).
- **Deutsche und englische Oberflächen** werden gleichermaßen gelesen — `Campaign, Cost, Impressions, Conv. value` bzw. `Campaign name, Amount spent, Link clicks, Purchase conversion value`. Viele PPC-Leute im DACH-Raum betreiben ihre Konten auf Englisch; ein englischer Export darf deshalb nicht am Header scheitern.
- `vorperiode.csv` — optional; aktiviert Vergleichs-Deltas an den KPI-Kacheln und im Kommentar.
- Der Parser ist tolerant gegenüber echten Exportvarianten: Vorspannzeilen, Summenzeilen
  (`Gesamt`, `Gesamt: Konto`, `Summe`, `Total: account`, Metas `Ergebnisse aus …`),
  Komma/Semikolon/Tab und Spaltennamen mit Zusatz (`Kosten (EUR)`, `Cost (USD)`).
- **Zahlenformate erkennt der Parser pro Datei**, nicht pro Zelle: `1.234,56` und `1,234.56`
  ergeben beide 1234,56. Das ist nötig, weil `1,234` für sich genommen mehrdeutig ist —
  deutsch 1,234, englisch 1234. Eine eindeutige Zahl derselben Datei (`24.657,70` oder
  `0.57`) entscheidet, welches Zeichen das Dezimaltrennzeichen ist; erst ohne jeden
  Anhaltspunkt gilt der Separator als Tausendertrenner. Steht die Währung in der
  Kostenspalte, übernimmt der Report sie (`Cost (USD)` → `8.549,06 $`).
- **Segmentierte Exporte** (nach Tag, Woche, Gerät, Netzwerk …) enthalten mehrere Zeilen je
  Kampagne. Diese werden zusammengefasst — Summen addiert, Verhältniskennzahlen wie CTR,
  CPC und ROAS anschließend aus den Summen berechnet statt gemittelt. Ein Hinweis auf der
  Konsole nennt die erkannte Segmentspalte.

Beispiel ausprobieren:

```bash
python3 reporthelden/build_report.py \
    reporthelden/sample-data/kampagnen-juli-2026.csv \
    reporthelden/sample-data/kampagnen-juni-2026.csv \
    --kunde "Beispiel GmbH" -o reporthelden/dist/beispiel-report.html
```

## Was der Report enthält

- **KPI-Kacheln:** Werbekosten, Conversions, Umsatz, ROAS — mit Vorperioden-Delta (bei Kosten gilt „weniger = gut").
- **Zusammenfassung & Empfehlungen:** generierter Fließtext — Gesamtentwicklung, stärkste/schwächste Kampagne, Budget-Empfehlung bei Kampagnen unter der Effizienzschwelle (ROAS < 1,5), CPC-Auffälligkeiten ≥ 15 %.
- **Mehrmonats-Trends:** Ab drei Monats-Exporten im Ordner zeigt der Report Trendlinien für Kosten, Conversions und ROAS.
- **Kosten-je-Kampagne-Chart** und die **vollständige Kampagnentabelle** (CTR, Ø-CPC, Kosten/Conv., ROAS).
- **White-Label:** `--brand agentur.json` setzt Logo (lokal eingebettet als data-URI), Akzentfarben, Agenturname und Footer — siehe `sample-data/agentur-beispiel.json`.
- **KI-Feinschliff (optional):** `--ai` verfeinert den Kommentar über die Claude-API (`claude-opus-5`, mit Server-Side-Fallback). Gesendet werden nur aggregierte Kennzahlen, nie Rohdaten; ohne `ANTHROPIC_API_KEY` oder SDK bleibt der regelbasierte Kommentar bestehen. Benötigt `pip install anthropic`.
- Eine einzige HTML-Datei, hell/dunkel automatisch, druckfähig (→ PDF über den Druckdialog).

## Beta-Auslieferung

```bash
python3 reporthelden/package.py   # erzeugt dist/reporthelden-beta.zip
```

Das Zip enthält App, Generator, [Kundenanleitung](ANLEITUNG.md), Ein-Klick-Starter für
Windows/macOS, White-Label-Vorlage und Beispieldaten — das Paket, das Beta-Käufer nach
der Zahlung bekommen. SEO-Artikel und LinkedIn-Posts für den Launch liegen in
[`marketing/`](marketing/).

## Artikel auf WordPress veröffentlichen

```bash
export WP_USER='...'
export WP_APP_PASSWORD='xxxx xxxx xxxx xxxx xxxx xxxx'   # Anwendungspasswort, nicht das Login-Passwort

python3 reporthelden/publish_wp.py                          # Trockenlauf
python3 reporthelden/publish_wp.py --preview vorschau.html  # erzeugtes HTML ansehen
python3 reporthelden/publish_wp.py --apply                  # als Entwürfe anlegen
python3 reporthelden/publish_wp.py --apply --status publish # direkt live
```

Überträgt Startseite, Beispiel-Report, Impressum und Datenschutz als **Seiten** sowie die
beiden SEO-Artikel aus `marketing/` als **Beiträge**. Die eigenständigen HTML-Seiten werden
dabei in themesichere Blöcke gewandelt: Das komplette CSS wird unter `.rh-page` gekapselt,
sodass keine Regel ins WordPress-Theme ausbricht, und repo-interne Links werden zu
Site-Pfaden (`/beispiel-report/`, `/impressum/`, `/datenschutz/`).

Nach dem ersten Lauf in WordPress unter *Einstellungen → Lesen* die Seite „start" als
Startseite festlegen. Mit `--only posts` bzw. `--only pages` lässt sich die Übertragung
einschränken. Trockenlauf und
Entwurfsstatus sind Voreinstellung, Zugangsdaten kommen ausschließlich aus der Umgebung,
und bestehende Beiträge werden über den Slug aktualisiert statt dupliziert. Die interne
`Ziel-Keywords`-Zeile wird nie mitveröffentlicht — das Skript bricht ab, falls sie es
doch in den Inhalt schaffen sollte.

## Pre-Launch-Check

```bash
python3 reporthelden/preflight.py
```

Prüft vor dem Livegang: offene Platzhalter (auch mehrzeilige), nicht ersetzter CTA, tote
interne Links, Share-Bild-Maße, CNAME-/canonical-Konsistenz sowie Aktualität von
Demo-Report und Beta-Paket. Exit-Code 1, solange Blocker offen sind — damit auch als
CI-Gate nutzbar.

## Tests

```bash
cd reporthelden && python3 -m unittest test_reporthelden -v
```

48 Tests decken beide Parser (Google/Meta) in deutscher und englischer Oberfläche,
beide Zahlenformate samt Mehrdeutigkeiten, Währungserkennung, segmentierte Exporte,
Spaltenverwechslungs- und Summenzeilen-Fälle, die Kommentar-Regeln, HTML-Escaping
und den Multipart-Parser der App ab. Vier davon sichern die **Python-3.9-Kompatibilität**
statisch ab (3.9 ist der Systempython von macOS — dort darf nichts nachinstalliert werden
müssen): 3.9-Syntax, der nötige `from __future__ import annotations`, keine PEP-604-Union
außerhalb von Annotationen und die Versionsprüfung beim Start. Sechs weitere sichern den
**Windows-Betrieb**: CSVs aus Excel (cp1252), Google-Ads-„Excel-CSV" (UTF-16), BOM-Dateien,
unlesbare Bytes ohne Traceback — und ein AST-Guard, dass keine Datei-Operation ohne
`encoding=` zurückkehrt (ohne das schreibt Windows in der Codepage der Systemsprache und
scheitert am ersten `€` des Reports).

## Roadmap

- ✅ White-Label, Mehrmonats-Trends, KI-Feinschliff, Meta-Ads-Import, Drag-&-Drop-App, Test-Suite, PDF-Export (`--pdf`, via installiertem Chrome/Edge)
- GA4-Exporte als weitere Quelle
