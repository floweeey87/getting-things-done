#!/usr/bin/env python3
"""Erzeugt landing/og-image.png (1200×630) aus einer HTML-Vorlage.

Das Share-Bild ist das Erste, was jemand von ReportHelden sieht — in
LinkedIn, WhatsApp, Slack. Es darf kein Zufallsprodukt sein, das niemand
mehr nachbauen kann, deshalb steht die Quelle hier im Repo.

    python3 make_og_image.py

Nutzt das installierte Chrome/Edge/Chromium im Hintergrund (dieselbe
Erkennung wie der PDF-Export in build_report.py).
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from build_report import find_browser

BASE = Path(__file__).resolve().parent
ZIEL = BASE / "landing" / "og-image.png"
BREITE, HOEHE = 1200, 630

VORLAGE = """<!doctype html>
<html lang="de"><head><meta charset="utf-8"><style>
* { box-sizing: border-box; margin: 0; }
html, body { width: 1200px; height: 630px; }
body {
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  background: #0d0d0d; color: #fff; display: flex; overflow: hidden;
}
.links { flex: 1 1 56%; padding: 62px 32px 62px 72px; display: flex;
  flex-direction: column; justify-content: center; }
.brand { display: flex; align-items: center; gap: 14px; margin-bottom: 34px; }
.brand-name { font-size: 27px; font-weight: 700; letter-spacing: -.02em; }
h1 { font-size: 54px; line-height: 1.06; letter-spacing: -.03em; font-weight: 800; }
h1 .a { color: #5fa3ef; }
.sub { margin-top: 24px; font-size: 20px; line-height: 1.4; color: #c3c2b7; max-width: 34ch; }
.rechts { flex: 1 1 44%; display: flex; align-items: center; padding-right: 64px; }
.karte { background: #fcfcfb; color: #0b0b0b; border-radius: 18px;
  padding: 26px 28px; width: 100%; box-shadow: 0 30px 70px -20px rgba(0,0,0,.7); }
.k-head { font-size: 19px; font-weight: 700; letter-spacing: -.02em; }
.k-sub { font-size: 14px; color: #898781; margin-bottom: 18px; }
.tiles { display: grid; grid-template-columns: 1fr 1fr; gap: 11px; }
.tile { background: #f2f1ec; border-radius: 11px; padding: 12px 14px; }
.t-label { font-size: 13px; color: #52514e; }
.t-value { font-size: 24px; font-weight: 700; letter-spacing: -.02em; }
.t-delta { font-size: 12px; font-weight: 600; }
.up { color: #006300; } .down { color: #d03b3b; }
.bars { margin-top: 18px; display: grid; gap: 8px; }
.bar { display: grid; grid-template-columns: 118px 1fr; align-items: center; gap: 10px; }
.bar span { font-size: 12px; color: #52514e; white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis; }
.track { display: block; height: 9px; border-radius: 5px; background: #e6e5df; }
.fill { display: block; height: 9px; border-radius: 5px; background: #2a78d6; }
</style></head><body>
<div class="links">
  <div class="brand">
    <svg width="42" height="42" viewBox="0 0 30 30">
      <rect width="30" height="30" rx="8" fill="#2a78d6"/>
      <rect x="8" y="15" width="3.4" height="7" rx="1.2" fill="#fff" opacity=".72"/>
      <rect x="13.3" y="11" width="3.4" height="11" rx="1.2" fill="#fff" opacity=".86"/>
      <rect x="18.6" y="7" width="3.4" height="15" rx="1.2" fill="#fff"/>
    </svg>
    <span class="brand-name">ReportHelden</span>
  </div>
  <h1>Aus dem Ads-Export wird ein <span class="a">fertiger Kundenreport</span>.</h1>
  <p class="sub">Google Ads &amp; Meta Ads &middot; mit Zusammenfassung und Empfehlungen
  &middot; l&auml;uft lokal auf deinem Rechner</p>
</div>
<div class="rechts">
  <div class="karte">
    <div class="k-head">Performance-Report &middot; Beispiel GmbH</div>
    <div class="k-sub">Google Ads &middot; Juli 2026</div>
    <div class="tiles">
      <div class="tile"><div class="t-label">Werbekosten</div>
        <div class="t-value">21.662,90&nbsp;&euro;</div><div class="t-delta up">&#9660; 5,7 %</div></div>
      <div class="tile"><div class="t-label">Conversions</div>
        <div class="t-value">1.062</div><div class="t-delta down">&#9660; 7,4 %</div></div>
      <div class="tile"><div class="t-label">Umsatz</div>
        <div class="t-value">106.720&nbsp;&euro;</div><div class="t-delta down">&#9660; 8,1 %</div></div>
      <div class="tile"><div class="t-label">ROAS</div>
        <div class="t-value">4,93</div><div class="t-delta down">&#9660; 2,5 %</div></div>
    </div>
    <div class="bars">
      <div class="bar"><span>Performance Max</span><span class="track"><span class="fill" style="width:100%"></span></span></div>
      <div class="bar"><span>Generische Suche</span><span class="track"><span class="fill" style="width:71%"></span></span></div>
      <div class="bar"><span>Shopping</span><span class="track"><span class="fill" style="width:44%"></span></span></div>
      <div class="bar"><span>Brand Search</span><span class="track"><span class="fill" style="width:17%"></span></span></div>
    </div>
  </div>
</div>
</body></html>
"""


def main() -> int:
    browser = find_browser()
    if not browser:
        print("Kein Chrome/Edge/Chromium gefunden — Browser installieren oder "
              "REPORTHELDEN_BROWSER setzen.", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        quelle = Path(tmp) / "og.html"
        quelle.write_text(VORLAGE, encoding="utf-8")
        ZIEL.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [browser, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
             f"--window-size={BREITE},{HOEHE}", f"--screenshot={ZIEL}",
             f"--user-data-dir={tmp}/profil", quelle.as_uri()],
            check=True, capture_output=True, timeout=90)

    breite, hoehe = ZIEL.read_bytes()[16:20], ZIEL.read_bytes()[20:24]
    masse = (int.from_bytes(breite, "big"), int.from_bytes(hoehe, "big"))
    if masse != (BREITE, HOEHE):
        print(f"Warnung: {ZIEL.name} ist {masse[0]}×{masse[1]}, "
              f"erwartet {BREITE}×{HOEHE}.", file=sys.stderr)
        return 1
    print(f"OK: {ZIEL} ({masse[0]}×{masse[1]}, {ZIEL.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
