#!/usr/bin/env python3
"""Überträgt den gequeueten Artikel aus content-sync/manifest.json nach WordPress.

Sicherheitsprinzipien dieses Skripts:

* **Trockenlauf ist die Voreinstellung.** Ohne ``--apply`` wird nichts geschrieben.
* **Zugangsdaten nur aus der Umgebung** (``WP_USER``, ``WP_APP_PASSWORD``) —
  niemals in dieser Datei oder im Repository.
* **Aktualisieren statt anlegen.** Der Beitrag wird über den Slug gesucht und
  aktualisiert; existiert er nicht, bricht das Skript ab (kein Duplikat).
* **Prüfsumme entscheidet.** ``content_sha256`` im Manifest gehört zu den
  auditierten Quelldateien unter ``content-sync/article-<version>/``. Diese
  Quelle wird standardmäßig veröffentlicht. Weicht der ``content_base64``-
  Payload davon ab, wird die Abweichung angezeigt statt stillschweigend
  übernommen.

Nutzung:

    export WP_USER='Achim'
    export WP_APP_PASSWORD='xxxx xxxx xxxx xxxx xxxx xxxx'

    python3 sync_wordpress.py                 # Trockenlauf: zeigt, was passieren würde
    python3 sync_wordpress.py --apply         # überträgt die auditierte Quelle
    python3 sync_wordpress.py --diff          # Quelle vs. Manifest-Payload vergleichen
"""

import argparse
import base64
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
SYNC_DIR = BASE / "content-sync"
DEFAULT_SITE = "https://powerstation-helden.de"


def fail(msg: str) -> "typing.NoReturn":  # noqa: F821
    print(f"Fehler: {msg}", file=sys.stderr)
    sys.exit(1)


# ------------------------------------------------------------------ Manifest

def load_manifest() -> tuple[dict, dict]:
    path = SYNC_DIR / "manifest.json"
    if not path.exists():
        fail(f"{path} nicht gefunden.")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    updates = manifest.get("updates") or []
    if len(updates) != 1:
        fail(f"Manifest enthält {len(updates)} Einträge — erwartet wird genau einer.")
    return manifest, updates[0]


def source_for(update: dict, version: int) -> tuple[str, Path]:
    """Findet das Quellverzeichnis, dessen Inhalt zu content_sha256 passt.

    Konvention: Manifest-Version N entspricht article-<N:03d>. Die Zuordnung
    wird über die Prüfsumme bestätigt; schlägt das fehl, werden alle
    Artikelverzeichnisse durchprobiert.
    """
    want = update.get("content_sha256")
    candidates = [SYNC_DIR / f"article-{version:03d}"]
    candidates += sorted(d for d in SYNC_DIR.glob("article-*") if d.is_dir())
    seen = set()
    for d in candidates:
        if d in seen or not d.is_dir():
            continue
        seen.add(d)
        content = b"".join(p.read_bytes() for p in sorted(d.glob("*.html")))
        if hashlib.sha256(content).hexdigest() == want:
            return content.decode("utf-8"), d
    fail("keine Quelldateien gefunden, deren Prüfsumme zu content_sha256 passt — "
         "Manifest und Artikelquellen passen nicht zusammen.")


def payload_from_manifest(update: dict) -> str:
    return base64.b64decode(update["content_base64"]).decode("utf-8")


# ----------------------------------------------------------------- WordPress

class WordPress:
    def __init__(self, site: str, user: str, app_password: str) -> None:
        self.api = site.rstrip("/") + "/wp-json/wp/v2"
        token = base64.b64encode(
            f"{user}:{app_password.replace(' ', '')}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "User-Agent": "psh-content-sync/1.0",
        }

    def _request(self, method: str, path: str, body: dict | None = None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.api + path, data=data,
                                     headers=self.headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:400]
            if e.code in (401, 403):
                fail(f"Anmeldung abgelehnt ({e.code}). Anwendungspasswort und "
                     f"Benutzername prüfen; REST-API darf nicht durch ein "
                     f"Sicherheits-Plugin blockiert sein.\n{detail}")
            fail(f"{method} {path} → HTTP {e.code}\n{detail}")
        except urllib.error.URLError as e:
            fail(f"Site nicht erreichbar: {e.reason}")

    def whoami(self) -> dict:
        return self._request("GET", "/users/me?context=edit")

    def find_post(self, slug: str) -> dict | None:
        q = urllib.parse.urlencode({"slug": slug, "status": "any", "context": "edit"})
        hits = self._request("GET", f"/posts?{q}")
        return hits[0] if hits else None

    def update_post(self, post_id: int, fields: dict) -> dict:
        return self._request("POST", f"/posts/{post_id}", fields)


