#!/usr/bin/env python3
"""AdReport: erzeugt aus einem Google-Ads-Kampagnen-CSV-Export einen
fertigen deutschen Kundenreport (eine HTML-Datei) — inklusive KPI-Kacheln,
Chart, Kampagnentabelle und generiertem Kommentar.

Local-first: läuft komplett offline mit der Python-Standardbibliothek.
Kundendaten verlassen den Rechner nicht.

Nutzung:
    python3 build_report.py aktuell.csv [vorperiode.csv] \
        --kunde "Beispiel GmbH" --zeitraum "Juli 2026" -o dist/report.html
"""

import argparse
import csv
import html
import io
import sys
from pathlib import Path

REQUIRED = ["Kampagne", "Impressionen", "Klicks", "Kosten", "Conversions"]


# ---------------------------------------------------------------- Parsen

def parse_number(raw: str) -> float:
    """'1.234,56' / '12,3 %' / '1234.56' -> float."""
    s = raw.strip().replace(" ", "").replace("€", "").replace("%", "").strip()
    if not s or s in {"--", "-"}:
        return 0.0
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_export(path: Path) -> dict:
    """Liest einen Google-Ads-Export: tolerant gegenüber Vorspannzeilen,
    Trennzeichen (Komma/Semikolon/Tab) und einer 'Gesamt'-Zeile."""
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    header_idx = next(
        (i for i, l in enumerate(lines) if "Kampagne" in l and ("Klicks" in l or "Kosten" in l)),
        None,
    )
    if header_idx is None:
        raise SystemExit(f"{path}: keine Kopfzeile mit 'Kampagne' gefunden.")

    zeitraum = lines[header_idx - 1].strip() if header_idx >= 2 else ""
    body = "\n".join(lines[header_idx:])
    delimiter = max([",", ";", "\t"], key=lines[header_idx].count)
    reader = csv.DictReader(io.StringIO(body), delimiter=delimiter)

    missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
    if missing:
        raise SystemExit(f"{path}: Spalten fehlen: {', '.join(missing)}")

    campaigns = []
    for row in reader:
        name = (row.get("Kampagne") or "").strip()
        if not name or name.lower().startswith("gesamt"):
            continue
        c = {
            "name": name,
            "impressionen": parse_number(row.get("Impressionen", "0")),
            "klicks": parse_number(row.get("Klicks", "0")),
            "kosten": parse_number(row.get("Kosten", "0")),
            "conversions": parse_number(row.get("Conversions", "0")),
            "conv_wert": parse_number(row.get("Conv.-Wert", row.get("Conv-Wert", "0"))),
        }
        c["ctr"] = c["klicks"] / c["impressionen"] * 100 if c["impressionen"] else 0.0
        c["cpc"] = c["kosten"] / c["klicks"] if c["klicks"] else 0.0
        c["cpa"] = c["kosten"] / c["conversions"] if c["conversions"] else 0.0
        c["roas"] = c["conv_wert"] / c["kosten"] if c["kosten"] else 0.0
        campaigns.append(c)
    if not campaigns:
        raise SystemExit(f"{path}: keine Kampagnenzeilen gefunden.")

    total = {k: sum(c[k] for c in campaigns) for k in
             ("impressionen", "klicks", "kosten", "conversions", "conv_wert")}
    total["ctr"] = total["klicks"] / total["impressionen"] * 100 if total["impressionen"] else 0.0
    total["cpc"] = total["kosten"] / total["klicks"] if total["klicks"] else 0.0
    total["roas"] = total["conv_wert"] / total["kosten"] if total["kosten"] else 0.0
    return {"zeitraum": zeitraum, "campaigns": campaigns, "total": total}


# ------------------------------------------------------------ Formatieren

def de(value: float, decimals: int = 0) -> str:
    s = f"{value:,.{decimals}f}"
    return s.replace(",", " ").replace(".", ",").replace(" ", ".")


def eur(value: float) -> str:
    return de(value, 2) + " €"


def pct_delta(now: float, before: float) -> float | None:
    if not before:
        return None
    return (now - before) / before * 100


# ------------------------------------------------------------- Kommentar

