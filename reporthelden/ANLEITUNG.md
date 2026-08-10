# ReportHelden — Erste Schritte

Danke, dass du bei der Beta dabei bist! In 5 Minuten erstellst du deinen ersten Report.

## 1. Voraussetzung: Python (einmalig)

ReportHelden läuft komplett auf deinem Rechner — dafür braucht es Python (kostenlos):

- **Windows:** [python.org/downloads](https://www.python.org/downloads/) → Installer starten → **Haken bei „Add Python to PATH" setzen** → Installieren.
- **macOS:** Python ist meist schon da. Prüfen: Terminal öffnen, `python3 --version` eintippen. Falls nicht: [python.org/downloads](https://www.python.org/downloads/).

Mehr wird nicht installiert — ReportHelden selbst hat keine Abhängigkeiten.

## 2. ReportHelden starten

Zip entpacken, dann:

- **Windows:** Doppelklick auf `ReportHelden starten.bat`
- **macOS:** Doppelklick auf `ReportHelden starten.command`
  (beim ersten Mal ggf. Rechtsklick → „Öffnen" wegen der Gatekeeper-Abfrage)

Es öffnet sich ein Browserfenster mit der ReportHelden-Oberfläche. Alles läuft nur auf
deinem Rechner (localhost) — es werden keine Daten übertragen.

## 3. CSV exportieren

- **Google Ads:** Kampagnen-Übersicht → Download-Symbol → **CSV**. Zeitraum vorher auf den Berichtsmonat stellen.
- **Meta Ads:** Werbeanzeigenmanager → Kampagnen-Tab → **Exportieren → Tabellendaten exportieren (CSV)**.

Tipp: Exportiere gleich die letzten 2–3 Monate als einzelne Dateien — ReportHelden macht
daraus automatisch Vergleichswerte und Trendlinien.

Egal welche Oberflächensprache: **deutsche und englische Exporte** werden beide gelesen
(„Kampagne/Kosten" ebenso wie „Campaign/Cost"), inklusive der jeweiligen Zahlenformate
(`1.234,56` und `1,234.56`). Segmentierte Exporte (nach Tag, Gerät, Netzwerk …) fasst
ReportHelden automatisch je Kampagne zusammen. Steht die Währung in der Kostenspalte
(`Cost (USD)`), erscheint sie auch so im Report.

## 4. Report erstellen

CSV-Dateien ins Fenster ziehen, Kundennamen eintragen, „Report erstellen" klicken.
Kommentar kurz gegenlesen (er ist ein Vorschlag, kein Gesetz), dann:

- **Als PDF an den Kunden:** Im Browser Drucken (Strg+P / Cmd+P) → „Als PDF sichern".
  Profi-Weg ohne Druckdialog: `python3 build_report.py deine-exports/ --pdf` erzeugt das PDF direkt
  (nutzt dein installiertes Chrome oder Edge im Hintergrund).
- **Als HTML:** Seite speichern (Strg+S) — eine einzige Datei, die überall funktioniert.

## 5. Dein Branding (optional)

Öffne `agentur.json` im ReportHelden-Ordner mit einem Texteditor:

```json
{
  "agentur": "Deine Agentur GmbH",
  "logo": "logo.png",
  "accent": "#2a78d6",
  "accent_dark": "#3987e5",
  "footer": "Erstellt von Deine Agentur GmbH"
}
```

Logo-Datei einfach in den Ordner legen. Ab dem nächsten Report ist alles gebrandet.

## Fragen, Wünsche, Fehler?

Antworte einfach auf die Mail mit deinem Beta-Zugang — als Beta-Nutzer prägst du
die Roadmap direkt mit. Wenn ein CSV nicht erkannt wird: Datei mitschicken
(gern mit geschwärzten Zahlen), das ist der schnellste Weg zum Fix.
