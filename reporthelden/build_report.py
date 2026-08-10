#!/usr/bin/env python3
"""ReportHelden: erzeugt aus Google-Ads-Kampagnen-CSV-Exporten einen fertigen
deutschen Kundenreport (eine HTML-Datei) — KPI-Kacheln, Kosten-Chart,
Mehrmonats-Trends, Kampagnentabelle und generierter Kommentar.

Local-first: läuft komplett offline mit der Python-Standardbibliothek.
Kundendaten verlassen den Rechner nicht. Ausnahme nur auf Wunsch: --ai
schickt die aggregierten Kampagnen-Kennzahlen (keine Rohdaten) an die
Claude-API, um den Kommentar sprachlich zu verfeinern.

Nutzung:
    # Einzelne Monate
    python3 build_report.py aktuell.csv [vorperiode.csv] --kunde "Beispiel GmbH"

    # Ordner mit Monats-Exporten (alphabetisch sortiert, neuester = aktuell)
    python3 build_report.py exports/ --kunde "Beispiel GmbH"

    # White-Label und KI-Feinschliff
    python3 build_report.py exports/ --brand agentur.json --ai
"""

import argparse
import base64
import csv
import html
import io
import json
import mimetypes
import os
import sys
from pathlib import Path

# Spalten-Mappings je Quelle: interner Name -> Liste möglicher Spalten-Präfixe.
SOURCES = {
    "Meta Ads": {
        "detect": ["Kampagnenname", "Ausgegebener Betrag"],
        "name": ["Kampagnenname"],
        "impressionen": ["Impressionen"],
        "klicks": ["Link-Klicks", "Klicks (alle)", "Klicks"],
        "kosten": ["Ausgegebener Betrag"],
        "conversions": ["Ergebnisse", "K\u00e4ufe", "Conversions"],
        "conv_wert": ["Conversion-Wert", "Kaufwert"],
    },
    "Google Ads": {
        "detect": ["Kampagne", "Kosten"],
        "name": ["Kampagne"],
        "impressionen": ["Impressionen"],
        "klicks": ["Klicks"],
        "kosten": ["Kosten"],
        "conversions": ["Conversions"],
        "conv_wert": ["Conv.-Wert", "Conv-Wert"],
    },
}

# Spalten, die einen Export in mehrere Zeilen je Kampagne aufteilen
# (Segmentierung nach Zeit, Gerät, Netzwerk …). Ihre Zeilen werden summiert.
SEGMENT_COLUMNS = ("Tag", "Woche", "Monat", "Quartal", "Jahr", "Wochentag",
                   "Gerät", "Netzwerk", "Klicktyp", "Anzeigengruppe", "Datum")

ADDITIVE = ("impressionen", "klicks", "kosten", "conversions", "conv_wert")


def is_total_row(name: str) -> bool:
    """Summenzeile der Exporte erkennen — ohne Kampagnen zu treffen,
    die zufällig mit „Gesamt…" beginnen (z. B. „Gesamtpaket Brand")."""
    n = name.strip().lower()
    return n in ("gesamt", "summe", "total") or n.startswith(
        ("gesamt:", "gesamt —", "gesamt -", "ergebnisse aus", "summe:"))


def derive(c: dict) -> dict:
    """Verhältniskennzahlen aus den Summen berechnen (nie Mittelwerte mitteln)."""
    c["ctr"] = c["klicks"] / c["impressionen"] * 100 if c["impressionen"] else 0.0
    c["cpc"] = c["kosten"] / c["klicks"] if c["klicks"] else 0.0
    c["cpa"] = c["kosten"] / c["conversions"] if c["conversions"] else 0.0
    c["roas"] = c["conv_wert"] / c["kosten"] if c["kosten"] else 0.0
    return c


