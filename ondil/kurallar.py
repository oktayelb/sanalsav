# -*- coding: utf-8 -*-
"""Ses değişim kurallarının bağlam koşulları.

Bir Ön Dil harfi bir dalda birden çok sese gidiyorsa, kuralları ayrıştırmak
için önce buradaki bağlam koşulları denenir (asgari harf hedefi: yeni harf
türetmeden önce bağlamla genelleme). Koşullar özgülden genele sıralıdır;
uygulamada bir konuma birden çok kural uyarsa en özgül olan kazanır,
"her yerde" kuralı en sona kalır.
"""

from sesbiçim.harf import ünlü_mü


def _başta(w, i):
    return i == 0


def _sonda(w, i):
    return i == len(w) - 1


def _ünlü_önünde(w, i):
    return i + 1 < len(w) and ünlü_mü(w[i + 1])


def _ünsüz_önünde(w, i):
    return i + 1 < len(w) and not ünlü_mü(w[i + 1])


def _ünlü_ardında(w, i):
    return i > 0 and ünlü_mü(w[i - 1])


def _ünsüz_ardında(w, i):
    return i > 0 and not ünlü_mü(w[i - 1])


def _içte(w, i):
    return 0 < i < len(w) - 1


def _her_yerde(w, i):
    return True


BAĞLAMLAR = [
    ("söz başında", _başta),
    ("söz sonunda", _sonda),
    ("ünlü önünde", _ünlü_önünde),
    ("ünsüz önünde", _ünsüz_önünde),
    ("ünlü ardında", _ünlü_ardında),
    ("ünsüz ardında", _ünsüz_ardında),
    ("söz içinde", _içte),
    ("her yerde", _her_yerde),
]

BAĞLAM_SIRASI = [ad for ad, _ in BAĞLAMLAR]
_İŞLEVLER = dict(BAĞLAMLAR)


def bağlam_işlevi(ad):
    return _İŞLEVLER[ad]


def ayır_biçimlerle(kendi, diğer):
    """ayır'ın hazır (biçim, indeks) çiftleriyle çalışan kardeşi.

    `kendi` ve `diğer`, doğrudan (kelime_biçimi, konum) çiftleridir; proto
    konumları yerine HERHANGİ bir katmanın biçimleri verilebilir. Böylece
    aynı bağlam koşulları ara Ön Dil katmanlarında da denenir (bir ayrım
    proto'da değil, sesler kaydıktan sonraki bir alt dilde belirebilir).
    """
    if not kendi or not diğer:
        return None
    for ad, f in BAĞLAMLAR[:-1]:
        if all(f(w, i) for w, i in kendi) and not any(
            f(w, i) for w, i in diğer
        ):
            return ad
    return None


def ayır(kendi_yerleri, diğer_yerleri, protolar):
    """Bir kural grubunu diğerlerinden ayıran tek bağlam koşulu arar.

    Koşul, grubun bütün görüldüğü yerlerde doğru, diğer bütün gruplarınkinde
    yanlış olmalıdır. Bulunamazsa None döner (o zaman yeni harf türetilir).
    """
    for ad, f in BAĞLAMLAR[:-1]:
        if all(f(protolar[k], i) for k, i in kendi_yerleri) and not any(
            f(protolar[k], i) for k, i in diğer_yerleri
        ):
            return ad
    return None
