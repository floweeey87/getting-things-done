#!/usr/bin/env python3
"""Schnürt das Beta-Auslieferungspaket: dist/reporthelden-beta.zip

Inhalt: App + Generator, Kundenanleitung, Ein-Klick-Starter für
Windows/macOS, White-Label-Vorlage und Beispieldaten zum Ausprobieren.
"""

import sys
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent

STARTER_BAT = """@echo off\r
cd /d "%~dp0"\r
py app.py 2>nul || python app.py\r
pause\r
"""

STARTER_COMMAND = """#!/bin/bash
cd "$(dirname "$0")"
python3 app.py
"""

BRAND_TEMPLATE = """{
  "agentur": "",
  "logo": "",
  "accent": "#2a78d6",
  "accent_dark": "#3987e5",
  "footer": "Erstellt mit ReportHelden \\u00b7 Daten wurden lokal verarbeitet und nicht an Dritte \\u00fcbertragen."
}
"""


def main() -> int:
    out = BASE / "dist" / "reporthelden-beta.zip"
    out.parent.mkdir(exist_ok=True)

    files = [
        (BASE / "app.py", "reporthelden/app.py"),
        (BASE / "build_report.py", "reporthelden/build_report.py"),
        (BASE / "ANLEITUNG.md", "reporthelden/ANLEITUNG.md"),
        (BASE / "sample-data" / "kampagnen-juli-2026.csv",
         "reporthelden/beispieldaten/kampagnen-juli-2026.csv"),
        (BASE / "sample-data" / "kampagnen-juni-2026.csv",
         "reporthelden/beispieldaten/kampagnen-juni-2026.csv"),
        (BASE / "sample-data" / "meta" / "meta-juli-2026.csv",
         "reporthelden/beispieldaten/meta-juli-2026.csv"),
    ]

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for src, arc in files:
            z.write(src, arc)
        z.writestr("reporthelden/ReportHelden starten.bat", STARTER_BAT)
        info = zipfile.ZipInfo("reporthelden/ReportHelden starten.command")
        info.external_attr = 0o755 << 16  # ausführbar auf macOS/Linux
        z.writestr(info, STARTER_COMMAND)
        z.writestr("reporthelden/agentur.json", BRAND_TEMPLATE)

    size_kb = out.stat().st_size / 1024
    print(f"OK: {out} ({size_kb:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
