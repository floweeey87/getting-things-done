# Biolink — selbst gehosteter Linktree-Ersatz

Eine Link-in-Bio-Seite aus einer JSON-Datei. Alles, wofür Linktree $8–35/Monat nimmt — ohne Abo, ohne Fremd-Branding, auf eigener Domain.

| | Linktree Free | Linktree Pro ($15/M) | **Biolink** |
|---|---|---|---|
| Links | unbegrenzt | unbegrenzt | unbegrenzt |
| E-Mail-Capture | ❌ | ✅ | ✅ (beliebiger Form-Endpoint) |
| Eigenes Branding / kein Logo | ❌ | ✅ | ✅ |
| Eigene Domain | ❌ | ✅ | ✅ |
| Design frei anpassbar | eingeschränkt | eingeschränkt | ✅ (es ist dein HTML) |
| Kosten | 0 € | 180 $/Jahr | **0 €** |

## Benutzung

1. `profile.json` anpassen: Name, Tagline, Links, Farben, optional Avatar-URL.
2. Seite bauen:
   ```bash
   python3 biolink/build.py
   ```
3. `biolink/dist/index.html` deployen — GitHub Pages, Cloudflare Pages oder jeder Webspace. Eine Datei, keine Abhängigkeiten.

## E-Mail-Capture

In `profile.json` unter `email_capture.form_action` einen Form-Endpoint eintragen, z. B. [Formspree](https://formspree.io) (Free-Plan reicht für den Start) oder eine eigene Edge-Function. `enabled: false` blendet den Block aus.

## Analytics (optional)

`analytics_snippet` akzeptiert ein beliebiges Snippet (z. B. Plausible oder ein selbst gehosteter Zähler). Leer lassen = keine Tracker.

## Nächste Ausbaustufen (siehe SAAS-RESEARCH.md)

- Kurzlink-Redirects über eine `_redirects`-Datei (Bitly-Ersatz) auf demselben Hosting
- QR-Code clientseitig generieren (QR-SaaS-Ersatz)