# ---------------------------------------------------------------------- Main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--site", default=os.environ.get("WP_SITE", DEFAULT_SITE),
                    help=f"WordPress-Basis-URL (Standard: {DEFAULT_SITE})")
    ap.add_argument("--apply", action="store_true",
                    help="Änderung wirklich übertragen (ohne dies nur Trockenlauf)")
    ap.add_argument("--source", choices=("files", "manifest"), default="files",
                    help="Was veröffentlicht wird: die auditierten Quelldateien "
                         "(Standard, durch Prüfsumme gedeckt) oder der "
                         "content_base64-Payload des Manifests")
    ap.add_argument("--diff", action="store_true",
                    help="Unterschiede zwischen Quelle und Manifest-Payload zeigen")
    args = ap.parse_args()

    manifest, update = load_manifest()
    version = manifest.get("version", 0)
    slug, title = update["slug"], update["title"]
    excerpt = update.get("excerpt", "")
    source_html, source_dir = source_for(update, version)
    manifest_html = payload_from_manifest(update)

    print(f"\nManifest v{version} · {slug}")
    print(f"  Titel   : {title}")
    print(f"  Quelle  : {source_dir.name} ({len(source_html)} Zeichen, Prüfsumme OK)")

    if source_html != manifest_html:
        print(f"  {'!':>8} Manifest-Payload weicht von der auditierten Quelle ab "
              f"({len(manifest_html)} Zeichen) — nur die Quelle ist durch "
              f"content_sha256 gedeckt.")
        if args.diff:
            import difflib
            print()
            for line in difflib.unified_diff(
                    source_html.splitlines(), manifest_html.splitlines(),
                    "auditierte Quelle", "manifest content_base64", lineterm="", n=0):
                if not line.startswith(("---", "+++", "@@")):
                    line = line[0] + " " + line[1:]
                print("   " + line[:200])
            print()

    content = source_html if args.source == "files" else manifest_html
    print(f"  Sende   : {args.source}")

    user = os.environ.get("WP_USER")
    password = os.environ.get("WP_APP_PASSWORD")
    if not user or not password:
        fail("WP_USER und WP_APP_PASSWORD müssen als Umgebungsvariablen gesetzt sein.")

    wp = WordPress(args.site, user, password)
    me = wp.whoami()
    print(f"\nAngemeldet als {me.get('name')} (ID {me.get('id')}) auf {args.site}")

    post = wp.find_post(slug)
    if not post:
        fail(f"kein Beitrag mit Slug '{slug}' gefunden. Dieses Skript aktualisiert "
             f"nur bestehende Beiträge und legt bewusst keine neuen an.")

    old = post.get("content", {}).get("raw", "")
    print(f"Beitrag {post['id']} gefunden · Status {post.get('status')} · "
          f"{post.get('link', '')}")
    print(f"  Inhalt bisher: {len(old)} Zeichen → neu: {len(content)} Zeichen "
          f"({'unverändert' if old.strip() == content.strip() else 'geändert'})")

    if not args.apply:
        print("\nTrockenlauf — nichts übertragen. Mit --apply wirklich schreiben.\n")
        return 0

    result = wp.update_post(post["id"], {
        "title": title, "content": content, "excerpt": excerpt,
    })
    print(f"\nAktualisiert: {result.get('link')}")
    print(f"  Status: {result.get('status')} · geändert am {result.get('modified')}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
