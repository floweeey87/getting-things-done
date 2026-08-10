#!/usr/bin/env python3
"""Veröffentlicht die ReportHelden-Inhalte auf dem WordPress unter reporthelden.de.

Überträgt die SEO-Artikel aus ``marketing/`` als Beiträge und optional den
Inhalt der Landingpage als Seite.

Sicherheitsprinzipien:

* **Trockenlauf ist Voreinstellung** — geschrieben wird nur mit ``--apply``.
* **Entwurf ist Voreinstellung** — Beiträge landen als ``draft``; erst
  ``--status publish`` stellt sie live.
* **Zugangsdaten nur aus der Umgebung** (``WP_USER``, ``WP_APP_PASSWORD``).
* **Idempotent:** Existiert ein Beitrag mit dem Slug, wird er aktualisiert
  statt ein Duplikat anzulegen.
* Interne Notizen (die ``Ziel-Keywords``-Zeile) werden nie mitveröffentlicht.

Nutzung:

    export WP_USER='Achim'
    export WP_APP_PASSWORD='xxxx xxxx xxxx xxxx xxxx xxxx'

    python3 publish_wp.py                    # Trockenlauf
    python3 publish_wp.py --apply            # als Entwürfe anlegen
    python3 publish_wp.py --apply --status publish
"""

import argparse
import base64
import html as html_mod
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
DEFAULT_SITE = "https://reporthelden.de"

ARTICLES = [
    ("seo-google-ads-report-erstellen.md", "google-ads-report-erstellen"),
    ("seo-agencyanalytics-alternative.md", "agencyanalytics-alternative"),
]

# Eigenständige HTML-Seiten → WordPress-Seiten (Slug, Titel)
PAGES = [
    ("index.html", "start", "ReportHelden — Kundenreports in 60 Sekunden"),
    ("demo-report.html", "beispiel-report", "Beispiel-Report"),
    ("impressum.html", "impressum", "Impressum"),
    ("datenschutz.html", "datenschutz", "Datenschutzerklärung"),
]

# Repo-Dateinamen → Pfade auf der Site
LINK_MAP = {
    "index.html": "/",
    "demo-report.html": "/beispiel-report/",
    "impressum.html": "/impressum/",
    "datenschutz.html": "/datenschutz/",
}


def fail(msg: str):
    print(f"Fehler: {msg}", file=sys.stderr)
    sys.exit(1)


# ------------------------------------------------------------ Markdown → HTML

def inline(text: str) -> str:
    """Fett, kursiv, Code und Links — der Rest wird escapt."""
    tokens: list[str] = []

    def stash(rendered: str) -> str:
        tokens.append(rendered)
        return f"\x00{len(tokens) - 1}\x00"

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
                  lambda m: stash(f'<a href="{html_mod.escape(rewrite_link(m.group(2)))}">'
                                  f"{html_mod.escape(m.group(1))}</a>"), text)
    text = re.sub(r"`([^`]+)`",
                  lambda m: stash(f"<code>{html_mod.escape(m.group(1))}</code>"), text)
    text = re.sub(r"\*\*([^*]+)\*\*",
                  lambda m: stash(f"<strong>{html_mod.escape(m.group(1))}</strong>"), text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)",
                  lambda m: stash(f"<em>{html_mod.escape(m.group(1))}</em>"), text)
    out = html_mod.escape(text)
    return re.sub(r"\x00(\d+)\x00", lambda m: tokens[int(m.group(1))], out)


def rewrite_link(href: str) -> str:
    """Repo-interne Pfade in Site-URLs übersetzen."""
    if href.startswith("../landing/index.html"):
        return "/"
    if href.startswith(("http://", "https://", "/", "#", "mailto:")):
        return href
    return "/" + href.lstrip("./")


