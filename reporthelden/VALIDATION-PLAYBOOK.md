# ReportHelden · Validierungs-Playbook

Ziel: **≥ 10 zahlende Beta-Nutzer (19 €) aus ≤ 100 Ansprachen**, bevor weiter gebaut wird. Dieses Playbook enthält alles, was für die Durchführung nötig ist.

## Vorbereitung (einmalig, ~1 Stunde)

1. **Inhalte nach WordPress bringen:** Die Site läuft auf WordPress unter reporthelden.de.
   `python3 publish_wp.py` überträgt Startseite, Beispiel-Report, Impressum, Datenschutz
   (als Seiten) und die beiden SEO-Artikel (als Beiträge) — Trockenlauf und Entwurfsstatus
   sind Voreinstellung. Vorher die Platzhalter in `landing/impressum.html` und
   `landing/datenschutz.html` füllen; das Skript verweigert sonst die Übertragung.
   **Ohne Impressum keine Ads schalten (Abmahnrisiko).** Danach in WordPress die Seite
   „start" als Startseite setzen (Einstellungen → Lesen).
2. **Zahlungslink statt Mail-CTA (empfohlen):** Stripe Payment Link oder LemonSqueezy-Produkt „ReportHelden Beta — 19 €" anlegen und als CTA-Ziel eintragen. Zahlung ist das einzige Validierungssignal, das zählt.
3. **Pre-Launch-Check laufen lassen:** `python3 preflight.py` prüft offene Platzhalter,
   den CTA, interne Links, Share-Bild, Domain-Konsistenz und die Aktualität von Demo-Report
   und Beta-Paket. Exit-Code 0 = startklar. **Nicht launchen, solange Blocker rot sind.**
4. **Eigenen Report erzeugen:** Einen echten (anonymisierten) Kunden-Export durch den Generator jagen. Der eigene „Wow, das ist mein Report"-Moment ist der beste Pitch — und deckt Parser-Lücken auf.

**Auslieferung nach Zahlung:** `python3 package.py` erzeugt `dist/reporthelden-beta.zip` —
per Mail verschicken oder als Download hinter den Zahlungslink legen. Die Anleitung im
Paket beantwortet Installation, Export und Branding, sodass kein Support-Ping nötig ist.

## Kanäle & Reihenfolge

| Welle | Kanal | Ansprachen | Erwartung |
|-------|-------|-----------:|-----------|
| 1 | Direktkontakte: bekannte PPC-Freelancer & Kleinst-Agenturen | 10–15 | ehrlichstes Feedback, 2–3 Käufe |
| 2 | LinkedIn: Kommentierende unter PPC-/SEA-Posts (DACH), 1st/2nd-Degree | 40–50 | Kernkanal |
| 3 | Communities: SEA-/PPC-Gruppen (Facebook/Slack/Discord), OMR-Community-Threads | 20–30 | Post + Demo-Link, kein Spam: erst Mehrwert, dann Link |
| 4 | Eigener Kanal: LinkedIn-Posts (`marketing/linkedin-posts.md`) | 3 Posts | Post 1 vor Welle 2 veröffentlichen |
| 5 | Paid (optional, Zweitkanal): Meta- & X-Ads (`marketing/ad-copy-meta-x.md`) | 10–15 €/Tag | validiert Messaging, nicht Nachfrage — Messplan beachten |

## Nachrichten-Vorlagen

**LinkedIn-DM (Welle 1–2):**

> Hi [Name], kurze Frage von PPC'ler zu PPC'ler: Wie lange sitzt du pro Kunde am Monatsreport?
> Ich baue gerade ein Tool, das aus dem normalen Google-Ads-CSV-Export in unter einer Minute
> einen fertigen deutschen Kundenreport macht — inklusive geschriebener Zusammenfassung und
> Empfehlungen, nicht nur Charts. Läuft lokal, Kundendaten bleiben auf deinem Rechner.
> Hier ist ein Beispiel-Report: [Link]. Wäre das was für deinen Workflow — und falls ja:
> Beta-Zugang kostet einmalig 19 €. Ehrliches „brauch ich nicht" hilft mir genauso.

**Community-Post (Welle 3):**

> Monatsreports: Ich habe aufgehört, Slides zu bauen. Stattdessen: Google-Ads-CSV exportieren,
> durch ein kleines lokales Tool jagen, fertiger Report mit Kommentar fällt raus (Beispiel im Link).
> Bin gerade in der Beta-Phase und suche 10 PPC-Freelancer, die es gegen kleines Geld (19 € einmalig)
> mittesten und die Roadmap mitbestimmen. Feedback — auch kritisches — sehr willkommen.

## Interview-Leitfaden (bei jedem Gespräch, 10 Min.)

1. Wie erstellst du heute Kundenreports, und wie lange dauert das pro Kunde?
2. Was kostet dich dein aktuelles Setup (Tool-Abos + Zeit)?
3. Was ist der nervigste Teil? (Hypothese: der Kommentar-Text — prüfen!)
4. Demo zeigen → Was fehlt dir, damit du *diesen* Report an deinen Kunden schicken würdest?
5. Abschluss: „Beta kostet 19 € einmalig — bist du dabei?" (Antwort notieren: gekauft / später / nein + Grund)

## Tracking

Die Vorlage liegt bereit: [`validierung.csv`](validierung.csv) (Datum · Name · Kanal ·
Antwort · Einwand · Feature-Wunsch · Notiz) — Beispielzeile überschreiben und nach jedem
Gespräch eine Zeile ergänzen. Nach jeder Welle auswerten: Welcher Einwand kommt ≥ 3-mal?
→ vor der nächsten Welle adressieren, und zwar in der Landingpage oder im Produkt, nicht
im nächsten Gespräch.

Vorbereitete Antworten auf die acht wahrscheinlichsten Einwände:
[`marketing/einwaende.md`](marketing/einwaende.md) — vor Welle 1 einmal durchlesen.

## Entscheidungsregeln

- **≥ 10 Käufe aus ≤ 100 Ansprachen** → Validiert. Weiterbauen in Roadmap-Reihenfolge der Beta-Wünsche (erwartet: White-Label, Meta Ads, KI-Feinschliff).
- **5–9 Käufe** → Signal da, Positionierung unscharf. Häufigsten Einwand beheben, Welle wiederholen.
- **< 5 Käufe** → Stopp. Einwände auswerten und zurück zur Rangliste in [MARKET-OPPORTUNITY.md](../MARKET-OPPORTUNITY.md) (Kandidat #2: vertikale Workflow-Tools) — nicht aus Trotz weiterbauen.

## Warum 19 € und nicht kostenlos

Die Micro-SaaS-Recherche ist eindeutig: Wartelisten und „würde ich nutzen"-Aussagen validieren nichts — nur Zahlungen zählen. 19 € ist niedrig genug für eine Spontanentscheidung und hoch genug, um Höflichkeitszusagen auszusortieren.
