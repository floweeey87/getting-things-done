#!/usr/bin/env python3
"""Pre-Launch-Check für ReportHelden.

Prüft vor dem Livegang alles, was still und leise kaputt sein kann:
offene Platzhalter, nicht ersetzter Mail-CTA, tote interne Links,
fehlendes/falsch dimensioniertes Share-Bild, Domain-Konsistenz und ein
veraltetes Auslieferungspaket.

    python3 preflight.py

Exit-Code 0 = startklar, 1 = es sind noch Blocker offen.
"""

import re
import struct
import sys
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
LANDING = BASE / "landing"
DOMAIN = "reporthelden.de"

RED, YELLOW, GREEN, RESET = "\033[31m", "\033[33m", "\033[32m", "\033[0m"

blockers: list[str] = []
warnings: list[str] = []


def check(name: str, ok: bool, detail: str = "", blocking: bool = True) -> None:
    if ok:
        print(f"  {GREEN}✓{RESET} {name}")
        return
    mark, bucket = (f"{RED}✗{RESET}", blockers) if blocking else (f"{YELLOW}!{RESET}", warnings)
    print(f"  {mark} {name}" + (f" — {detail}" if detail else ""))
    bucket.append(name)


print("\nReportHelden · Pre-Launch-Check\n")

# 1) Offene Platzhalter (auch mehrzeilige) in allen Landing-Seiten
print("Platzhalter")
placeholder = re.compile(r"\[[A-ZÄÖÜ][^\]]{3,}\]", re.S)
for page in sorted(LANDING.glob("*.html")):
    hits = placeholder.findall(page.read_text(encoding="utf-8"))
    labels = ", ".join(sorted({h.split("—")[0].strip()[:32] for h in hits})[:3])
    check(f"{page.name}: keine offenen Platzhalter", not hits,
          f"{len(hits)} offen ({labels}{' …' if len(hits) > 3 else ''})")

# 2) CTA muss auf den Zahlungslink zeigen, nicht auf den Platzhalter
print("\nCall-to-Action")
index = (LANDING / "index.html").read_text(encoding="utf-8")
ctas = re.findall(r'class="btn btn-primary" href="([^"]+)"', index)
check("CTA-Ziel gesetzt (Zahlungslink statt Platzhalter-Mail)",
      bool(ctas) and not any("PLATZHALTER" in c for c in ctas),
      f"aktuell: {ctas[0] if ctas else 'kein CTA gefunden'}")

# 3) Interne Links und Bilder
print("\nVerlinkung")
missing = []
for page in sorted(LANDING.glob("*.html")):
    html = page.read_text(encoding="utf-8")
    targets = re.findall(r'href="([^"#:]+)"', html)
    targets += [s for s in re.findall(r'(?:src|content)="([^":]+\.(?:png|jpg|svg))"', html)]
    missing += [f"{page.name} → {t}" for t in targets if not (LANDING / t).exists()]
check("alle internen Links und Bilder auflösbar", not missing, "; ".join(missing[:3]))

# 4) Share-Bild
print("\nSocial")
og = LANDING / "og-image.png"
if og.exists():
    w, h = struct.unpack(">II", og.read_bytes()[16:24])
    check("og-image.png ist 1200×630", (w, h) == (1200, 630), f"ist {w}×{h}")
else:
    check("og-image.png vorhanden", False, "Datei fehlt")

# 5) Domain-Konsistenz (canonical/og:url zeigen auf die Live-Domain)
print("\nDomain")
urls = set(re.findall(r'(?:canonical" href|og:url" content)="https://([^/"]+)', index))
check("canonical/og:url zeigen auf " + DOMAIN,
      bool(urls) and urls == {DOMAIN}, f"gefunden: {', '.join(urls) or '–'}")
check("kein GitHub-Pages-Rest (CNAME/Workflow)",
      not (LANDING / "CNAME").exists()
      and not (BASE.parent / ".github/workflows/deploy-landing.yml").exists(),
      "Site läuft auf WordPress — statische Deploy-Reste entfernen")

# 6) Demo-Report aktuell (Landing-Kopie vs. generierter Report)
print("\nAuslieferung")
demo, built = LANDING / "demo-report.html", BASE / "dist" / "beispiel-report.html"
check("Demo-Report auf der Landingpage aktuell",
      demo.exists() and built.exists() and demo.read_bytes() == built.read_bytes(),
      "dist/beispiel-report.html neu generieren und nach landing/demo-report.html kopieren",
      blocking=False)

# 7) Beta-Paket enthält den aktuellen Code
zip_path = BASE / "dist" / "reporthelden-beta.zip"
if zip_path.exists():
    with zipfile.ZipFile(zip_path) as z:
        stale = [n for n, src in (("reporthelden/app.py", BASE / "app.py"),
                                  ("reporthelden/build_report.py", BASE / "build_report.py"),
                                  ("reporthelden/ANLEITUNG.md", BASE / "ANLEITUNG.md"))
                 if z.read(n) != src.read_bytes()]
    check("Beta-Paket enthält den aktuellen Stand", not stale,
          f"veraltet: {', '.join(Path(s).name for s in stale)} — python3 package.py ausführen")
else:
    check("Beta-Paket vorhanden", False, "python3 package.py ausführen")

# Fazit
print()
if blockers:
    print(f"{RED}{len(blockers)} Blocker offen{RESET}"
          + (f", {len(warnings)} Hinweis(e)" if warnings else "") + " — noch nicht launchen.\n")
    sys.exit(1)
print(f"{GREEN}Startklar{RESET}"
      + (f" ({len(warnings)} Hinweis(e))" if warnings else "") + " — Welle 1 kann losgehen.\n")
sys.exit(0)
