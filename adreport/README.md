# AdReport — Google-Ads-Kundenreports aus dem CSV-Export

**CSV rein, fertiger Kundenreport raus.** AdReport verwandelt einen normalen Google-Ads-Kampagnen-Export in einen deutschsprachigen, kundenfertigen Performance-Report — inklusive automatisch generierter Zusammenfassung und Empfehlungen.

Positionierung siehe [MARKET-OPPORTUNITY.md](../MARKET-OPPORTUNITY.md): der Angriff auf Per-Client-Abos von AgencyAnalytics ($20/Kunde/Monat), DashThis & Co. — mit drei Differenzierern, die kein Incumbent hat:

1. **Local-first & DSGVO-nativ:** läuft komplett offline (nur Python-Standardbibliothek). Kundendaten verlassen nie den Rechner — kein Cloud-Upload, kein AV-Vertrag, keine US-Datenübertragung.
2. **AI-nativ:** Der Report enthält den Kommentar („was ist passiert, warum, was tun"), nicht nur Charts. Aktuell regelbasiert und deterministisch; ein optionaler Claude-Feinschliff ist der nächste Ausbauschritt.
3. **CSV-first:** keine Google-Ads-API, kein Developer-Token, kein OAuth — die Einstiegshürde der Incumbents wird schlicht umgangen.

## Nutzung

**Ohne Terminal (empfohlen für die Beta):**

```bash
python3 adreport/app.py
```

Öffnet eine lokale Drag-&-Drop-Oberfläche im Browser (nur localhost, keine Datenübertragung).
CSV-Exporte hineinziehen, Kundennamen eintragen, Report erstellen. Liegt eine `agentur.json`
neben `app.py`, wird sie automatisch als White-Label-Konfiguration verwendet.

**Per Kommandozeile:**

```bash
# Einzelne Monate
python3 adreport/build_report.py aktuell.csv vorperiode.csv --kunde "Beispiel GmbH" -o report.html

# Ordner mit Monats-Exporten -> automatisch Mehrmonats-Trends
python3 adreport/build_report.py exports/ --kunde "Beispiel GmbH"

# White-Label (Logo, Farben, Agenturname) und KI-Feinschliff
python3 adreport/build_report.py exports/ --brand agentur.json --ai
```

- `aktuell.csv` — Kampagnenbericht aus **Google Ads** (Berichte → Kampagnen → CSV) oder **Meta Ads** (Werbeanzeigenmanager → Exportieren). Die Quelle wird automatisch am Header erkannt; Google braucht `Kampagne, Kosten` (plus Impressionen/Klicks/Conversions), Meta `Kampagnenname, Ausgegebener Betrag` (plus Link-Klicks/Ergebnisse/Conversion-Wert).
- `vorperiode.csv` — optional; aktiviert Vergleichs-Deltas an den KPI-Kacheln und im Kommentar.
- Der Parser ist tolerant: Vorspannzeilen, `Gesamt`-Zeile, Komma/Semikolon/Tab und deutsche Zahlenformate werden automatisch erkannt.

Beispiel ausprobieren:

```bash
python3 adreport/build_report.py \
    adreport/sample-data/kampagnen-juli-2026.csv \
    adreport/sample-data/kampagnen-juni-2026.csv \
    --kunde "Beispiel GmbH" -o adreport/dist/beispiel-report.html
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
python3 adreport/package.py   # erzeugt dist/adreport-beta.zip
```

Das Zip enthält App, Generator, [Kundenanleitung](ANLEITUNG.md), Ein-Klick-Starter für
Windows/macOS, White-Label-Vorlage und Beispieldaten — das Paket, das Beta-Käufer nach
der Zahlung bekommen. SEO-Artikel und LinkedIn-Posts für den Launch liegen in
[`marketing/`](marketing/).

## Tests

```bash
cd adreport && python3 -m unittest test_adreport -v
```

20 Tests decken beide Parser (Google/Meta), deutsche und englische Zahlenformate,
Spaltenverwechslungs- und Summenzeilen-Fälle, die Kommentar-Regeln, HTML-Escaping
und den Multipart-Parser der App ab.

## Roadmap

- ✅ White-Label, Mehrmonats-Trends, KI-Feinschliff, Meta-Ads-Import, Drag-&-Drop-App, Test-Suite
- GA4-Exporte als weitere Quelle
- PDF-Export ohne Druckdialog
