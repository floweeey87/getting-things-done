#!/usr/bin/env python3
"""Biolink: erzeugt aus profile.json eine selbst gehostete Link-in-Bio-Seite.

Nur Python-Standardbibliothek. Ausgabe: dist/index.html (eine Datei, keine
Abhängigkeiten) — deploybar auf GitHub Pages, Cloudflare Pages oder jedem
Webspace.
"""

import html
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent


def esc(value: str) -> str:
    return html.escape(str(value), quote=True)


def render(profile: dict) -> str:
    theme = profile.get("theme", {})
    accent = theme.get("accent", "#6c5ce7")
    accent_dark = theme.get("accent_dark", "#a29bfe")

    if profile.get("avatar_url"):
        avatar = f'<img class="avatar" src="{esc(profile["avatar_url"])}" alt="{esc(profile["name"])}">'
    else:
        avatar = f'<div class="avatar avatar-initials">{esc(profile.get("initials", "?"))}</div>'

    links = "\n".join(
        f'<a class="link" href="{esc(l["url"])}" rel="me noopener">{esc(l["label"])}</a>'
        for l in profile.get("links", [])
    )

    capture = ""
    ec = profile.get("email_capture", {})
    if ec.get("enabled"):
        capture = f"""
<section class="capture">
  <h2>{esc(ec.get("heading", "Newsletter"))}</h2>
  <form action="{esc(ec.get("form_action", ""))}" method="POST">
    <input type="email" name="email" required placeholder="{esc(ec.get("placeholder", "email"))}" autocomplete="email">
    <button type="submit">{esc(ec.get("button", "Eintragen"))}</button>
  </form>
</section>"""

    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(profile["name"])}</title>
<meta name="description" content="{esc(profile.get("tagline", ""))}">
<style>
:root {{
  --accent: {accent};
  --bg: #f4f4f8;
  --card: #ffffff;
  --text: #1d1d2b;
  --muted: #6b6b7b;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --accent: {accent_dark};
    --bg: #14141c;
    --card: #1f1f2b;
    --text: #ececf4;
    --muted: #9a9aac;
  }}
}}
* {{ box-sizing: border-box; margin: 0; }}
body {{
  font-family: system-ui, -apple-system, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  display: flex;
  justify-content: center;
  padding: 3rem 1rem;
}}
main {{ width: 100%; max-width: 420px; text-align: center; }}
.avatar {{
  width: 96px; height: 96px; border-radius: 50%;
  object-fit: cover; margin: 0 auto 1rem;
  display: flex; align-items: center; justify-content: center;
}}
.avatar-initials {{
  background: var(--accent); color: #fff;
  font-size: 2rem; font-weight: 700;
}}
h1 {{ font-size: 1.4rem; }}
.tagline {{ color: var(--muted); margin: .4rem 0 1.6rem; }}
.link {{
  display: block; background: var(--card); color: var(--text);
  text-decoration: none; font-weight: 600;
  padding: .9rem 1rem; border-radius: 14px; margin-bottom: .7rem;
  border: 1px solid transparent;
  box-shadow: 0 1px 3px rgba(0,0,0,.08);
  transition: transform .12s ease, border-color .12s ease;
}}
.link:hover {{ transform: translateY(-2px); border-color: var(--accent); }}
.capture {{
  background: var(--card); border-radius: 14px;
  padding: 1.2rem 1rem; margin-top: 1.6rem;
  box-shadow: 0 1px 3px rgba(0,0,0,.08);
}}
.capture h2 {{ font-size: 1rem; margin-bottom: .8rem; }}
.capture form {{ display: flex; gap: .5rem; }}
.capture input {{
  flex: 1; padding: .7rem .9rem; border-radius: 10px;
  border: 1px solid var(--muted); background: var(--bg); color: var(--text);
  font-size: .95rem; min-width: 0;
}}
.capture button {{
  padding: .7rem 1.1rem; border: none; border-radius: 10px;
  background: var(--accent); color: #fff; font-weight: 700; cursor: pointer;
}}
footer {{ margin-top: 2rem; color: var(--muted); font-size: .8rem; }}
</style>
</head>
<body>
<main>
  {avatar}
  <h1>{esc(profile["name"])}</h1>
  <p class="tagline">{esc(profile.get("tagline", ""))}</p>
  <nav>
{links}
  </nav>
  {capture}
  <footer>{esc(profile.get("footer", ""))}</footer>
</main>
{profile.get("analytics_snippet", "")}
</body>
</html>
"""


def main() -> int:
    profile = json.loads((BASE / "profile.json").read_text())
    dist = BASE / "dist"
    dist.mkdir(exist_ok=True)
    (dist / "index.html").write_text(render(profile))
    print(f"OK: {dist / 'index.html'} geschrieben.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
