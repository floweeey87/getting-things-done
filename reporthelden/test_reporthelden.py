#!/usr/bin/env python3
"""Test-Suite für ReportHelden: Parser (beide Quellen), Zahlenformate,
Kommentar-Regeln, Rendering und den Multipart-Parser der App.

    python3 -m unittest test_reporthelden -v
"""

import ast
import tempfile
import unittest
from pathlib import Path

from app import parse_multipart
from build_report import (DEFAULT_BRAND, build_commentary, de, detect_decimal,
                          eur, parse_export, parse_number, pct_delta, render)

SAMPLES = Path(__file__).parent / "sample-data"


def write_csv(content: str) -> Path:
    f = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return Path(f.name)


class TestZahlen(unittest.TestCase):
    def test_deutsche_formate(self):
        self.assertEqual(parse_number("1.234,56"), 1234.56)
        self.assertEqual(parse_number("12,3 %"), 12.3)
        self.assertEqual(parse_number("24.657,70"), 24657.7)

    def test_englische_und_leere_formate(self):
        self.assertEqual(parse_number("1234.56"), 1234.56)
        self.assertEqual(parse_number(""), 0.0)
        self.assertEqual(parse_number("--"), 0.0)

    def test_englisches_tausendertrennzeichen(self):
        """1,234.56 darf nie als 1,23456 gelesen werden."""
        self.assertEqual(parse_number("1,234.56"), 1234.56)
        self.assertEqual(parse_number("24,657.70"), 24657.7)
        self.assertEqual(parse_number("1,234,567.89"), 1234567.89)

    def test_reine_tausendertrennung_ohne_nachkommastellen(self):
        """'1.234' und '1,234' sind Tausender, keine Drei-Nachkomma-Zahl."""
        self.assertEqual(parse_number("1.234"), 1234.0)
        self.assertEqual(parse_number("1,234"), 1234.0)
        self.assertEqual(parse_number("1.234.567"), 1234567.0)

    def test_dezimaltrennzeichen_der_datei_entscheidet(self):
        """Der Dateikontext löst die Mehrdeutigkeit von '1,234' auf."""
        self.assertEqual(detect_decimal(["24.657,70", "0,57", "1,234"]), ",")
        self.assertEqual(detect_decimal(["24,657.70", "0.57", "1,234"]), ".")
        self.assertIsNone(detect_decimal(["1,234", "5.678"]))
        self.assertEqual(parse_number("1,234", ","), 1.234)
        self.assertEqual(parse_number("1,234", "."), 1234.0)

    def test_symbole_und_vorzeichen(self):
        self.assertEqual(parse_number("€ 24.657,70"), 24657.7)
        self.assertEqual(parse_number("$1,234.56"), 1234.56)
        self.assertEqual(parse_number("CHF 1'234.50"), 1234.5)
        self.assertEqual(parse_number("1 234,56"), 1234.56)
        self.assertEqual(parse_number("-12,50"), -12.5)

    def test_ausgabeformat(self):
        self.assertEqual(de(24657.7, 2), "24.657,70")
        self.assertEqual(eur(1000), "1.000,00 €")

    def test_delta(self):
        self.assertAlmostEqual(pct_delta(110, 100), 10.0)
        self.assertIsNone(pct_delta(5, 0))


class TestGoogleParser(unittest.TestCase):
    def setUp(self):
        self.data = parse_export(SAMPLES / "kampagnen-juli-2026.csv")

    def test_quelle_und_kampagnen(self):
        self.assertEqual(self.data["source"], "Google Ads")
        self.assertEqual(len(self.data["campaigns"]), 6)

    def test_gesamtzeile_ausgefiltert_und_summe(self):
        self.assertNotIn("Gesamt", [c["name"] for c in self.data["campaigns"]])
        self.assertAlmostEqual(self.data["total"]["kosten"], 24657.7, places=1)

    def test_abgeleitete_kennzahlen(self):
        brand = next(c for c in self.data["campaigns"] if c["name"] == "Brand Search")
        self.assertAlmostEqual(brand["roas"], 38760 / 1245.8, places=2)
        self.assertAlmostEqual(brand["cpc"], 1245.8 / 6120, places=4)

    def test_semikolon_und_vorspann(self):
        p = write_csv("Irgendein Vorspann\nZeile 2\n"
                      "Kampagne;Impressionen;Klicks;Kosten;Conversions\n"
                      "Test A;1000;100;50,00;5\n")
        d = parse_export(p)
        self.assertEqual(d["campaigns"][0]["kosten"], 50.0)

    def test_kosten_conv_spalte_nicht_verwechselt(self):
        p = write_csv("Kampagne,Kosten/Conv.,Impressionen,Klicks,Kosten,Conversions\n"
                      "Test A,\"10,00\",1000,100,\"50,00\",5\n")
        self.assertEqual(parse_export(p)["campaigns"][0]["kosten"], 50.0)


