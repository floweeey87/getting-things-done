#!/usr/bin/env python3
"""Test-Suite für AdReport: Parser (beide Quellen), Zahlenformate,
Kommentar-Regeln, Rendering und den Multipart-Parser der App.

    python3 -m unittest test_adreport -v
"""

import tempfile
import unittest
from pathlib import Path

from app import parse_multipart
from build_report import (DEFAULT_BRAND, build_commentary, de, eur,
                          parse_export, parse_number, pct_delta, render)

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


if __name__ == "__main__":
    unittest.main()
