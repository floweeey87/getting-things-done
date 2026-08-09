# 01 · Uptime-Monitor (ersetzt UptimeRobot)

Eigener Uptime-Monitor auf GitHub-Actions-Basis: 0 € laufende Kosten, unbegrenzte Monitore, Verlauf versioniert im Repo.

## Wie es funktioniert

- **Scheduler:** `.github/workflows/uptime.yml` läuft alle 30 Minuten (GitHub-Actions-Cron) und bei Bedarf manuell über *Run workflow*.
- **Checks:** `check.py` (nur Python-Standardbibliothek) ruft jede Site aus `sites.json` auf, mit Timeout, 2 Wiederholungen und optionalem Keyword-Check (erkennt auch "Seite lädt, zeigt aber Fehlerseite").
- **Verlauf:** Jeder Check landet in `status/history/<slug>.jsonl` (gekappt auf `history_max_entries`, Standard 4320 ≈ 90 Tage bei 30-Minuten-Takt). Daraus wird die Uptime in Prozent berechnet.
- **Statusseite:** `status/index.html` — statisches HTML mit Ampel, Antwortzeit und Uptime pro Site. `status/summary.json` liefert dieselben Daten maschinenlesbar.
- **Alarm:** Bei Ausfall öffnet der Workflow automatisch ein GitHub-Issue mit Label `incident` → GitHub benachrichtigt per Mail/App. Sobald die Site wieder erreichbar ist, wird das Issue automatisch geschlossen.

## Site hinzufügen

Eintrag in `sites.json` ergänzen:

```json
{ "slug": "meine-site", "name": "Meine Site", "url": "https://example.de/", "keyword": "Impressum" }
```

`keyword` ist optional; wenn gesetzt, gilt die Site nur als "up", wenn der Text im HTML vorkommt.

## Lokal testen

```bash
python3 saas-replacements/01-uptime-monitor/check.py
open saas-replacements/01-uptime-monitor/status/index.html
```

## Hinweise

- Der Cron läuft auf dem Standard-Branch. Nach dem Merge dieses Branches nach `master` startet der Monitor von selbst.
- GitHub-Actions-Crons können sich bei hoher Last um einige Minuten verzögern — für unseren Zweck (Ausfall binnen ~30–40 Min bemerken) völlig ausreichend. Wer 1-Minuten-Auflösung braucht, bleibt bei einem SaaS.
- Ersparnis: UptimeRobot Solo/Team kostet $7–29/Monat, der Free-Plan ist seit 2025 auf nicht-kommerzielle Nutzung beschränkt.
