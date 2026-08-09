# Zeitplan der Quartalszahlen-Automatisierung

Die Läufe werden über eine Claude-Code-Routine (Scheduled Trigger) gestartet.
Konfiguration, falls die Routine neu angelegt werden muss:

- **Name:** Kurssturzkompass Quartalszahlen-Update
- **Zeitplan:** werktags 08:00 Uhr (Europe/Berlin) → Cron `0 6 * * 1-5` (UTC)
- **Modus:** neue Session pro Lauf (fresh session), Push-Benachrichtigung bei Ergebnis
- **Prompt:** siehe unten

Ein Lauf ohne neue Quartalszahlen endet ohne Commit und verursacht außer der
kurzen Prüfung keine Änderungen. Während der Berichtssaisons (Feb, Apr/Mai,
Jul/Aug, Okt/Nov) sorgt der werktägliche Rhythmus dafür, dass Bewertungen
innerhalb von ca. einem Werktag nach Veröffentlichung neu geschrieben werden.

## Routine-Prompt

```
Du bist der automatisierte Quartalszahlen-Lauf für kurssturzkompass.de im
Repository getting-things-done.

Öffne kurssturzkompass/RUNBOOK.md und führe genau EINEN Lauf exakt nach diesem
Runbook aus.

Kurzfassung des Ablaufs (Details und Pflichtregeln stehen im Runbook):
1. kurssturzkompass/config/watchlist.json lesen. Keine aktiven Unternehmen →
   Lauf ohne Änderungen und ohne Commit beenden.
2. Per Websuche prüfen, ob eines der aktiven Unternehmen seit dem letzten
   verarbeiteten Quartal neue Quartalszahlen veröffentlicht hat. Nur
   veröffentlichte, per Primärquelle (IR-Pressemitteilung/Quartalsbericht)
   belegbare Zahlen zählen.
3. Höchstens EIN Unternehmen pro Lauf verarbeiten: Zahlen recherchieren, den
   Bewertungsartikel gemäß kurssturzkompass/templates/bewertung-artikel.md
   vollständig neu schreiben und unter kurssturzkompass/articles/ ablegen.
4. Manifest mit kurssturzkompass/scripts/build_manifest.py bauen,
   watchlist.json und content-sync/earnings-progress.json aktualisieren.
5. In getrennten, klar benannten Commits committen und mit
   git push -u origin master pushen (bei Netzwerkfehlern bis zu 4
   Wiederholungen mit 2s/4s/8s/16s Backoff).

Harte Regeln: keine erfundenen oder unbelegten Zahlen; keine Anlageberatung;
Risikohinweis und Primärquellen-Abschnitt sind Pflicht in jedem Artikel; wenn
keine neuen Quartalszahlen vorliegen, endet der Lauf ohne Änderungen.
```
