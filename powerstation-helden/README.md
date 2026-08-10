# Powerstation-Helden · Content-Sync

Auditierte Artikel liegen als Quelldateien unter `content-sync/article-<version>/`.
`content-sync/manifest.json` benennt den jeweils zur Übertragung vorgesehenen Beitrag
(Slug, Titel, Excerpt) und trägt mit `content_sha256` die Prüfsumme **der Quelldateien**.

## Übertragung nach WordPress

```bash
export WP_USER='...'
export WP_APP_PASSWORD='xxxx xxxx xxxx xxxx xxxx xxxx'   # Anwendungspasswort, nicht das Login-Passwort

python3 sync_wordpress.py            # Trockenlauf: zeigt Beitrag, Größe, Abweichungen
python3 sync_wordpress.py --diff     # Quelle vs. manifest content_base64 vergleichen
python3 sync_wordpress.py --apply    # überträgt die auditierte Quelle
```

Verhalten mit Absicht so gewählt:

- **Trockenlauf ist Standard** — geschrieben wird nur mit `--apply`.
- **Zugangsdaten ausschließlich aus der Umgebung**, nie im Repository.
- **Nur Aktualisieren, kein Anlegen:** Der Beitrag wird über den Slug gesucht;
  fehlt er, bricht das Skript ab, statt ein Duplikat zu erzeugen.
- **Prüfsummen-gedeckte Quelle:** Veröffentlicht werden standardmäßig die
  Quelldateien, deren Hash zu `content_sha256` passt — nicht der
  `content_base64`-Payload, falls dieser abweicht (`--source manifest`
  überschreibt das bewusst).

## Offener Punkt in Manifest v13

Der `content_base64`-Payload weicht von der auditierten Quelle ab: Der Link zur
EcoFlow-Produktseite lautet dort `river-3-plus-power-station` statt
`river-3-plus-portable-power-station`. Welche Variante gültig ist, ließ sich hier
nicht prüfen (Egress blockiert). Vor dem Übertragen einmal im Browser aufrufen —
`sync_wordpress.py --diff` zeigt die Stelle.