def aggregate(campaigns: list[dict]) -> list[dict]:
    """Mehrere Zeilen derselben Kampagne (segmentierter Export) zusammenfassen."""
    merged: dict[str, dict] = {}
    for c in campaigns:
        target = merged.get(c["name"])
        if target is None:
            merged[c["name"]] = dict(c)
            continue
        for key in ADDITIVE:
            target[key] += c[key]
    return [derive(c) for c in merged.values()]


DEFAULT_BRAND = {
    "agentur": "",
    "logo": "",
    "accent": "#2a78d6",
    "accent_dark": "#3987e5",
    "footer": "Erstellt mit ReportHelden · Daten wurden lokal verarbeitet und nicht an Dritte übertragen.",
}


# ---------------------------------------------------------------- Parsen

def parse_number(raw: str) -> float:
    """'1.234,56' / '12,3 %' / '1234.56' -> float."""
    s = raw.strip().replace(" ", "").replace("€", "").replace("%", "").strip()
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
    header_idx, source = None, None
    for i, l in enumerate(lines):
        for src, spec in SOURCES.items():
            if all(marker in l for marker in spec["detect"]):
                header_idx, source = i, src
                break
        if source:
            break
    if header_idx is None:
        raise SystemExit(f"{path}: keine bekannte Kopfzeile gefunden "
                         f"(unterst\u00fctzt: {', '.join(SOURCES)}).")
    spec = SOURCES[source]

    zeitraum = lines[header_idx - 1].strip() if header_idx >= 2 else ""
    body = "\n".join(lines[header_idx:])
    delimiter = max([",", ";", "\t"], key=lines[header_idx].count)
    reader = csv.DictReader(io.StringIO(body), delimiter=delimiter)
    fields = reader.fieldnames or []

    def col(key: str) -> str | None:
        for prefix in spec[key]:
            if prefix in fields:
                return prefix
        for prefix in spec[key]:
            for f in fields:
                if f.startswith(prefix):
                    return f
        return None

    cols = {k: col(k) for k in ("name", "impressionen", "klicks", "kosten",
                                "conversions", "conv_wert")}
    known = {c for c in cols.values() if c}
    segments = [f for f in fields
                if f and f not in known
                and any(f.startswith(seg) for seg in SEGMENT_COLUMNS)]
    missing = [k for k in ("name", "kosten") if not cols[k]]
    if missing:
        raise SystemExit(f"{path} ({source}): Spalten fehlen: {', '.join(missing)}")

    def val(row: dict, key: str) -> float:
        return parse_number(row.get(cols[key] or "", "0") or "0")

    campaigns = []
    for row in reader:
        name = (row.get(cols["name"]) or "").strip()
        if not name or is_total_row(name):
            continue
        c = {
            "name": name,
            "impressionen": val(row, "impressionen"),
            "klicks": val(row, "klicks"),
            "kosten": val(row, "kosten"),
            "conversions": val(row, "conversions"),
            "conv_wert": val(row, "conv_wert"),
        }
        campaigns.append(derive(c))
    if not campaigns:
        raise SystemExit(f"{path}: keine Kampagnenzeilen gefunden.")

    campaigns = aggregate(campaigns)

    total = {k: sum(c[k] for c in campaigns) for k in
             ("impressionen", "klicks", "kosten", "conversions", "conv_wert")}
    total["ctr"] = total["klicks"] / total["impressionen"] * 100 if total["impressionen"] else 0.0
    total["cpc"] = total["kosten"] / total["klicks"] if total["klicks"] else 0.0
    total["roas"] = total["conv_wert"] / total["kosten"] if total["kosten"] else 0.0
    return {"zeitraum": zeitraum, "campaigns": campaigns, "total": total, "source": source,
            "segments": segments,
            "label": path.stem.replace("kampagnen-", "").replace("meta-", "").replace("-", " ")}


