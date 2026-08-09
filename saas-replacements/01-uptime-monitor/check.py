#!/usr/bin/env python3
"""Uptime-Monitor: prüft alle Sites aus sites.json, schreibt Verlauf und Statusseite.

Nur Python-Standardbibliothek, gedacht für einen GitHub-Actions-Cron.
Exit-Code ist immer 0; ausgefallene Sites werden über die Datei
status/down.json an den Workflow gemeldet (für Issue-Alarme).
"""

import json
import ssl
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
STATUS_DIR = BASE / "status"
HISTORY_DIR = STATUS_DIR / "history"

USER_AGENT = "Mozilla/5.0 (compatible; gtd-uptime-monitor/1.0)"


def check_site(site: dict, timeout: int, retries: int) -> dict:
    url = site["url"]
    keyword = site.get("keyword")
    last_error = None
    for attempt in range(retries + 1):
        start = time.monotonic()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                elapsed_ms = round((time.monotonic() - start) * 1000)
                body = resp.read(512 * 1024)
                status = resp.status
                if status >= 400:
                    last_error = f"HTTP {status}"
                elif keyword and keyword.encode() not in body:
                    last_error = f"Keyword '{keyword}' nicht gefunden"
                else:
                    return {"up": True, "http_status": status, "response_ms": elapsed_ms, "error": None}
        except Exception as exc:  # URLError, timeout, SSL, ...
            last_error = f"{type(exc).__name__}: {exc}"
        if attempt < retries:
            time.sleep(3)
    return {"up": False, "http_status": None, "response_ms": None, "error": last_error}


def load_history(slug: str) -> list:
    path = HISTORY_DIR / f"{slug}.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def save_history(slug: str, entries: list, max_entries: int) -> None:
    entries = entries[-max_entries:]
    path = HISTORY_DIR / f"{slug}.jsonl"
    path.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in entries) + "\n")


def uptime_pct(entries: list) -> float:
    if not entries:
        return 100.0
    up = sum(1 for e in entries if e["up"])
    return round(100.0 * up / len(entries), 2)


def render_html(summary: dict) -> str:
    rows = []
    for s in summary["sites"]:
        dot = "🟢" if s["up"] else "🔴"
        ms = f"{s['response_ms']} ms" if s["response_ms"] is not None else "–"
        err = s["error"] or ""
        rows.append(
            f"<tr><td>{dot}</td><td><a href='{s['url']}'>{s['name']}</a></td>"
            f"<td>{ms}</td><td>{s['uptime_pct']} %</td><td>{err}</td></tr>"
        )
    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Status</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:720px;margin:2rem auto;padding:0 1rem;color:#1a1a2e;background:#fafafa}}
table{{border-collapse:collapse;width:100%}}
td,th{{padding:.6rem .8rem;border-bottom:1px solid #ddd;text-align:left}}
h1{{font-size:1.4rem}} small{{color:#666}}
@media (prefers-color-scheme: dark){{body{{background:#16161e;color:#e8e8f0}}td,th{{border-color:#333}}a{{color:#8ab4f8}}}}
</style></head><body>
<h1>Status unserer Sites</h1>
<small>Zuletzt geprüft: {summary['checked_at']} (UTC) · Uptime über die letzten {summary['window_checks']} Checks</small>
<table><tr><th></th><th>Site</th><th>Antwortzeit</th><th>Uptime</th><th>Fehler</th></tr>
{''.join(rows)}
</table>
</body></html>
"""


def main() -> int:
    config = json.loads((BASE / "sites.json").read_text())
    timeout = config.get("timeout_seconds", 15)
    retries = config.get("retries", 2)
    max_entries = config.get("history_max_entries", 4320)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    summary = {"checked_at": now, "window_checks": 0, "sites": []}
    down = []

    for site in config["sites"]:
        result = check_site(site, timeout, retries)
        entry = {"t": now, "up": result["up"], "ms": result["response_ms"], "err": result["error"]}
        history = load_history(site["slug"])
        history.append(entry)
        save_history(site["slug"], history, max_entries)
        summary["window_checks"] = max(summary["window_checks"], len(history[-max_entries:]))
        site_summary = {
            "slug": site["slug"],
            "name": site["name"],
            "url": site["url"],
            "up": result["up"],
            "http_status": result["http_status"],
            "response_ms": result["response_ms"],
            "error": result["error"],
            "uptime_pct": uptime_pct(history[-max_entries:]),
        }
        summary["sites"].append(site_summary)
        if not result["up"]:
            down.append(site_summary)
        state = "UP" if result["up"] else f"DOWN ({result['error']})"
        print(f"[{state}] {site['name']} {site['url']}")

    (STATUS_DIR / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    (STATUS_DIR / "down.json").write_text(json.dumps(down, indent=2, ensure_ascii=False) + "\n")
    (STATUS_DIR / "index.html").write_text(render_html(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