def markdown_to_html(md: str) -> tuple[str, str, str]:
    """-> (titel, html, auszug). Entfernt interne Notizen und Trennlinien."""
    lines = md.splitlines()
    title = ""
    body: list[str] = []
    excerpt = ""
    i, para, list_items, table = 0, [], [], []

    def flush_para():
        nonlocal excerpt
        if para:
            text = " ".join(para).strip()
            body.append(f"<p>{inline(text)}</p>")
            if not excerpt:
                excerpt = re.sub(r"[*`\[\]]|\(.*?\)", "", text)[:220].strip()
            para.clear()

    def flush_list():
        if list_items:
            body.append("<ul>\n" + "\n".join(f"<li>{inline(x)}</li>" for x in list_items) + "\n</ul>")
            list_items.clear()

    def flush_table():
        if not table:
            return
        head, *rows = table
        rows = [r for r in rows if not set(r.replace("|", "").strip()) <= {"-", " ", ":"}]
        cells = lambda row: [c.strip() for c in row.strip().strip("|").split("|")]
        out = ["<figure class=\"wp-block-table\"><table><thead><tr>"]
        out += [f"<th>{inline(c)}</th>" for c in cells(head)]
        out.append("</tr></thead><tbody>")
        for r in rows:
            out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells(r)) + "</tr>")
        out.append("</tbody></table></figure>")
        body.append("".join(out))
        table.clear()

    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()

        # interne Notiz (Ziel-Keywords) niemals veröffentlichen
        if stripped.startswith("*Ziel-Keywords:"):
            i += 1
            continue
        if stripped in ("---", "***", "___"):
            flush_para(); flush_list(); flush_table()
            i += 1
            continue
        if stripped.startswith("|"):
            flush_para(); flush_list()
            table.append(stripped)
            i += 1
            continue
        flush_table()
        if stripped.startswith("# "):
            flush_para(); flush_list()
            title = stripped[2:].strip()
        elif stripped.startswith("### "):
            flush_para(); flush_list()
            body.append(f"<h3>{inline(stripped[4:])}</h3>")
        elif stripped.startswith("## "):
            flush_para(); flush_list()
            body.append(f"<h2>{inline(stripped[3:])}</h2>")
        elif stripped.startswith("> "):
            flush_para(); flush_list()
            quote = [stripped[2:]]
            while i + 1 < len(lines) and lines[i + 1].strip().startswith(">"):
                i += 1
                quote.append(lines[i].strip().lstrip(">").strip())
            body.append(f"<blockquote class=\"wp-block-quote\"><p>{inline(' '.join(quote))}</p></blockquote>")
        elif re.match(r"^[-*] ", stripped):
            flush_para()
            list_items.append(stripped[2:])
        elif re.match(r"^\d+\. ", stripped):
            flush_para(); flush_list()
            items = []
            while i < len(lines) and re.match(r"^\d+\. ", lines[i].strip()):
                items.append(re.sub(r"^\d+\. ", "", lines[i].strip()))
                i += 1
            i -= 1
            body.append("<ol>\n" + "\n".join(f"<li>{inline(x)}</li>" for x in items) + "\n</ol>")
        elif not stripped:
            flush_para(); flush_list()
        else:
            para.append(stripped)
        i += 1

    flush_para(); flush_list(); flush_table()
    return title, "\n\n".join(body), excerpt


# --------------------------------------------- Standalone-HTML → WP-Block

WRAPPER = "rh-page"


def _scope_selector(sel: str) -> str:
    """Einen Selektor unter den Wrapper sperren, damit er das Theme nicht trifft."""
    out = []
    for part in sel.split(","):
        part = part.strip()
        if not part:
            continue
        if part in ("body", "html", ":root") or part.startswith(":root"):
            out.append(f".{WRAPPER}")
        elif part == "*":
            out.append(f".{WRAPPER}, .{WRAPPER} *")
        else:
            out.append(f".{WRAPPER} {part}")
    return ", ".join(out)


def _scope_css(css: str) -> str:
    """CSS-Regeln rekursiv unter den Wrapper sperren (inkl. @media-Blöcken)."""
    out, i, n = [], 0, len(css)
    while i < n:
        brace = css.find("{", i)
        if brace == -1:
            break
        prelude = css[i:brace].strip()
        depth, j = 1, brace + 1
        while j < n and depth:
            depth += (css[j] == "{") - (css[j] == "}")
            j += 1
        block = css[brace + 1:j - 1]
        if prelude.startswith("@"):
            inner = _scope_css(block) if prelude.startswith("@media") else block
            out.append(f"{prelude} {{\n{inner}\n}}")
        else:
            out.append(f"{_scope_selector(prelude)} {{{block}}}")
        i = j
    return "\n".join(out)


def standalone_to_block(path: Path, link_map: dict[str, str]) -> str:
    """Eigenständige HTML-Seite in einen themesicheren WordPress-Block wandeln."""
    raw = path.read_text(encoding="utf-8")
    style = re.search(r"<style>(.*?)</style>", raw, re.S)
    body = re.search(r"<body>(.*)</body>", raw, re.S)
    if not body:
        fail(f"{path.name}: kein <body> gefunden.")
    content = body.group(1).strip()
    for old, new in link_map.items():
        content = content.replace(f'href="{old}"', f'href="{new}"')
    css = _scope_css(style.group(1)) if style else ""
    return (f"<!-- wp:html -->\n<style>\n{css}\n</style>\n"
            f'<div class="{WRAPPER}">\n{content}\n</div>\n<!-- /wp:html -->')


# ----------------------------------------------------------------- WordPress