class TestMetaParser(unittest.TestCase):
    def setUp(self):
        self.data = parse_export(SAMPLES / "meta" / "meta-juli-2026.csv")

    def test_quelle_erkannt(self):
        self.assertEqual(self.data["source"], "Meta Ads")

    def test_spalten_mapping(self):
        self.assertEqual(len(self.data["campaigns"]), 4)
        self.assertAlmostEqual(self.data["total"]["kosten"], 8252.5, places=1)
        retarget = next(c for c in self.data["campaigns"]
                        if c["name"].startswith("Retargeting"))
        self.assertEqual(retarget["klicks"], 3410)          # Link-Klicks
        self.assertEqual(retarget["conversions"], 114)      # Ergebnisse
        self.assertAlmostEqual(retarget["roas"], 11240 / 1120.3, places=2)

    def test_summenzeile_ausgefiltert(self):
        self.assertFalse(any(c["name"].startswith("Ergebnisse aus")
                             for c in self.data["campaigns"]))

    def test_unbekannter_header_bricht_ab(self):
        p = write_csv("Foo,Bar\n1,2\n")
        with self.assertRaises(SystemExit):
            parse_export(p)


class TestEchteExportformate(unittest.TestCase):
    """Fälle, die in echten Google-Ads-Exporten vorkommen."""

    def test_segmentierter_export_wird_zusammengefasst(self):
        p = write_csv(
            "Kampagne,Tag,Impressionen,Klicks,Kosten,Conversions,Conv.-Wert\n"
            'Brand,2026-07-01,1600,200,"40,00",14,"1.300,00"\n'
            'Brand,2026-07-02,1500,190,"38,00",13,"1.200,00"\n'
            'Shopping,2026-07-01,8000,300,"180,00",9,"1.000,00"\n')
        d = parse_export(p)
        self.assertEqual([c["name"] for c in d["campaigns"]], ["Brand", "Shopping"])
        brand = d["campaigns"][0]
        self.assertAlmostEqual(brand["kosten"], 78.0, places=2)
        self.assertEqual(brand["conversions"], 27)
        # Verhältniszahlen aus den Summen, nicht gemittelt
        self.assertAlmostEqual(brand["roas"], 2500 / 78, places=4)
        self.assertAlmostEqual(brand["cpc"], 78 / 390, places=4)

    def test_segmentspalte_wird_gemeldet(self):
        p = write_csv("Kampagne,Gerät,Impressionen,Klicks,Kosten,Conversions\n"
                      'A,Computer,10,1,"1,00",0\n')
        self.assertIn("Gerät", parse_export(p)["segments"])

    def test_summenzeilen_varianten_gefiltert(self):
        p = write_csv("Kampagne,Impressionen,Klicks,Kosten,Conversions\n"
                      'Brand,10,1,"1,00",0\n'
                      'Gesamt: Konto,10,1,"1,00",0\n'
                      'Summe,10,1,"1,00",0\n')
        self.assertEqual([c["name"] for c in parse_export(p)["campaigns"]], ["Brand"])

    def test_kampagne_die_mit_gesamt_beginnt_bleibt(self):
        p = write_csv("Kampagne,Impressionen,Klicks,Kosten,Conversions\n"
                      'Gesamtpaket Brand,10,1,"1,00",0\n')
        self.assertEqual(parse_export(p)["campaigns"][0]["name"], "Gesamtpaket Brand")

    def test_waehrung_im_spaltennamen(self):
        p = write_csv("Kampagne,Impressionen,Klicks,Kosten (EUR),Conversions\n"
                      'A,100,10,"25,50",2\n')
        self.assertAlmostEqual(parse_export(p)["campaigns"][0]["kosten"], 25.5, places=2)


