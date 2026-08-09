# SaaS ersetzen: Recherche & Priorisierung

Stand: 2026-08-09 · Kontext: Solo-Betrieb (PPC-Marketing + Affiliate-Content-Projekt powerstation-helden.de). Ziel: SaaS-Abos Stück für Stück durch eigene, schlanke (AI-gestützte) Lösungen ersetzen — beginnend mit der einfachsten.

## Bewertungslogik

Jeder Kandidat wird nach drei Fragen bewertet:

1. **Ersetzbarkeit** — Lebt das SaaS von einem Daten-Moat (z. B. eigener Backlink-Index) oder nur von Convenience um frei verfügbare APIs/Standards herum? Convenience ist ersetzbar, Daten-Moats praktisch nicht.
2. **Aufwand** — Wie viele Stunden bis zu einer Lösung, die für *unseren* Anwendungsfall (nicht für den Massenmarkt) besser ist?
3. **Ersparnis/Nutzen** — Was kostet das SaaS pro Jahr, und was gewinnen wir an Kontrolle (eigene Daten, keine Limits, AI-Integration)?

## Rangliste (einfachste zuerst)

| # | SaaS-Kategorie | Typische Anbieter | Kosten/Jahr | Aufwand | Ersetzbarkeit | Status |
|---|----------------|-------------------|------------:|---------|---------------|--------|
| 1 | **Uptime-Monitoring + Status­seite** | UptimeRobot (Solo $7/M, Team $29/M), Better Stack | ~84–350 € | ⭐ Sehr gering (Stunden) | Voll — nur HTTP-Checks + Cron + Benachrichtigung | ✅ **Gebaut** → `01-uptime-monitor/` |
| 2 | **Rank-/Sichtbarkeits-Tracking** | Wincher ($29/M), SE Ranking, Sistrix-Ranktracker | ~350–1.200 € | ⭐⭐ Gering (GSC-API-Anbindung) | Hoch — Google Search Console liefert echte Positionen/Klicks gratis per API; SaaS verkauft nur die Hülle | 🔜 Nächster Schritt |
| 3 | **Content-Audit / On-Page-Checks** | Seobility, Screaming Frog (Lizenz), Semrush Site Audit | ~200–500 € | ⭐⭐ Gering–mittel | Hoch — eigener Crawler + Claude für inhaltliche Prüfung; passt direkt auf unseren bestehenden `content-sync`-Audit-Workflow | Geplant |
| 4 | **Broken-Link- & Affiliate-Link-Checker** | Dr. Link Check, LinkChecker-SaaS | ~100–300 € | ⭐⭐ Gering | Voll — kritisch fürs Affiliate-Geschäft (tote Amazon-/Partnerlinks = verlorene Provision) | Geplant |
| 5 | **Reporting-Dashboards (PPC + SEO)** | Supermetrics, AgencyAnalytics, Looker-Aufsätze | ~600–1.500 € | ⭐⭐⭐ Mittel | Hoch — Google Ads/GSC/GA4-APIs + statisches HTML-Dashboard; Anbieter verkaufen API-Klebstoff | Geplant |
| 6 | **Social-Media-Scheduling** | Buffer, Hootsuite | ~120–1.200 € | ⭐⭐⭐ Mittel | Mittel — APIs der Plattformen teils restriktiv (X, Instagram), Review-Prozesse nötig | Später |
| 7 | **E-Mail-Marketing/Newsletter** | Mailchimp, Brevo | ~200–800 € | ⭐⭐⭐⭐ Hoch | Mittel — Versand-Reputation/Deliverability ist der versteckte Moat; Selbstbau riskiert Spam-Ordner | Später, ggf. nur Teilersatz |
| 8 | **Keyword-Recherche & Backlink-Analyse** | Ahrefs (ab $139/M), Semrush, Sistrix | ~1.700–3.000 € | ⭐⭐⭐⭐⭐ Sehr hoch | **Gering** — eigener Crawl-Index ist der Moat; nicht sinnvoll replizierbar. Stattdessen: Nutzung reduzieren (GSC + Autocomplete + Claude), Abo nur bei Bedarf monatsweise | Nicht ersetzen, nur minimieren |

## Warum Uptime-Monitoring zuerst

- UptimeRobot hat 2025 den Free-Plan auf privat/nicht-kommerziell eingeschränkt und die Preise deutlich erhöht — für kommerzielle Projekte wie unseres fallen also real Kosten an.
- Die Kernfunktion ist trivial: URL per HTTP prüfen, Antwortzeit messen, bei Ausfall alarmieren, Verlauf anzeigen. Kein Daten-Moat, keine fremde API nötig.
- GitHub Actions liefert den Cron-Scheduler gratis mit (Muster wie bei Upptime bewährt); GitHub Issues sind der Alarmkanal (→ Mail/Push über die normale GitHub-Benachrichtigung), GitHub Pages oder das JSON selbst die Statusseite.
- Ergebnis: 0 € laufende Kosten, unbegrenzte Monitore, Verlauf liegt versioniert im eigenen Repo.

Umsetzung siehe [`01-uptime-monitor/`](01-uptime-monitor/README.md).

## Nächster Schritt (Rang 2): Rank-Tracker auf GSC-Basis

Google Search Console liefert per API kostenlos echte durchschnittliche Positionen, Klicks und Impressionen pro Keyword und Seite — genau die Daten, für die Wincher/SE Ranking/Sistrix Geld nehmen (deren Zusatzwert sind nur Wettbewerber-Rankings). Plan: täglicher GSC-Export per Actions-Cron, Verlauf als CSV/JSON im Repo, Alarm bei Positionsverlust > X, Claude-generierte Wochenzusammenfassung. Benötigt einmalig ein Google-Cloud-Service-Konto mit GSC-Zugriff (Secret im Repo) — deshalb Rang 2 statt 1.

## Quellen

- [UptimeRobot Pricing 2026 & Alternativen (GoPinger)](https://gopinger.com/blog/uptimerobot-pricing-alternatives/)
- [UptimeRobot vs. GitHub Actions (ObserveOne)](https://www.observeone.com/compare/uptime-robot-vs-github-actions)
- [Open-Source-Monitoring-Vergleich (Better Stack)](https://betterstack.com/community/comparisons/open-source-website-monitoring/)
- [Best Rank Tracker Tools 2026 (Konabayev)](https://konabayev.com/blog/best-rank-tracker/)
- [Semrush-Alternativen 2026 (SE Ranking)](https://seranking.com/blog/semrush-alternatives/)
- [Sistrix-Alternativen: Kosten & Tools 2026](https://www.alexanderpeterhihler.com/artikel/sistrix-alternativen-kostenlos-kostenpflichtig/)