def build_commentary(data: dict, prev: dict | None) -> list[str]:
    total = data["total"]
    campaigns = data["campaigns"]
    parts = []

    if prev:
        pt = prev["total"]
        d_kosten = pct_delta(total["kosten"], pt["kosten"])
        d_conv = pct_delta(total["conversions"], pt["conversions"])
        d_roas = pct_delta(total["roas"], pt["roas"])
        richtung = "gestiegen" if (d_roas or 0) >= 0 else "gesunken"
        parts.append(
            f"Im Berichtszeitraum wurden {eur(total['kosten'])} investiert "
            f"({d_kosten:+.1f} % gegenüber der Vorperiode) und {de(total['conversions'])} Conversions "
            f"erzielt ({d_conv:+.1f} %). Der ROAS ist auf {de(total['roas'], 2)} {richtung} "
            f"({d_roas:+.1f} %) — das Konto entwickelt sich damit "
            f"{'effizienter' if (d_roas or 0) >= 0 else 'weniger effizient'} als im Vormonat."
        )
    else:
        parts.append(
            f"Im Berichtszeitraum wurden {eur(total['kosten'])} investiert und "
            f"{de(total['conversions'])} Conversions mit einem Wert von {eur(total['conv_wert'])} "
            f"erzielt (ROAS {de(total['roas'], 2)})."
        )

    by_roas = sorted((c for c in campaigns if c["kosten"] > 0), key=lambda c: c["roas"], reverse=True)
    best, worst = by_roas[0], by_roas[-1]
    hinweis = " (Brand-Traffic ist naturgemäß am effizientesten)" if "brand" in best["name"].lower() else ""
    parts.append(
        f"Stärkste Kampagne nach Effizienz war \u201e{best['name']}\u201c mit einem ROAS von "
        f"{de(best['roas'], 2)}{hinweis}. Am schwächsten schnitt \u201e{worst['name']}\u201c ab "
        f"(ROAS {de(worst['roas'], 2)} bei {eur(worst['kosten'])} Kosten)."
    )

    weak = [c for c in by_roas if c["roas"] < 1.5 and c["kosten"] > total["kosten"] * 0.05]
    strong = [c for c in by_roas if c["roas"] > total["roas"]]
    if weak:
        namen = ", ".join(f"\u201e{c['name']}\u201c" for c in weak)
        empf = (f" Empfehlung: Budget schrittweise in die effizienteren Kampagnen "
                f"(z. B. \u201e{strong[1]['name'] if len(strong) > 1 else strong[0]['name']}\u201c) verlagern "
                f"oder Ausrichtung und Gebote der schwachen Kampagne überarbeiten.") if strong else ""
        parts.append(
            f"Unter der Effizienzschwelle (ROAS < 1,5) liegt: {namen}."
            f"{empf}"
        )

    if prev:
        prev_by_name = {c["name"]: c for c in prev["campaigns"]}
        for c in campaigns:
            p = prev_by_name.get(c["name"])
            if not p:
                continue
            d_cpc = pct_delta(c["cpc"], p["cpc"])
            if d_cpc is not None and abs(d_cpc) >= 15:
                parts.append(
                    f"Auffällig: Der durchschnittliche Klickpreis von \u201e{c['name']}\u201c hat sich um "
                    f"{d_cpc:+.1f} % auf {eur(c['cpc'])} verändert — "
                    f"{'Wettbewerbsdruck oder Gebotsanpassungen prüfen.' if d_cpc > 0 else 'die Effizienzgewinne können für zusätzliche Reichweite genutzt werden.'}"
                )
                break
    return parts


# ----------------------------------------------------------------- HTML

def kpi_tile(label: str, value: str, delta: float | None, invert: bool = False) -> str:
    if delta is None:
        badge = ""
    else:
        good = (delta >= 0) != invert
        cls = "delta-good" if good else "delta-bad"
        arrow = "▲" if delta >= 0 else "▼"
        badge = f'<span class="delta {cls}">{arrow} {abs(delta):.1f} % <em>vs. Vorperiode</em></span>'
    return (f'<div class="tile"><span class="tile-label">{html.escape(label)}</span>'
            f'<span class="tile-value">{value}</span>{badge}</div>')