def load_inputs(paths: list[Path]) -> list[dict]:
    """Ein Ordner (alle *.csv, sortiert) oder 1-2 CSV-Dateien -> Historie,
    ältester zuerst, neuester = Berichtszeitraum."""
    if len(paths) == 1 and paths[0].is_dir():
        files = sorted(paths[0].glob("*.csv"))
        if not files:
            raise SystemExit(f"{paths[0]}: keine CSV-Dateien gefunden.")
        return [parse_export(f) for f in files]
    if len(paths) == 2:
        return [parse_export(paths[1]), parse_export(paths[0])]
    return [parse_export(paths[0])]


def load_brand(path: Path | None) -> dict:
    brand = dict(DEFAULT_BRAND)
    if path:
        brand.update(json.loads(path.read_text()))
    return brand


def logo_data_uri(logo: str) -> str:
    """Lokale Logodatei als data:-URI einbetten; URLs unverändert lassen."""
    if not logo:
        return ""
    if logo.startswith(("http://", "https://", "data:")):
        return logo
    p = Path(logo)
    if not p.exists():
        print(f"Warnung: Logo {logo} nicht gefunden — wird ausgelassen.", file=sys.stderr)
        return ""
    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


# ------------------------------------------------------------ Formatieren

def de(value: float, decimals: int = 0) -> str:
    s = f"{value:,.{decimals}f}"
    return s.replace(",", " ").replace(".", ",").replace(" ", ".")


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
        f"Stärkste Kampagne nach Effizienz war „{best['name']}“ mit einem ROAS von "
        f"{de(best['roas'], 2)}{hinweis}. Am schwächsten schnitt „{worst['name']}“ ab "
        f"(ROAS {de(worst['roas'], 2)} bei {eur(worst['kosten'])} Kosten)."
    )

    weak = [c for c in by_roas if c["roas"] < 1.5 and c["kosten"] > total["kosten"] * 0.05]
    strong = [c for c in by_roas if c["roas"] > total["roas"]]
    if weak:
        namen = ", ".join(f"„{c['name']}“" for c in weak)
        empf = (f" Empfehlung: Budget schrittweise in die effizienteren Kampagnen "
                f"(z. B. „{strong[1]['name'] if len(strong) > 1 else strong[0]['name']}“) verlagern "
                f"oder Ausrichtung und Gebote der schwachen Kampagne überarbeiten.") if strong else ""
        parts.append(f"Unter der Effizienzschwelle (ROAS < 1,5) liegt: {namen}.{empf}")

    if prev:
        prev_by_name = {c["name"]: c for c in prev["campaigns"]}
        for c in campaigns:
            p = prev_by_name.get(c["name"])
            if not p:
                continue
            d_cpc = pct_delta(c["cpc"], p["cpc"])
            if d_cpc is not None and abs(d_cpc) >= 15:
                parts.append(
                    f"Auffällig: Der durchschnittliche Klickpreis von „{c['name']}“ hat sich um "
                    f"{d_cpc:+.1f} % auf {eur(c['cpc'])} verändert — "
                    f"{'Wettbewerbsdruck oder Gebotsanpassungen prüfen.' if d_cpc > 0 else 'die Effizienzgewinne können für zusätzliche Reichweite genutzt werden.'}"
                )
                break
    return parts


