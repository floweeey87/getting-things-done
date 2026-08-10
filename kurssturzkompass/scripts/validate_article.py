#!/usr/bin/env python3
"""Check a rewritten valuation article against the mandatory template rules.

Run this before building the manifest. It enforces the parts of
templates/bewertung-artikel.md that must never be forgotten: the risk
disclaimer, the primary-sources section with a data-as-of date, and the
absence of language that would read as investment advice.

Usage:
  python3 kurssturzkompass/scripts/validate_article.py article-001
"""

import argparse
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ARTICLES = BASE / "articles"

# (label, regex) - each must appear somewhere in the joined article HTML.
REQUIRED = [
    ("Risikohinweis", r"<strong>\s*Risikohinweis:\s*</strong>"),
    ("Hinweis 'keine Anlageberatung'", r"keine\s+Anlageberatung"),
    ("Abschnitt Primärquellen", r"<h2>\s*Primärquellen[^<]*</h2>"),
    ("Datenstand", r"Datenstand:\s*\d"),
    ("Kurzantwort-Einstieg", r"<strong>\s*Die kurze Antwort:\s*</strong>"),
    ("Kernfakten-Kasten", r'class="ksk-keyfacts"'),
    ("Abschnitt Fazit", r"<h2>\s*Fazit[^<]*</h2>"),
]

# Phrases that turn an assessment into a recommendation or a promise.
FORBIDDEN = [
    (r"\bKursziel\b", "Kursziel-Angabe liest sich als Versprechen"),
    (r"\bgarantiert(e|er|es)?\b", "Garantie-Formulierung"),
    (r"\bsicher(er)?\s+Gewinn\b", "Gewinnversprechen"),
    (r"\bjetzt\s+(kaufen|einsteigen|zuschlagen)\b", "Handlungsaufforderung"),
    (r"\bmuss\s+man\s+(kaufen|haben)\b", "Handlungsaufforderung"),
    (r"\bVerdopplung\s+garantiert\b", "Renditeversprechen"),
]

# Minimum length below which the article is almost certainly a stub.
MIN_CHARS = 3000


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source_dir", help="directory under articles/, e.g. article-001")
    args = ap.parse_args()

    src = ARTICLES / args.source_dir
    parts = sorted(src.glob("part-*.html"))
    if not parts:
        print(f"FEHLER: keine part-*.html in {src}", file=sys.stderr)
        return 1

    html = "\n".join(p.read_text(encoding="utf-8") for p in parts)
    errors: list[str] = []
    warnings: list[str] = []

    for label, pattern in REQUIRED:
        if not re.search(pattern, html, re.IGNORECASE):
            errors.append(f"fehlt: {label}")

    for pattern, why in FORBIDDEN:
        for match in re.finditer(pattern, html, re.IGNORECASE):
            snippet = html[max(0, match.start() - 60) : match.end() + 60].replace("\n", " ")
            errors.append(f"unzulässige Formulierung ({why}): …{snippet.strip()}…")

    if len(html) < MIN_CHARS:
        errors.append(f"Artikel zu kurz: {len(html)} Zeichen, erwartet mindestens {MIN_CHARS}")

    if not re.search(r"<a\s[^>]*href=", html, re.IGNORECASE):
        errors.append("keine Quellen-Links im Artikel")

    if html.count("<h2>") < 5:
        warnings.append(f"nur {html.count('<h2>')} h2-Abschnitte, die Vorlage sieht mindestens 6 vor")

    for part in parts:
        if not part.read_text(encoding="utf-8").strip():
            errors.append(f"leere Datei: {part.name}")

    for warning in warnings:
        print(f"WARNUNG: {warning}")
    for error in errors:
        print(f"FEHLER: {error}")

    if errors:
        print(f"\n{len(errors)} Problem(e) - Artikel NICHT ausliefern, erst korrigieren.")
        return 1

    print(f"OK: {args.source_dir} erfüllt die Vorlagenregeln ({len(html)} Zeichen, {len(parts)} Teil(e)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