def bar_chart(campaigns: list[dict]) -> str:
    ordered = sorted(campaigns, key=lambda c: c["kosten"], reverse=True)
    peak = ordered[0]["kosten"] or 1
    rows = []
    for c in ordered:
        w = max(c["kosten"] / peak * 100, 1.5)
        rows.append(
            f'<div class="bar-row" title="{html.escape(c["name"])}: {eur(c["kosten"])}, '
            f'ROAS {de(c["roas"], 2)}">'
            f'<span class="bar-name">{html.escape(c["name"])}</span>'
            f'<span class="bar-track"><span class="bar-fill" style="width:{w:.1f}%"></span></span>'
            f'<span class="bar-value">{eur(c["kosten"])}</span></div>'
        )
    return "\n".join(rows)


def table(campaigns: list[dict], total: dict) -> str:
    rows = []
    for c in sorted(campaigns, key=lambda c: c["kosten"], reverse=True):
        rows.append(
            f"<tr><td>{html.escape(c['name'])}</td><td>{de(c['impressionen'])}</td>"
            f"<td>{de(c['klicks'])}</td><td>{de(c['ctr'], 2)} %</td><td>{eur(c['cpc'])}</td>"
            f"<td>{eur(c['kosten'])}</td><td>{de(c['conversions'])}</td>"
            f"<td>{eur(c['cpa'])}</td><td>{de(c['roas'], 2)}</td></tr>"
        )
    rows.append(
        f"<tr class='total'><td>Gesamt</td><td>{de(total['impressionen'])}</td>"
        f"<td>{de(total['klicks'])}</td><td>{de(total['ctr'], 2)} %</td><td>{eur(total['cpc'])}</td>"
        f"<td>{eur(total['kosten'])}</td><td>{de(total['conversions'])}</td>"
        f"<td>{eur(total['kosten'] / total['conversions']) if total['conversions'] else '–'}</td>"
        f"<td>{de(total['roas'], 2)}</td></tr>"
    )
    return "\n".join(rows)


def render(kunde: str, zeitraum: str, data: dict, prev: dict | None) -> str:
    total = data["total"]
    pt = prev["total"] if prev else None
    tiles = "\n".join([
        kpi_tile("Werbekosten", eur(total["kosten"]),
                 pct_delta(total["kosten"], pt["kosten"]) if pt else None, invert=True),
        kpi_tile("Conversions", de(total["conversions"]),
                 pct_delta(total["conversions"], pt["conversions"]) if pt else None),
        kpi_tile("Umsatz (Conv.-Wert)", eur(total["conv_wert"]),
                 pct_delta(total["conv_wert"], pt["conv_wert"]) if pt else None),
        kpi_tile("ROAS", de(total["roas"], 2),
                 pct_delta(total["roas"], pt["roas"]) if pt else None),
    ])
    commentary = "\n".join(f"<p>{html.escape(p)}</p>" for p in build_commentary(data, prev))

    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Performance-Report · {html.escape(kunde)}</title>