def ai_refine(parts: list[str], data: dict, kunde: str) -> list[str]:
    """Optionaler Feinschliff des Kommentars über die Claude-API (claude-opus-5).

    Gesendet werden nur die aggregierten Kennzahlen und der vorformulierte
    Kommentar — keine Rohdaten. Bei jedem Fehler bleibt der regelbasierte
    Kommentar unverändert bestehen.
    """
    try:
        import anthropic
    except ImportError:
        print("Warnung: --ai benötigt das Paket 'anthropic' (pip install anthropic) — "
              "verwende regelbasierten Kommentar.", file=sys.stderr)
        return parts

    kennzahlen = [
        {"kampagne": c["name"], "kosten": round(c["kosten"], 2),
         "conversions": c["conversions"], "roas": round(c["roas"], 2),
         "cpc": round(c["cpc"], 2), "ctr": round(c["ctr"], 2)}
        for c in data["campaigns"]
    ]
    try:
        client = anthropic.Anthropic()
        response = client.beta.messages.create(
            model="claude-opus-5",
            max_tokens=2000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=(
                "Du bist ein erfahrener deutscher PPC-Berater und verfeinerst den "
                "Kommentar eines Google-Ads-Kundenreports. Behalte alle Zahlen und "
                "Kernaussagen exakt bei, verbessere Sprache, Fluss und Kundennutzen. "
                "Antworte ausschließlich mit den überarbeiteten Absätzen, getrennt "
                "durch Leerzeilen — keine Überschriften, keine Meta-Kommentare."
            ),
            messages=[{
                "role": "user",
                "content": (
                    f"Kunde: {kunde}\n\nKennzahlen (aggregiert):\n"
                    f"{json.dumps(kennzahlen, ensure_ascii=False)}\n\n"
                    f"Bisheriger Kommentar:\n\n" + "\n\n".join(parts)
                ),
            }],
        )
        if response.stop_reason == "refusal":
            print("Warnung: KI-Feinschliff abgelehnt — verwende regelbasierten Kommentar.",
                  file=sys.stderr)
            return parts
        text = next((b.text for b in response.content if b.type == "text"), "")
        refined = [p.strip() for p in text.split("\n\n") if p.strip()]
        return refined or parts
    except Exception as exc:
        print(f"Warnung: KI-Feinschliff fehlgeschlagen ({type(exc).__name__}) — "
              f"verwende regelbasierten Kommentar.", file=sys.stderr)
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


def sparkline(values: list[float], labels: list[str], fmt) -> str:
    """Kleine SVG-Trendlinie: 2px-Linie, Endpunkt-Marker, Erst-/Letztwert beschriftet."""
    w, h, pad = 260, 56, 8
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1.0
    n = len(values)
    pts = []
    for i, v in enumerate(values):
        x = pad + (w - 2 * pad) * (i / (n - 1))
        y = h - pad - (h - 2 * pad) * ((v - lo) / span)
        pts.append((x, y))
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    lx, ly = pts[-1]
    title = " · ".join(f"{l}: {fmt(v)}" for l, v in zip(labels, values))
    return (
        f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{html.escape(title)}">'
        f'<title>{html.escape(title)}</title>'
        f'<polyline points="{poly}" fill="none" stroke="var(--accent)" stroke-width="2" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
        f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="4" fill="var(--accent)"/>'
        f'</svg>'
    )


def trend_section(history: list[dict]) -> str:
    """Small Multiples für Kosten, Conversions, ROAS über alle Monate."""
    if len(history) < 3:
        return ""
    labels = [h["label"] for h in history]
    metrics = [
        ("Kosten", [h["total"]["kosten"] for h in history], eur),
        ("Conversions", [h["total"]["conversions"] for h in history], lambda v: de(v)),
        ("ROAS", [h["total"]["roas"] for h in history], lambda v: de(v, 2)),
    ]
    cells = []
    for name, values, fmt in metrics:
        cells.append(
            f'<div class="trend-cell"><div class="trend-head">'
            f'<span class="trend-name">{name}</span>'
            f'<span class="trend-value">{fmt(values[-1])}</span></div>'
            f'{sparkline(values, labels, fmt)}'
            f'<div class="trend-axis"><span>{html.escape(labels[0])}</span>'
            f'<span>{html.escape(labels[-1])}</span></div></div>'
        )
    return (f'<h2>Entwicklung über {len(history)} Monate</h2>'
            f'<div class="card trend-grid">{"".join(cells)}</div>')


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