class TestEnglischeOberflaeche(unittest.TestCase):
    """Viele PPC-Leute im DACH-Raum betreiben Google Ads und Meta auf Englisch."""

    GOOGLE_EN = ("Campaign report\nAug 1, 2026 - Aug 31, 2026\n"
                 "Campaign,Impressions,Clicks,Cost,Conversions,Conv. value,Cost / conv.\n"
                 'Brand - Search,"124,300","4,210","1,234.56",48.00,"9,870.00",25.72\n'
                 'Generic - Search,"88,120","2,105","2,980.10",31.00,"5,120.50",96.13\n'
                 'Total: account,"212,420","6,315","4,214.66",79.00,"14,990.50",53.35\n')

    def test_englischer_google_export_wird_erkannt(self):
        d = parse_export(write_csv(self.GOOGLE_EN))
        self.assertEqual(d["source"], "Google Ads")
        self.assertEqual([c["name"] for c in d["campaigns"]],
                         ["Brand - Search", "Generic - Search"])

    def test_englische_zahlen_korrekt_gelesen(self):
        d = parse_export(write_csv(self.GOOGLE_EN))
        brand = d["campaigns"][0]
        self.assertAlmostEqual(brand["kosten"], 1234.56, places=2)
        self.assertEqual(brand["impressionen"], 124300)
        self.assertEqual(brand["klicks"], 4210)
        self.assertAlmostEqual(brand["conv_wert"], 9870.0, places=2)
        self.assertAlmostEqual(d["total"]["kosten"], 4214.66, places=2)

    def test_englische_summenzeile_gefiltert(self):
        d = parse_export(write_csv(self.GOOGLE_EN))
        self.assertNotIn("Total: account", [c["name"] for c in d["campaigns"]])

    def test_cost_pro_conv_nicht_als_kosten_genommen(self):
        d = parse_export(write_csv(self.GOOGLE_EN))
        self.assertAlmostEqual(d["campaigns"][1]["kosten"], 2980.10, places=2)

    def test_kampagne_die_mit_total_beginnt_bleibt(self):
        p = write_csv("Campaign,Impressions,Clicks,Cost,Conversions\n"
                      'Total Rewards Brand,10,1,1.00,0\n')
        self.assertEqual(parse_export(p)["campaigns"][0]["name"], "Total Rewards Brand")

    def test_englischer_meta_export_nicht_als_google_erkannt(self):
        p = write_csv("Campaign name,Impressions,Link clicks,Amount spent (USD),"
                      "Results,Purchase conversion value\n"
                      'Retargeting,"12,000","1,200","345.60",18,"2,400.00"\n')
        d = parse_export(p)
        self.assertEqual(d["source"], "Meta Ads")
        self.assertAlmostEqual(d["campaigns"][0]["kosten"], 345.6, places=2)

    def test_englische_segmentspalte_wird_gemeldet(self):
        p = write_csv("Campaign,Device,Impressions,Clicks,Cost,Conversions\n"
                      "Brand,Mobile,10,1,1.00,0\nBrand,Desktop,20,2,2.00,1\n")
        d = parse_export(p)
        self.assertIn("Device", d["segments"])
        self.assertEqual(len(d["campaigns"]), 1)
        self.assertAlmostEqual(d["campaigns"][0]["kosten"], 3.0, places=2)

    def test_waehrung_aus_der_kostenspalte(self):
        usd = parse_export(write_csv(
            "Campaign,Impressions,Clicks,Cost (USD),Conversions\n"
            "Brand,10,1,1.00,0\n"))
        self.assertEqual(usd["currency"], "$")
        eur_export = parse_export(write_csv(
            "Kampagne,Impressionen,Klicks,Kosten,Conversions\n"
            'Brand,10,1,"1,00",0\n'))
        self.assertEqual(eur_export["currency"], "€")

    def test_report_zeigt_fremdwaehrung(self):
        d = parse_export(write_csv(
            "Campaign,Impressions,Clicks,Cost (USD),Conversions,Conv. value\n"
            'Brand,"10,000",100,"1,234.56",10,"5,000.00"\n'))
        out = render("Kunde", "August 2026", [d], DEFAULT_BRAND,
                     build_commentary(d, None))
        self.assertIn("1.234,56 $", out)
        self.assertNotIn("1.234,56 €", out)


class TestKommentar(unittest.TestCase):
    def setUp(self):
        self.juli = parse_export(SAMPLES / "kampagnen-juli-2026.csv")
        self.juni = parse_export(SAMPLES / "kampagnen-juni-2026.csv")

    def test_schwache_kampagne_erkannt(self):
        text = " ".join(build_commentary(self.juli, self.juni))
        self.assertIn("YouTube Awareness Q3", text)   # ROAS 0,57 < 1,5
        self.assertIn("Effizienzschwelle", text)

    def test_vorperioden_deltas_enthalten(self):
        text = build_commentary(self.juli, self.juni)[0]
        self.assertIn("gegenüber der Vorperiode", text)

    def test_ohne_vorperiode_kein_vergleich(self):
        text = " ".join(build_commentary(self.juli, None))
        self.assertNotIn("Vorperiode", text)


