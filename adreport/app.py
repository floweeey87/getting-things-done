#!/usr/bin/env python3
"""AdReport-App: lokale Drag-&-Drop-Oberfläche für den Report-Generator.

Startet einen Server, der ausschließlich auf localhost lauscht — Kundendaten
verlassen den Rechner nicht. Kein Terminal-Wissen nötig:

    python3 app.py          # öffnet http://127.0.0.1:8437

CSV-Exporte (Google Ads oder Meta Ads) ins Fenster ziehen, Kundennamen
eintragen, fertig. Mehrere Monate ergeben automatisch Trends.
"""

import re
import sys
import tempfile
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from build_report import (DEFAULT_BRAND, build_commentary, load_brand,
                          parse_export, render)

HOST, PORT = "127.0.0.1", 8437

PAGE = """<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AdReport</title>
<style>
:root {
  color-scheme: light;
  --page: #f9f9f7; --surface: #fcfcfb; --ink: #0b0b0b; --ink-2: #52514e;
  --muted: #898781; --border: rgba(11,11,11,.10); --accent: #2a78d6;
}
@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --page: #0d0d0d; --surface: #1a1a19; --ink: #fff; --ink-2: #c3c2b7;
    --muted: #898781; --border: rgba(255,255,255,.10); --accent: #3987e5;
  }
}
* { box-sizing: border-box; margin: 0; }
body { font-family: system-ui, sans-serif; background: var(--page); color: var(--ink);
  min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 1.5rem; }
main { width: 100%; max-width: 460px; }
h1 { font-size: 1.3rem; margin-bottom: .3rem; }
.sub { color: var(--ink-2); font-size: .9rem; margin-bottom: 1.4rem; }
.drop {
  border: 2px dashed var(--border); border-radius: 16px; background: var(--surface);
  padding: 2.2rem 1.5rem; text-align: center; cursor: pointer; transition: border-color .15s;
}
.drop.armed, .drop:hover { border-color: var(--accent); }
.drop p { color: var(--ink-2); font-size: .92rem; }
.drop strong { color: var(--ink); }
#files { display: none; }
ul { list-style: none; margin: .9rem 0 0; padding: 0; font-size: .85rem; color: var(--ink-2); }
li::before { content: "📄 "; }
label { display: block; font-size: .82rem; color: var(--ink-2); margin: 1.1rem 0 .3rem; }
input[type=text] {
  width: 100%; padding: .65rem .8rem; border-radius: 10px; font-size: .95rem;
  border: 1px solid var(--border); background: var(--surface); color: var(--ink);
}
button {
  margin-top: 1.2rem; width: 100%; padding: .8rem; border: none; border-radius: 12px;
  background: var(--accent); color: #fff; font-weight: 700; font-size: 1rem; cursor: pointer;
}
button:disabled { opacity: .45; cursor: default; }
.hint { margin-top: .9rem; font-size: .78rem; color: var(--muted); text-align: center; }
</style>
</head>
<body>
<main>
<h1>AdReport</h1>
<p class="sub">Google-Ads- oder Meta-Ads-Exporte rein, fertiger Kundenreport raus.</p>
<form method="post" action="/report" enctype="multipart/form-data">
  <div class="drop" id="drop">
    <p><strong>CSV-Exporte hierher ziehen</strong><br>oder klicken zum Auswählen —
    mehrere Monate ergeben automatisch Trends.</p>
    <input type="file" id="files" name="files" accept=".csv" multiple required>
    <ul id="list"></ul>
  </div>
  <label for="kunde">Kundenname</label>
  <input type="text" id="kunde" name="kunde" placeholder="Beispiel GmbH">
  <button type="submit" id="go" disabled>Report erstellen</button>
</form>
<p class="hint">Läuft nur auf deinem Rechner (localhost) — es werden keine Daten übertragen.</p>
</main>
<script>
const drop = document.getElementById('drop'), input = document.getElementById('files'),
      list = document.getElementById('list'), go = document.getElementById('go');
const show = () => {
  list.innerHTML = [...input.files].map(f => `<li>${f.name}</li>`).join('');
  go.disabled = input.files.length === 0;
};
drop.addEventListener('click', () => input.click());
input.addEventListener('change', show);
['dragover', 'dragenter'].forEach(e => drop.addEventListener(e, ev => {
  ev.preventDefault(); drop.classList.add('armed');
}));
['dragleave', 'drop'].forEach(e => drop.addEventListener(e, ev => {
  ev.preventDefault(); drop.classList.remove('armed');
}));
drop.addEventListener('drop', ev => {
  const dt = new DataTransfer();
  [...ev.dataTransfer.files].filter(f => f.name.toLowerCase().endsWith('.csv'))
    .forEach(f => dt.items.add(f));
  input.files = dt.files; show();
});
</script>
</body>
</html>
"""


def parse_multipart(body: bytes, content_type: str) -> tuple[list[tuple[str, bytes]], dict]:
    """Minimaler Multipart-Parser: -> ([(dateiname, inhalt), ...], {feld: wert})."""
    m = re.search(r'boundary="?([^";]+)"?', content_type)
    if not m:
        return [], {}
    boundary = b"--" + m.group(1).encode()
    files, fields = [], {}
    for part in body.split(boundary):
        if b"\r\n\r\n" not in part:
            continue
        head, _, content = part.partition(b"\r\n\r\n")
        content = content.rstrip(b"\r\n-")
        header = head.decode("utf-8", "replace")
        name_m = re.search(r'name="([^"]*)"', header)
        file_m = re.search(r'filename="([^"]*)"', header)
        if not name_m:
            continue
        if file_m:
            if file_m.group(1):
                files.append((Path(file_m.group(1)).name, content))
        else:
            fields[name_m.group(1)] = content.decode("utf-8", "replace").strip()
    return files, fields


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: str, ctype: str = "text/html; charset=utf-8") -> None:
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path == "/":
            self._send(200, PAGE)
        else:
            self._send(404, "Nicht gefunden")

    def do_POST(self) -> None:
        if self.path != "/report":
            self._send(404, "Nicht gefunden")
            return
        length = int(self.headers.get("Content-Length", 0))
        files, fields = parse_multipart(self.rfile.read(length),
                                        self.headers.get("Content-Type", ""))
        if not files:
            self._send(400, "Keine CSV-Dateien empfangen — bitte zurück und erneut versuchen.")
            return
        try:
            with tempfile.TemporaryDirectory() as tmp:
                paths = []
                for name, content in sorted(files):
                    p = Path(tmp) / name
                    p.write_bytes(content)
                    paths.append(p)
                history = [parse_export(p) for p in paths]
        except SystemExit as exc:
            self._send(422, f"<h1>CSV nicht lesbar</h1><p>{exc}</p><p><a href='/'>Zurück</a></p>")
            return
        data = history[-1]
        prev = history[-2] if len(history) >= 2 else None
        kunde = fields.get("kunde") or "Kunde"
        brand_file = Path(__file__).parent / "agentur.json"
        brand = load_brand(brand_file if brand_file.exists() else None)
        commentary = build_commentary(data, prev)
        report = render(kunde, data["zeitraum"] or "Berichtszeitraum", history, brand, commentary)
        self._send(200, report)

    def log_message(self, fmt: str, *args) -> None:
        pass


def main() -> int:
    server = HTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}"
    print(f"AdReport läuft auf {url} — Fenster schließen mit Strg+C.")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBeendet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