def render(kunde: str, zeitraum: str, history: list[dict], brand: dict,
           commentary_parts: list[str]) -> str:
    data = history[-1]
    prev = history[-2] if len(history) >= 2 else None
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
    commentary = "\n".join(f"<p>{html.escape(p)}</p>" for p in commentary_parts)

    logo_uri = logo_data_uri(brand.get("logo", ""))
    logo_html = f'<img class="logo" src="{logo_uri}" alt="">' if logo_uri else ""
    agentur = html.escape(brand.get("agentur", ""))
    agentur_html = f'<span class="agentur">{agentur}</span>' if agentur else ""

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
  --accent: {brand["accent"]}; --good: #006300; --bad: #d03b3b;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    color-scheme: dark;
    --page: #0d0d0d; --surface: #1a1a19;
    --ink: #ffffff; --ink-2: #c3c2b7; --muted: #898781;
    --grid: #2c2c2a; --border: rgba(255,255,255,.10);
    --accent: {brand["accent_dark"]}; --good: #0ca30c; --bad: #e66767;
  }}
}}
* {{ box-sizing: border-box; margin: 0; }}
body {{
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  background: var(--page); color: var(--ink);
  max-width: 880px; margin: 0 auto; padding: 2.5rem 1.2rem 4rem;
  line-height: 1.55;
}}
header {{ margin-bottom: 2rem; display: flex; align-items: center; gap: 1rem; }}
.logo {{ height: 44px; width: auto; }}
h1 {{ font-size: 1.5rem; }}
.zeitraum {{ color: var(--ink-2); margin-top: .2rem; }}
.agentur {{ margin-left: auto; color: var(--muted); font-size: .85rem; }}
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
.trend-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.2rem; }}
.trend-head {{ display: flex; justify-content: space-between; align-items: baseline; }}
.trend-name {{ font-size: .85rem; color: var(--ink-2); }}
.trend-value {{ font-weight: 700; font-variant-numeric: tabular-nums; }}
.trend-cell svg {{ width: 100%; height: auto; margin-top: .3rem; }}
.trend-axis {{ display: flex; justify-content: space-between;
  font-size: .72rem; color: var(--muted); }}
