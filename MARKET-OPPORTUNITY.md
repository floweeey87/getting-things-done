# Markt-Priorisierung: Wo lohnt sich der Angriff wirklich?

Stand: 2026-08-09 · Fortsetzung von [SAAS-RESEARCH.md](SAAS-RESEARCH.md), jetzt nach **Marktlücke und Zahlungsbereitschaft** priorisiert statt nach Bauaufwand.

## Was die Marktrecherche ergab

1. **Die horizontalen DSGVO-Lücken sind zu.** Terminbuchung „DSGVO-konform, Server in Deutschland" ist bereits ein eigener Markt mit mehreren etablierten Anbietern (meetergo ab 7 €/Nutzer, Zeeg, TerminNow, Calenso — teils mit Gratis-Plänen). Bei Formularen dasselbe: Formbricks (Frankfurt, Open Source), LimeSurvey (deutsch, ISO 27001), Zenforms, dazu Tally kostenlos mit EU-Hosting. Ein weiterer Klon hätte hier kein Alleinstellungsmerkmal.
2. **Technisch triviale Produkte (Linktree, Bitly) sind Distributions-Geschäfte.** Hunderte Klone existieren; der Moat ist Marke/Reichweite, nicht Technik. Als *Business* unattraktiv — als kostenlose Lead-Magnete aber weiter nützlich (Biolink behalten wir dafür).
3. **Die echten Lücken liegen in Mikro-Segmenten.** Die Indie-Hacker-Datenlage 2025/26: erfolgreiche Solo-SaaS zielen zu 73 % auf Mikro-Segmente, die Großanbieter ignorieren; Nischen-Zielgruppen zahlen $29–199/Monat, wenn das Tool ihren konkreten Workflow versteht. Das entscheidende Kriterium ist nicht „kann ich es bauen", sondern „habe ich Zugang zur Zielgruppe".

## Neue Rangliste (beste Gelegenheit zuerst)

| # | Gelegenheit | Zahlungsbereitschaft (belegt) | Wettbewerbslücke | Founder-Market-Fit |
|---|-------------|-------------------------------|------------------|--------------------|
| 1 | **PPC-Kundenreporting für Freelancer & Kleinst-Agenturen (DACH)** | AgencyAnalytics $20/Kunde/Monat; Supermetrics $25–400/Monat; Funnel.io ab $300/Monat | Alle Anbieter: Per-Client-Abos, englisch, Cloud-Zwang; **keiner** automatisiert den eigentlichen Schmerz — den Kommentar-Text; keiner ist local-first/DSGVO-nativ | **Maximal** — eigene tägliche Arbeit, eigene Zielgruppe, Distribution über deutsche PPC-/SEO-Kanäle beherrscht |
| 2 | Vertikale Workflow-Tools (Handwerk, lokale Dienstleister) | $30–150/Monat belegt | Groß („Zettel & Excel") | Gering — kein Zugang, Nische erst zu erschließen |
| 3 | DSGVO-Formulare/-Terminbuchung | vorhanden | **Geschlossen** (meetergo, Zeeg, Formbricks, Tally u. a.) | mittel |
| 4 | Linktree/Bitly-Klone | gering (Race to zero) | keine | hoch, aber irrelevant — Distributions-Business |

## Entscheidung: #1 — „AdReport" (Arbeitstitel)

**Der Schmerz:** Jeder PPC-Freelancer verliert pro Kunde und Monat 1–3 Stunden für den Monatsreport — Daten exportieren, in Slides/Sheets hübsch machen, und vor allem: den „Was ist passiert und warum"-Text schreiben. Die etablierten Tools (DashThis, Whatagraph, AgencyAnalytics, Reporting Ninja) automatisieren nur die Charts, nicht den Kommentar — und kosten dafür laufend pro Kunde.

**Der Wedge — drei Differenzierer, die kein Incumbent hat:**
1. **CSV-first & local-first:** Läuft lokal, kein Login, keine API-Anbindung nötig (die Google-Ads-API mit Developer-Token ist genau die Hürde, die Incumbents als Moat nutzen — wir umgehen sie: jeder kann CSV exportieren). Kundendaten verlassen nie den Rechner → die stärkste DSGVO-Story, die es gibt.
2. **AI-nativ:** Der Kommentar (Zusammenfassung, Auffälligkeiten, Empfehlungen) wird generiert, nicht nur die Charts. Erst regelbasiert (deterministisch, offline), optional per Claude-API verfeinert.
3. **Deutsch & fair bepreist:** Deutsche Reports für deutsche Kunden; Preismodell einmalig/flat statt Per-Client-Abo — direkt gegen das Preismodell der Incumbents positioniert.

**Distribution (der eigentliche Moat-Aufbau):** Deutschsprachiger SEO-Content („Google Ads Report Vorlage", „AgencyAnalytics Alternative deutsch"), PPC-Communities, LinkedIn, plus kleine eigene Ads-Budgets — exakt Florians Kernkompetenz.

## Validierungsplan (vor weiterem Ausbau)

1. **MVP zeigen, nicht beschreiben:** Der Generator in [`adreport/`](adreport/README.md) erzeugt aus einem echten CSV-Export in Sekunden einen fertigen Report — das Demo-Artefakt ist das Verkaufsargument.
2. **20 Gespräche** mit PPC-Freelancern/Kleinst-Agenturen (LinkedIn, Communities): Wie machst du Reports heute? Was kostet dich das? Würdest du für „CSV rein, fertiger Report mit Kommentar raus" zahlen?
3. **Zahlungssignal statt Meinungen:** Beta-Zugang gegen kleinen Betrag (9–19 €) statt kostenloser Warteliste — die Recherche ist eindeutig: Nur „already paying" zählt als Validierung.
4. **Schwelle:** ≥ 10 zahlende Beta-Nutzer aus ≤ 100 Ansprachen → weiterbauen (Meta-Ads-Import, PDF-Export, White-Label). Darunter → Positionierung prüfen, bevor mehr gebaut wird.

## Quellen

- [DSGVO-Calendly-Alternativen 2026 (Zeeg)](https://zeeg.me/de/blog/content/calendly-alternative-dsgvo) · [meetergo Pricing](https://meetergo.com/en/pricing) · [TerminNow](https://termin-now.de/calendly-alternative)
- [Google-Forms-/Typeform-Alternativen mit DSGVO-Hosting (BornCity)](https://borncity.com/news/google-forms-alternative-deutsche-anbieter-mit-dsgvo-hosting/) · [Typeform-Alternativen im Vergleich (remote-job.net)](https://remote-job.net/typeform-alternative/)
- [AgencyAnalytics-Alternativen & Pricing 2026 (Databox)](https://databox.com/9-best-agencyanalytics-alternatives-in-2026-ranked-for-agencies) · [Supermetrics-Alternativen 2026 (Reporting Ninja)](https://www.reportingninja.com/blog/supermetrics-alternatives) · [Two Minute Reports](https://twominutereports.com/supermetrics-alternatives)
- [Profitable Micro-SaaS-Nischen 2026 (Superframeworks)](https://superframeworks.com/articles/profitable-micro-saas-niches) · [Bootstrapped-SaaS-Nischen für Solo-Founder (EntrepreneurLoop)](https://entrepreneurloop.com/bootstrapped-saas-niches-solo-founders/)