<style>
:root {{
  color-scheme: light;
  --page: #f9f9f7; --surface: #fcfcfb;
  --ink: #0b0b0b; --ink-2: #52514e; --muted: #898781;
  --grid: #e1e0d9; --border: rgba(11,11,11,.10);
  --series-1: #2a78d6; --good: #006300; --bad: #d03b3b;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    color-scheme: dark;
    --page: #0d0d0d; --surface: #1a1a19;
    --ink: #ffffff; --ink-2: #c3c2b7; --muted: #898781;
    --grid: #2c2c2a; --border: rgba(255,255,255,.10);
    --series-1: #3987e5; --good: #0ca30c; --bad: #e66767;
  }}
}}
* {{ box-sizing: border-box; margin: 0; }}
body {{
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  background: var(--page); color: var(--ink);
  max-width: 880px; margin: 0 auto; padding: 2.5rem 1.2rem 4rem;
  line-height: 1.55;
}}
header {{ margin-bottom: 2rem; }}
h1 {{ font-size: 1.5rem; }}
.zeitraum {{ color: var(--ink-2); margin-top: .2rem; }}
h2 {{ font-size: 1.05rem; margin: 2.2rem 0 .9rem; }}
.tiles {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: .8rem; }}
.tile {{
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: .9rem 1rem; display: flex; flex-direction: column; gap: .15rem;
}}
.tile-label {{ font-size: .8rem; color: var(--ink-2); }}
.tile-value {{ font-size: 1.45rem; font-weight: 700; }}
.delta {{ font-size: .8rem; font-weight: 600; }}
.delta em {{ font-style: normal; font-weight: 400; color: var(--muted); }}
.delta-good {{ color: var(--good); }}
.delta-bad {{ color: var(--bad); }}
.card {{
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 1.1rem 1.2rem;
}}
.bar-row {{
  display: grid; grid-template-columns: minmax(120px, 220px) 1fr 110px;
  align-items: center; gap: .7rem; padding: .3rem 0; border-radius: 6px;
}}
.bar-row:hover {{ background: color-mix(in srgb, var(--series-1) 8%, transparent); }}
.bar-name {{ font-size: .85rem; color: var(--ink-2);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.bar-track {{ position: relative; height: 14px; }}
.bar-fill {{
  position: absolute; inset: 0 auto 0 0; background: var(--series-1);
  border-radius: 0 4px 4px 0; min-width: 3px;
}}
.bar-value {{ font-size: .85rem; text-align: right;
  font-variant-numeric: tabular-nums; }}
.kommentar p + p {{ margin-top: .8rem; }}
table {{ border-collapse: collapse; width: 100%; font-size: .85rem; }}
th, td {{ padding: .45rem .6rem; text-align: right;
  border-bottom: 1px solid var(--grid); font-variant-numeric: tabular-nums; }}
th:first-child, td:first-child {{ text-align: left; }}
th {{ color: var(--ink-2); font-weight: 600; }}
tr.total td {{ font-weight: 700; border-top: 2px solid var(--muted); }}
tr:hover td {{ background: color-mix(in srgb, var(--series-1) 6%, transparent); }}
.table-wrap {{ overflow-x: auto; }}
footer {{ margin-top: 3rem; color: var(--muted); font-size: .78rem; }}
@media print {{ body {{ max-width: none; }} .card, .tile {{ border-color: #ccc; }} }}
</style>
</head>
<body>
<header>
  <h1>Performance-Report · {html.escape(kunde)}</h1>
  <p class="zeitraum">Google Ads · {html.escape(zeitraum)}</p>
</header>

<section class="tiles">
{tiles}
</section>

<h2>Zusammenfassung &amp; Empfehlungen</h2>
<div class="card kommentar">
{commentary}
</div>

<h2>Kosten je Kampagne</h2>
<div class="card">
{bar_chart(data["campaigns"])}
</div>

<h2>Alle Kampagnen im Detail</h2>
<div class="card table-wrap">
<table>
<tr><th>Kampagne</th><th>Impr.</th><th>Klicks</th><th>CTR</th><th>Ø-CPC</th>
<th>Kosten</th><th>Conv.</th><th>Kosten/Conv.</th><th>ROAS</th></tr>
{table(data["campaigns"], total)}
</table>
</div>

<footer>Erstellt mit AdReport · Daten wurden lokal verarbeitet und nicht an Dritte übertragen.</footer>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("aktuell", type=Path, help="CSV-Export des Berichtszeitraums")
    ap.add_argument("vorperiode", type=Path, nargs="?", help="CSV-Export der Vorperiode (optional, für Deltas)")
    ap.add_argument("--kunde", default="Kunde", help="Kundenname für die Kopfzeile")
    ap.add_argument("--zeitraum", default="", help="Zeitraum-Text (Standard: aus dem CSV)")
    ap.add_argument("-o", "--output", type=Path, default=Path(__file__).parent / "dist" / "report.html")
    args = ap.parse_args()

    data = parse_export(args.aktuell)
    prev = parse_export(args.vorperiode) if args.vorperiode else None
    zeitraum = args.zeitraum or data["zeitraum"] or "Berichtszeitraum"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(args.kunde, zeitraum, data, prev))
    print(f"OK: {args.output} geschrieben ({len(data['campaigns'])} Kampagnen"
          f"{', mit Vorperioden-Vergleich' if prev else ''}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
