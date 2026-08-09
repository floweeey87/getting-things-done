# AdReport — Erste Schritte

Danke, dass du bei der Beta dabei bist! In 5 Minuten erstellst du deinen ersten Report.

## 1. Voraussetzung: Python (einmalig)

AdReport läuft komplett auf deinem Rechner — dafür braucht es Python (kostenlos):

- **Windows:** [python.org/downloads](https://www.python.org/downloads/) → Installer starten → **Haken bei „Add Python to PATH" setzen** → Installieren.
- **macOS:** Python ist meist schon da. Prüfen: Terminal öffnen, `python3 --version` eintippen. Falls nicht: [python.org/downloads](https://www.python.org/downloads/).

Mehr wird nicht installiert — AdReport selbst hat keine Abhängigkeiten.

## 2. AdReport starten

Zip entpacken, dann:

- **Windows:** Doppelklick auf `AdReport starten.bat`
- **macOS:** Doppelklick auf `AdReport starten.command`
  (beim ersten Mal ggf. Rechtsklick → „Öffnen" wegen der Gatekeeper-Abfrage)

Es öffnet sich ein Browserfenster mit der AdReport-Oberfläche. Alles läuft nur auf
deinem Rechner (localhost) — es werden keine Daten übertragen.

## 3. CSV exportieren

- **Google Ads:** Kampagnen-Übersicht → Download-Symbol → **CSV**. Zeitraum vorher auf den Berichtsmonat stellen.
- **Meta Ads:** Werbeanzeigenmanager → Kampagnen-Tab → **Exportieren → Tabellendaten exportieren (CSV)**.

Tipp: Exportiere gleich die letzten 2–3 Monate als einzelne Dateien — AdReport macht
daraus automatisch Vergleichswerte und Trendlinien.

## 4. Report erstellen

CSV-Dateien ins Fenster ziehen, Kundennamen eintragen, „Report erstellen" klicken.
Kommentar kurz gegenlesen (er ist ein Vorschlag, kein Gesetz), dann:

- **Als PDF an den Kunden:** Im Browser Drucken (Strg+P / Cmd+P) → „Als PDF sichern".
- **Als HTML:** Seite speichern (Strg+S) — eine einzige Datei, die überall funktioniert.

## 5. Dein Branding (optional)

Öffne `agentur.json` im AdReport-Ordner mit einem Texteditor:

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