.bar-row {{
  display: grid; grid-template-columns: minmax(120px, 220px) 1fr 110px;
  align-items: center; gap: .7rem; padding: .3rem 0; border-radius: 6px;
}}
.bar-row:hover {{ background: color-mix(in srgb, var(--accent) 8%, transparent); }}
.bar-name {{ font-size: .85rem; color: var(--ink-2);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.bar-track {{ position: relative; height: 14px; }}
.bar-fill {{
  position: absolute; inset: 0 auto 0 0; background: var(--accent);
  border-radius: 0 4px 4px 0; min-width: 3px;
}}
.bar-value {{ font-size: .85rem; text-align: right; font-variant-numeric: tabular-nums; }}
.kommentar p + p {{ margin-top: .8rem; }}
table {{ border-collapse: collapse; width: 100%; font-size: .85rem; }}
th, td {{ padding: .45rem .6rem; text-align: right;
  border-bottom: 1px solid var(--grid); font-variant-numeric: tabular-nums; }}
th:first-child, td:first-child {{ text-align: left; }}
th {{ color: var(--ink-2); font-weight: 600; }}
tr.total td {{ font-weight: 700; border-top: 2px solid var(--muted); }}
tr:hover td {{ background: color-mix(in srgb, var(--accent) 6%, transparent); }}
.table-wrap {{ overflow-x: auto; }}
footer {{ margin-top: 3rem; color: var(--muted); font-size: .78rem; }}
@media print {{ body {{ max-width: none; }} .card, .tile {{ border-color: #ccc; }} }}
</style>
</head>
<body>
<header>
  {logo_html}
  <div>
    <h1>Performance-Report · {html.escape(kunde)}</h1>
    <p class="zeitraum">{html.escape(" + ".join(dict.fromkeys(h["source"] for h in history)))} · {html.escape(zeitraum)}</p>
  </div>
  {agentur_html}
</header>

<section class="tiles">
{tiles}
</section>

<h2>Zusammenfassung &amp; Empfehlungen</h2>
<div class="card kommentar">
{commentary}
</div>

{trend_section(history)}

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

<footer>{html.escape(brand["footer"])}</footer>
</body>
</html>
"""


BROWSER_CANDIDATES = [
    "chromium", "chromium-browser", "google-chrome", "google-chrome-stable",
    "chrome", "msedge", "microsoft-edge", "brave-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


def find_browser() -> str | None:
    """Findet einen Chromium-basierten Browser fuer den PDF-Export.

    Reihenfolge: Umgebungsvariable REPORTHELDEN_BROWSER, dann PATH,
    dann bekannte Installationspfade (macOS/Windows).
    """
    import shutil
    override = os.environ.get("REPORTHELDEN_BROWSER")
    if override and Path(override).exists():
        return override
    for cand in BROWSER_CANDIDATES:
        if Path(cand).exists():
            return cand
        hit = shutil.which(cand)
        if hit:
            return hit
    return None


def export_pdf(html_path: Path, pdf_path: Path) -> bool:
    """Rendert den HTML-Report per Headless-Browser als PDF (ohne Druckdialog)."""
    import subprocess
    browser = find_browser()
    if not browser:
        print("Warnung: kein Chrome/Edge/Chromium gefunden — PDF uebersprungen. "
              "Alternativ REPORTHELDEN_BROWSER auf den Browser-Pfad setzen "
              "oder den Report im Browser drucken.", file=sys.stderr)
        return False
    args = [browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path}", html_path.resolve().as_uri()]
    for extra in ([], ["--no-sandbox"]):
        try:
            r = subprocess.run(args + extra, capture_output=True, timeout=60)
            if r.returncode == 0 and pdf_path.exists() and pdf_path.stat().st_size > 0:
                return True
        except (subprocess.TimeoutExpired, OSError):
            break
    print("Warnung: PDF-Export fehlgeschlagen — HTML-Report liegt trotzdem vor.",
          file=sys.stderr)
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", type=Path, nargs="+",
                    help="CSV-Export(e): aktuell [vorperiode] — oder ein Ordner mit Monats-CSVs")
    ap.add_argument("--kunde", default="Kunde", help="Kundenname für die Kopfzeile")
    ap.add_argument("--zeitraum", default="", help="Zeitraum-Text (Standard: aus dem CSV)")
    ap.add_argument("--brand", type=Path, help="JSON mit agentur, logo, accent, accent_dark, footer")
    ap.add_argument("--ai", action="store_true",
                    help="Kommentar per Claude-API verfeinern (benötigt ANTHROPIC_API_KEY)")
    ap.add_argument("--pdf", action="store_true",
                    help="zusaetzlich ein PDF erzeugen (nutzt installiertes Chrome/Edge, ohne Druckdialog)")
    ap.add_argument("-o", "--output", type=Path,
                    default=Path(__file__).parent / "dist" / "report.html")
    args = ap.parse_args()

    history = load_inputs(args.inputs)
    for h in history:
        if h.get("segments"):
            print(f"Hinweis: Export ist nach {', '.join(h['segments'])} segmentiert — "
                  f"Zeilen wurden je Kampagne zusammengefasst.", file=sys.stderr)
    data = history[-1]
    prev = history[-2] if len(history) >= 2 else None
    zeitraum = args.zeitraum or data["zeitraum"] or "Berichtszeitraum"
    brand = load_brand(args.brand)

    commentary = build_commentary(data, prev)
    if args.ai:
        commentary = ai_refine(commentary, data, args.kunde)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(args.kunde, zeitraum, history, brand, commentary))
    extras = []
    if args.pdf and export_pdf(args.output, args.output.with_suffix(".pdf")):
        extras.append("PDF")
    if len(history) >= 3:
        extras.append(f"{len(history)}-Monats-Trend")
    if prev:
        extras.append("Vorperioden-Vergleich")
    if brand.get("agentur") or brand.get("logo"):
        extras.append("White-Label")
    print(f"OK: {args.output} geschrieben ({len(data['campaigns'])} Kampagnen"
          f"{', ' + ', '.join(extras) if extras else ''}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