class TestRendering(unittest.TestCase):
    def test_report_vollstaendig(self):
        history = [parse_export(SAMPLES / f"kampagnen-{m}-2026.csv")
                   for m in ("mai", "juni", "juli")]
        h = render("Testkunde GmbH", "Juli 2026", history, dict(DEFAULT_BRAND),
                   build_commentary(history[-1], history[-2]))
        for probe in ("Testkunde GmbH", "Entwicklung über 3 Monate", "polyline",
                      "Google Ads", "delta-", "</html>"):
            self.assertIn(probe, h)

    def test_html_escaping(self):
        history = [parse_export(SAMPLES / "kampagnen-juli-2026.csv")]
        h = render('<script>alert(1)</script>', "Juli", history,
                   dict(DEFAULT_BRAND), ["Text"])
        self.assertNotIn("<script>alert(1)</script>", h)


class TestMultipart(unittest.TestCase):
    def test_dateien_und_felder(self):
        boundary = "XBOUND"
        body = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="files"; filename="a.csv"\r\n'
            "Content-Type: text/csv\r\n\r\n"
            "Kampagne,Kosten\r\n"
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="kunde"\r\n\r\n'
            "Beispiel GmbH\r\n"
            f"--{boundary}--\r\n"
        ).encode()
        files, fields = parse_multipart(body, f'multipart/form-data; boundary={boundary}')
        self.assertEqual(files[0][0], "a.csv")
        self.assertIn(b"Kampagne,Kosten", files[0][1])
        self.assertEqual(fields["kunde"], "Beispiel GmbH")

    def test_pfad_traversal_abgewehrt(self):
        boundary = "XBOUND"
        body = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="files"; filename="../../evil.csv"\r\n\r\n'
            "x\r\n"
            f"--{boundary}--\r\n"
        ).encode()
        files, _ = parse_multipart(body, f'multipart/form-data; boundary={boundary}')
        self.assertEqual(files[0][0], "evil.csv")


class TestPython39(unittest.TestCase):
    """macOS liefert Python 3.9 mit („ist doch eh schon drauf") — genau darauf
    muss der ausgelieferte Code laufen. Ohne diese Absicherung schlägt
    ``str | None`` erst beim Beta-Nutzer zu, mit einem Traceback beim Start."""

    SHIPPED = ("app.py", "build_report.py")

    def quelle(self, name: str) -> str:
        return (Path(__file__).parent / name).read_text(encoding="utf-8")

    def test_syntax_ist_39_kompatibel(self):
        """Fängt 3.10+-Syntax ab (match-Statement, geklammerte with-Blöcke)."""
        for name in self.SHIPPED:
            with self.subTest(datei=name):
                ast.parse(self.quelle(name), filename=name, feature_version=(3, 9))

    def test_annotations_werden_nicht_ausgewertet(self):
        """``from __future__ import annotations`` macht ``str | None`` in
        Signaturen zu einem String — sonst: TypeError beim Import."""
        for name in self.SHIPPED:
            with self.subTest(datei=name):
                baum = ast.parse(self.quelle(name), filename=name)
                futures = [a.name for k in baum.body
                           if isinstance(k, ast.ImportFrom) and k.module == "__future__"
                           for a in k.names]
                self.assertIn("annotations", futures)

    def test_kein_pep604_ausserhalb_von_annotationen(self):
        """``int | None`` in normalem Code (z. B. isinstance) rettet der
        Future-Import nicht — solche Stellen müssen typing.Optional nutzen."""
        for name in self.SHIPPED:
            baum = ast.parse(self.quelle(name), filename=name)
            annotationen = set()
            for k in ast.walk(baum):
                if isinstance(k, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    ziele = [a.annotation for a in k.args.args + k.args.kwonlyargs]
                    annotationen.update(id(x) for x in ziele + [k.returns] if x)
                elif isinstance(k, ast.AnnAssign):
                    annotationen.add(id(k.annotation))
            innerhalb = {id(sub) for a in ast.walk(baum) if id(a) in annotationen
                         for sub in ast.walk(a)}
            for k in ast.walk(baum):
                if (isinstance(k, ast.BinOp) and isinstance(k.op, ast.BitOr)
                        and id(k) not in innerhalb):
                    self.assertIsNot(
                        type(k.right), ast.Constant,
                        f"{name}:{k.lineno}: PEP-604-Union außerhalb einer Annotation")

    def test_mindestversion_wird_geprueft(self):
        for name in self.SHIPPED:
            with self.subTest(datei=name):
                self.assertIn("MIN_PYTHON = (3, 9)", self.quelle(name))


if __name__ == "__main__":
    unittest.main()
