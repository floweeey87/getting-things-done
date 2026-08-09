# Vorlage: Bewertungsartikel nach Quartalszahlen

Jeder neu geschriebene Bewertungsartikel folgt exakt diesem Aufbau. Ausgabe ist
reines HTML (WordPress-Content ohne `<html>`/`<body>`-Gerüst), analog zu den
PSH-Artikeln. Tabellen in `<div class="ksk-table-wrap"><table>…</table></div>`
einschließen, Kernfakten-Kästen in `<div class="ksk-keyfacts">…</div>`.

## Pflichtaufbau

1. **Kurzantwort** (`<p><strong>Die kurze Antwort:</strong> …</p>`)
   – 3–5 Sätze: Wie sind die neuen Quartalszahlen einzuordnen, was heißt das
   für die Bewertung nach dem Kurssturz?

2. **Kernfakten-Kasten** (`ksk-keyfacts`)
   – Quartal, Umsatz, Ergebnis (EBIT/EPS), Guidance-Status, Kursreaktion,
   je Zeile ein `<li>` mit Wert und Vergleich zum Vorjahr.

3. **Transparenz-Absatz**
   – Womit wurde gearbeitet (IR-Pressemitteilung, Quartalsbericht), was ist
   eigene Einordnung, was sind Unternehmensangaben.

4. **`<h2>Die Quartalszahlen im Detail</h2>`**
   – Tabelle: Kennzahl | Q aktuell | Vorjahresquartal | Veränderung.
   – Danach Einordnung in Fließtext: Treiber, Sondereffekte, Segmentdetails.

5. **`<h2>Guidance und Ausblick</h2>`**
   – Was sagt das Management, wurde die Prognose bestätigt/angehoben/gesenkt,
   welche Annahmen stecken dahinter.

6. **`<h2>Bewertung nach den Zahlen</h2>`**
   – Aktuelle Kennzahlen (KGV, ggf. KUV/EV-EBITDA) mit Rechenbasis und Datum.
   – Einordnung: Ist der Kurssturz durch die Zahlen gerechtfertigt, überzogen
   oder noch nicht ausgestanden? Beide Lesarten fair darstellen.

7. **`<h2>Chancen und Risiken</h2>`**
   – Je 3–5 Punkte als Liste, konkret und auf die neuen Zahlen bezogen.

8. **`<h2>Fazit</h2>`**
   – Nüchterne Zusammenfassung. Keine Kauf-/Verkaufsaufforderung, keine
   Kurszielversprechen. Formulierungen wie „spricht dafür/dagegen“ statt
   Empfehlungen.

9. **`<h2>Primärquellen und Datenstand</h2>`**
   – Liste der Quellen als Links (IR-Pressemitteilung zuerst).
   – `<p><em>Datenstand: <Datum>. Kennzahlen können sich durch Restatements
   oder Folgeberichte ändern.</em></p>`

10. **Risikohinweis (Pflicht, letzter Block)**
    ```html
    <p><strong>Risikohinweis:</strong> Dieser Artikel ist eine journalistische
    Einordnung und keine Anlageberatung. Aktieninvestments sind mit Risiken
    bis hin zum Totalverlust verbunden. Kennzahlen und Kurse können sich
    jederzeit ändern; bitte prüfe alle Angaben selbst, bevor du eine
    Anlageentscheidung triffst.</p>
    ```

## Titel und Excerpt

- Titel-Muster: `<Name>-Aktie nach Q<x>-Zahlen <Jahr>: <prägnante Einordnung>`
- Excerpt: max. ~160 Zeichen, enthält Unternehmensname, Quartal und Kernaussage.
