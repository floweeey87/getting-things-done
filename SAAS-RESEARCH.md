# SaaS besser machen & ersetzen — Recherche und Priorisierung

Stand: 2026-08-09 · Ansatz: Etablierte SaaS-Produkte, deren Kern technisch klein ist, als bessere und günstigere Lösung nachbauen — beginnend mit dem einfachsten.

## Bewertungskriterien

- **Technischer Kern:** Wie klein ist das eigentliche Produkt, wenn man Marketing und Enterprise-Beiwerk abzieht?
- **Moat:** Hat der Anbieter etwas Unkopierbares (Netzwerkeffekt, Daten-Index, Zustell-Reputation, API-Privilegien)? Ohne Moat ist das Produkt angreifbar.
- **Schmerzpunkte der Nutzer:** Wo zahlen Kunden heute für Dinge, die sie ärgern (Preiserhöhungen, Branding-Zwang, Feature-Paywalls)?
- **Preisniveau:** Was kostet das Original — also wie groß ist der Hebel einer besseren/kostenlosen Alternative?

## Rangliste: einfachste zuerst

| # | SaaS | Preis 2026 | Kern-Technik | Moat | Größter Nutzer-Schmerz |
|---|------|-----------:|--------------|------|------------------------|
| 1 | **Linktree** (Link-in-Bio) | $8–35/Monat | Eine statische HTML-Seite | Keiner | E-Mail-Capture nur bezahlt, Linktree-Branding, fremde Domain |
| 2 | **Bitly** (URL-Shortener) | $10–249/Monat | Redirect-Tabelle + Klickzähler | Gering (bit.ly-Domain) | 10 Links/Monat im Free-Plan, Preise stark gestiegen |
| 3 | **QR-Code-SaaS** (QR-Verse u. a.) | $5–30/Monat | Client-seitige Codegenerierung | Keiner | Abo für etwas, das eine Bibliothek gratis kann; "dynamische" QR-Codes sind nur Redirects (→ #2) |
| 4 | **Typeform / Jotform** (Formulare) | $34–129/Monat | Formular-Renderer + Antwort-Speicher | Gering | Antwort-Limits als Paywall, hohe Einstiegspreise |
| 5 | **Calendly** (Terminbuchung) | $10–16/Sitz/Monat | Kalender-API + Slot-Logik | Mittel (Integrationen) | Per-Seat-Preise skalieren schmerzhaft; Kernfeatures hinter Teams/Enterprise |
| 6 | **Loom** (Screen-Recording) | $18–24/Sitz/Monat | Browser-Recording-APIs + Video-Hosting | Mittel (CDN/Transkription) | 5-Minuten-Cap im Free-Plan, Preise seit Atlassian-Kauf |
| 7 | **Buffer / Hootsuite** (Social-Scheduling) | $6–99/Monat | Plattform-APIs + Cron | Hoch (API-Zugänge, Review-Prozesse) | Preis pro Kanal; API-Hürden sind aber der Moat des Anbieters |
| 8 | **Mailchimp / Brevo** (E-Mail) | $20–350/Monat | SMTP + Listenverwaltung | **Hoch** (Zustell-Reputation) | Kontaktbasierte Preistreppen; Selbstbau riskiert Spam-Ordner — nicht sinnvoll ersetzbar |

**Merksatz aus der Recherche:** Ersetzbar ist alles, was nur Convenience um offene Standards verkauft (1–4). Schwer ersetzbar ist alles mit Netzwerkeffekt, privilegierten API-Zugängen oder Reputations-Moat (7–8).

## Warum Linktree zuerst

- Das Produkt ist im Kern **eine einzige statische Seite** — kein Backend, kein Login, keine Datenbank nötig.
- Linktree nimmt $8–35/Monat und hält ausgerechnet die wertvollste Funktion (E-Mail-Adressen einsammeln) im Free-Plan zurück — „ein Link-Profil ohne E-Mail-Capture ist ein löchriger Eimer".
- Eine selbst gehostete Seite ist in jedem Punkt besser: eigene Domain (SEO!), kein Fremd-Branding, unbegrenzte Links, E-Mail-Capture inklusive, volle Designkontrolle, keine laufenden Kosten (GitHub Pages/Cloudflare Pages hosten gratis).

→ **Gebaut:** [`biolink/`](biolink/README.md) — ein Generator, der aus einer `profile.json` eine fertige, selbst gehostete Link-in-Bio-Seite erzeugt.

## Roadmap danach

1. **#2 Bitly-Ersatz:** Redirects als statische Konfiguration (Cloudflare Pages `_redirects`-Datei) + Klickzählung via Edge-Function. Baut direkt auf #1 auf (gleiches Hosting), macht zusammen mit #3 „dynamische QR-Codes" trivial.
2. **#3 QR-Codes:** clientseitige Generierung in die Biolink-Seite integrieren — damit sind zwei SaaS-Kategorien in einem Produkt abgedeckt.
3. **#4 Formulare:** statischer Formular-Renderer aus JSON-Schema + Antworten in ein Google Sheet oder eine kleine Edge-Function. Ab hier wird erstmals ein (minimales) Backend nötig.
4. **#5 Calendly** danach neu bewerten — Cal.com als Open-Source-Basis prüfen statt komplett selbst zu bauen.

## Quellen

- [Linktree Pricing 2026 (SocialsLink)](https://socialslink.com/blog/linktree-pricing-2026)
- [Linktree-Alternativen 2026: E-Mail-Capture als größte Free-Plan-Lücke (Inflowave)](https://inflowave.io/resources/linktree-alternatives-2026)
- [Bitly Pricing 2026 (RedirHub)](https://www.redirhub.com/blog/bitly-pricing-2026)
- [Typeform Pricing 2026 (FormNX)](https://formnx.com/typeform-pricing)
- [Jotform Pricing 2026 (FormNX)](https://formnx.com/jotform-pricing)
- [Calendly-Alternativen 2026: Per-Seat-Preiskritik (WP Astra)](https://wpastra.com/resources/calendly-alternatives/)
- [Loom Pricing 2026 (Arcade)](https://www.arcade.software/post/loom-pricing)
- [Micro-SaaS-Ideen & Klonbarkeit 2026 (Flowjam)](https://www.flowjam.com/blog/indie-hackers-saas-ideas-2025-10-you-can-launch-fast)
