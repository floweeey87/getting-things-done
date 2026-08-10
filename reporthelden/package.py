#!/usr/bin/env python3
"""Schnürt das Beta-Auslieferungspaket: dist/reporthelden-beta.zip

Inhalt: App + Generator, Kundenanleitung, Ein-Klick-Starter für
Windows/macOS, White-Label-Vorlage und Beispieldaten zum Ausprobieren.
"""

import sys
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent

# Beide Starter sagen im Fehlerfall, was zu tun ist, statt ein schwarzes
# Fenster mit einem Traceback zu zeigen — der häufigste Abbruchgrund.
# Der .bat-Inhalt bleibt bewusst ASCII (Windows-Konsole, Codepage).
STARTER_BAT = """@echo off\r
cd /d "%~dp0"\r
\r
py -3 --version >nul 2>nul\r
if %errorlevel%==0 (\r
  py -3 app.py\r
  goto ende\r
)\r
\r
python --version >nul 2>nul\r
if %errorlevel%==0 (\r
  python app.py\r
  goto ende\r
)\r
\r
echo.\r
echo   Python wurde auf diesem Rechner nicht gefunden.\r
echo.\r
echo   1. https://www.python.org/downloads/ oeffnen\r
echo   2. Python 3 installieren - WICHTIG: beim Installieren den Haken\r
echo      bei "Add python.exe to PATH" setzen\r
echo   3. Diese Datei danach erneut doppelklicken\r
echo.\r
\r
:ende\r
echo.\r
pause\r
"""

STARTER_COMMAND = """#!/bin/bash
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo
  echo "  Python 3 wurde nicht gefunden."
  echo "  Auf dem Mac ist es normalerweise dabei — sonst hier laden:"
  echo "  https://www.python.org/downloads/"
  echo
  read -n 1 -s -r -p "  Taste drücken zum Schließen ..."
  exit 1
fi

python3 app.py || {
  echo
  read -n 1 -s -r -p "  Es ist ein Fehler aufgetreten. Taste drücken zum Schließen ..."
}
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