class WordPress:
    def __init__(self, site: str, user: str, password: str):
        self.api = site.rstrip("/") + "/wp-json/wp/v2"
        token = base64.b64encode(f"{user}:{password.replace(' ', '')}".encode()).decode()
        self.headers = {"Authorization": f"Basic {token}",
                        "Content-Type": "application/json",
                        "User-Agent": "reporthelden-publisher/1.0"}

    def _req(self, method: str, path: str, body: dict | None = None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.api + path, data=data,
                                     headers=self.headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:400]
            if e.code in (401, 403):
                fail(f"Anmeldung abgelehnt ({e.code}). Benutzername und "
                     f"Anwendungspasswort prüfen; ein Sicherheits-Plugin darf die "
                     f"REST-API nicht blockieren.\n{detail}")
            fail(f"{method} {path} → HTTP {e.code}\n{detail}")
        except urllib.error.URLError as e:
            fail(f"Site nicht erreichbar: {e.reason}")

    def whoami(self):
        return self._req("GET", "/users/me?context=edit")

    def find(self, kind: str, slug: str):
        q = urllib.parse.urlencode({"slug": slug, "status": "any", "context": "edit"})
        hits = self._req("GET", f"/{kind}?{q}")
        return hits[0] if hits else None

    def upsert(self, kind: str, slug: str, fields: dict):
        existing = self.find(kind, slug)
        if existing:
            return self._req("POST", f"/{kind}/{existing['id']}", fields), "aktualisiert"
        return self._req("POST", f"/{kind}", {**fields, "slug": slug}), "neu angelegt"


# ---------------------------------------------------------------------- Main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--site", default=os.environ.get("WP_SITE", DEFAULT_SITE))
    ap.add_argument("--apply", action="store_true", help="wirklich übertragen")
    ap.add_argument("--status", choices=("draft", "publish"), default="draft",
                    help="Status der Beiträge (Standard: draft)")
    ap.add_argument("--only", choices=("posts", "pages"),
                    help="nur Beiträge oder nur Seiten übertragen (Standard: beides)")
    ap.add_argument("--preview", type=Path,
                    help="erzeugtes HTML zur Kontrolle in diese Datei schreiben")
    args = ap.parse_args()

    prepared, pages = [], []
    if args.only != "pages":
      for filename, slug in ARTICLES:
        path = BASE / "marketing" / filename
        if not path.exists():
            fail(f"{path} nicht gefunden.")
        title, content, excerpt = markdown_to_html(path.read_text(encoding="utf-8"))
        if "Ziel-Keywords" in content:
            fail(f"{filename}: interne Notiz würde veröffentlicht — abgebrochen.")
        prepared.append({"slug": slug, "title": title, "content": content,
                         "excerpt": excerpt, "quelle": filename})

    if args.only != "posts":
        for filename, slug, title in PAGES:
            path = BASE / "landing" / filename
            if not path.exists():
                fail(f"{path} nicht gefunden.")
            block = standalone_to_block(path, LINK_MAP)
            if "PLATZHALTER" in block or re.search(r"\[[A-ZÄÖÜ][^\]]{3,}\]", block):
                fail(f"{filename}: enthält noch Platzhalter — erst ausfüllen "
                     f"(python3 preflight.py zeigt sie).")
            pages.append({"slug": slug, "title": title, "content": block,
                          "excerpt": "", "quelle": filename})

    print(f"\nReportHelden · Veröffentlichung nach {args.site}\n")
    if pages:
        print("  Seiten:")
        for a in pages:
            print(f"    {a['slug']:18s} {len(a['content']):6d} Zeichen  ← {a['quelle']}")
        print()
    if prepared:
        print("  Beiträge:")
    for a in prepared:
        print(f"  {a['slug']}")
        print(f"    Titel  : {a['title'][:72]}")
        print(f"    Inhalt : {len(a['content'])} Zeichen HTML aus {a['quelle']}")
        print(f"    Auszug : {a['excerpt'][:80]}…")

    if args.preview:
        args.preview.write_text("\n\n<hr>\n\n".join(
            f"<h1>{a['title']}</h1>\n{a['content']}" for a in pages + prepared),
            encoding="utf-8")
        print(f"\n  Vorschau geschrieben: {args.preview}")

    if not args.apply:
        print("\nTrockenlauf — nichts übertragen. Mit --apply schreiben "
              "(Status: Entwurf, sofern nicht --status publish).\n")
        return 0

    user, password = os.environ.get("WP_USER"), os.environ.get("WP_APP_PASSWORD")
    if not user or not password:
        fail("WP_USER und WP_APP_PASSWORD müssen gesetzt sein.")

    wp = WordPress(args.site, user, password)
    me = wp.whoami()
    print(f"\nAngemeldet als {me.get('name')} (ID {me.get('id')})")

    for kind, items in (("pages", pages), ("posts", prepared)):
        for a in items:
            fields = {"title": a["title"], "content": a["content"],
                      "status": args.status}
            if a["excerpt"]:
                fields["excerpt"] = a["excerpt"]
            result, action = wp.upsert(kind, a["slug"], fields)
            print(f"  {kind[:-1]} {a['slug']}: {action} → {result.get('link')} "
                  f"[{result.get('status')}]")

    print(f"\nFertig. Status: {args.status}."
          + (" Beiträge im WP-Backend prüfen und veröffentlichen.\n"
             if args.status == "draft" else "\n"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
