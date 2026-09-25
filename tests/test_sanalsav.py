import contextlib
import io
import pathlib
import sys
import tempfile
import unittest

KÖK = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KÖK))

import ana
from ondil import insa
from ondil.hizalama import hizala
from ondil.html import html_üret
from ondil.kurallar import bağlam_işlevi, sıralı_ayır
from ondil.rapor import istatistik, rapor_üret
from sesbiçim.harf import BOŞ, uzaklık, yol


def listeler(*adlar, boy=None):
    sözlükler = [ana.liste_yükle(KÖK / "diller" / f"{ad}.txt") for ad in adlar]
    satırlar = [(l[0][0],) + tuple(x[1] for x in l) for l in zip(*sözlükler)]
    return satırlar[:boy] if boy else satırlar


class SesbiçimTesti(unittest.TestCase):
    def test_komşu_harfler_tek_adım(self):
        self.assertEqual(uzaklık("b", "p"), 1)
        self.assertEqual(uzaklık("a", "a"), 0)

    def test_sıçrama_doğal_yola_bölünür(self):
        y = yol("k", "f")
        self.assertEqual((y[0], y[-1]), ("k", "f"))
        for a, b in zip(y, y[1:]):
            self.assertEqual(uzaklık(a, b), 1)


class HizalamaTesti(unittest.TestCase):
    def test_sütunlar_iki_sözcüğü_de_kapsar(self):
        sütunlar = hizala(list("köpek"), list("dog"))
        self.assertEqual("".join(a for a, _ in sütunlar if a != BOŞ), "köpek")
        self.assertEqual("".join(b for _, b in sütunlar if b != BOŞ), "dog")


class KuralTesti(unittest.TestCase):
    def test_sınıf_bağlamı(self):
        ön_ünlü_önünde = bağlam_işlevi("ön ünlü önünde")
        self.assertTrue(ön_ünlü_önünde(list("ki"), 0))
        self.assertFalse(ön_ünlü_önünde(list("ku"), 0))

    def test_sıralı_ayrım(self):
        biçimler = [list("kan"), list("kin"), list("kun"), list("ak")]
        gruplar = [
            ("k", [(0, 0), (2, 0), (3, 1)]),
            ("ç", [(1, 0)]),
        ]
        ayrım, takılan = sıralı_ayır(gruplar, biçimler)
        self.assertIsNone(takılan)
        self.assertEqual(ayrım["k"][0], "her yerde")
        bağlam = bağlam_işlevi(ayrım["ç"][0])
        self.assertTrue(bağlam(biçimler[1], 0))
        self.assertFalse(bağlam(biçimler[0], 0))


class SeriTesti(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.çiftler = listeler("türkçe", "azerbaycanca", boy=30)
        cls.seri = insa.seri_oluştur(cls.çiftler, ("Türkçe", "Azerbaycanca"))

    def test_istisnasız(self):
        self.assertEqual(self.seri.istisnalar, [])

    def test_kör_türetim_hedefi_üretir(self):
        for kno, row in enumerate(self.çiftler):
            for dal in range(2):
                biçimler = insa.kör_türet(self.seri.proto_kelimeler[kno], dal,
                                          self.seri.tablolar[dal],
                                          self.seri.katman[dal])
                self.assertEqual("".join(biçimler[-1]), row[1 + dal])

    def test_ön_dil_sözcüğü_sütun_başına_bir_ses(self):
        for w, h in zip(self.seri.proto_kelimeler, self.seri.hizalamalar):
            self.assertEqual(len(w), len(h))

    def test_rapor_ve_html(self):
        ist = istatistik(self.seri)
        self.assertEqual(ist["istisna"], 0)
        self.assertIn("KATMAN BAŞINA ORTALAMA KURAL", rapor_üret(self.seri))
        self.assertIn("<!DOCTYPE html>", html_üret(self.seri))

    def test_üç_dil(self):
        çiftler = listeler("türkçe", "azerbaycanca", "türkmence", boy=15)
        seri = insa.seri_oluştur(çiftler, ("A", "B", "C"))
        self.assertEqual(seri.istisnalar, [])


class EşikTesti(unittest.TestCase):
    def test_istisna_yalnız_kural_dışı_sözcüklerde(self):
        çiftler = listeler("türkçe", "azerbaycanca", boy=40)
        seri = insa.seri_oluştur(çiftler, ("A", "B"), 0, 2)
        beklenen = {(kno, d) for d in range(2) for ç in seri.düzensiz[d]
                    for kno, _ in seri.korr_yerleri[ç]}
        bozuk = {(kno, d) for kno, d, _, _ in seri.istisnalar}
        self.assertLessEqual(bozuk, beklenen)


class ÖlçütTesti(unittest.TestCase):
    def test_açıklama_uzunluğu(self):
        seri = insa.seri_oluştur(listeler("türkçe", "azerbaycanca", boy=20), ("A", "B"))
        m = istatistik(seri)["mdl"]
        self.assertAlmostEqual(m["toplam"], m["sözlük"] + m["kural"] + m["istisna"])
        self.assertEqual(m["istisna"], 0)
        self.assertGreater(m["kural"], 0)


class KomutSatırıTesti(unittest.TestCase):
    def test_rapor_ve_html_yazılır(self):
        with tempfile.TemporaryDirectory() as dizin:
            dizin = pathlib.Path(dizin)
            for ad, sözcükler in (("a", "ben sen su taş"), ("b", "men sen su daş")):
                (dizin / f"{ad}.txt").write_text(
                    "\n".join(f"s{i} {s}" for i, s in enumerate(sözcükler.split())),
                    encoding="utf-8")
            rapor = dizin / "rapor.txt"
            with contextlib.redirect_stdout(io.StringIO()):
                ana.main([str(dizin / "a.txt"), str(dizin / "b.txt"),
                          "--rapor", str(rapor)])
            self.assertIn("istisna                         : 0",
                          rapor.read_text(encoding="utf-8"))
            self.assertTrue(rapor.with_suffix(".html").exists())


if __name__ == "__main__":
    unittest.main()
