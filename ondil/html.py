import html as _html
import json

from sesbiçim.harf import BOŞ, dizi_harfleri, dizi_mi

from .insa import GÖÇÜŞÜM, _kural_seç
from .rapor import istatistik, katman_adı, kural_metni


def _izli_katman(w, kurallar):
    if kurallar and kurallar[0].bağlam == GÖÇÜŞÜM:
        çiftler = {tuple(dizi_harfleri(k.kaynak)): n for n, k in enumerate(kurallar)}
        adımlar = [[t, [t], -1] for t in w]
        i = 0
        while i < len(w) - 1:
            n = çiftler.get((w[i], w[i + 1]))
            if n is not None:
                adımlar[i] = [w[i], [w[i + 1]], n]
                adımlar[i + 1] = [w[i + 1], [w[i]], n]
                i += 2
            else:
                i += 1
        return adımlar
    adımlar = []
    no = {id(k): n for n, k in enumerate(kurallar)}
    for i, t in enumerate(w):
        k = _kural_seç(kurallar, w, i)
        if k is None:
            adımlar.append([t, [t], -1])
        elif dizi_mi(k.hedef):
            adımlar.append([t, dizi_harfleri(k.hedef), no[id(k)]])
        elif k.hedef == BOŞ:
            adımlar.append([t, [], no[id(k)]])
        else:
            adımlar.append([t, [k.hedef], no[id(k)]])
    return adımlar


def _veri(seri):
    ist = istatistik(seri)
    adlar = list(seri.dal_adları)
    dallar = []
    for d, ad in enumerate(adlar):
        L = seri.katman[d]
        katmanlar = []
        for j in range(0, L + 1):
            kurallar = seri.tablolar[d].get(j, []) if j else []
            k_ist = ist["dallar"][d]["katmanlar"][j]
            katmanlar.append({
                "j": j,
                "ad": katman_adı(ad, j, L),
                "harf": k_ist["harf"],
                "doğan": k_ist["doğan"],
                "yiten": k_ist["yiten"],
                "kurallar": [{"m": kural_metni(k)} for k in kurallar],
            })
        x = ist["dallar"][d]
        dallar.append({
            "ad": ad, "L": L, "kural": x["kural"],
            "ortalama": round(x["ortalama"], 2),
            "silme": x["silme"], "en_az_silme": x["en_az_silme"],
            "katmanlar": katmanlar,
        })

    kelimeler = []
    for kno, row in enumerate(seri.çiftler):
        izler = []
        for d in range(len(adlar)):
            biçimler = seri.türevler[kno][d]
            adımlar = [None]
            for j in range(1, seri.katman[d] + 1):
                adımlar.append(_izli_katman(biçimler[j - 1],
                                            seri.tablolar[d].get(j, [])))
            izler.append({"b": biçimler, "a": adımlar})
        kelimeler.append({
            "anlam": row[0], "hedef": list(row[1:]),
            "proto": seri.proto_kelimeler[kno], "iz": izler,
        })

    return {
        "diller": adlar,
        "özet": {
            "proto": ist["proto"], "temel": ist["temel"],
            "türetilmiş": ist["türetilmiş"], "sanal": ist["sanal"],
            "etiketler": ist["etiketler"],
            "istisna": ist["istisna"], "türetim": ist["türetim"],
            "düzenlilik": round(ist["düzenlilik"], 1),
            "toplam_kural": ist["toplam_kural"],
            "toplam_katman": ist["toplam_katman"],
            "ortalama": round(ist["genel_ortalama"], 2),
            "tüm_harf": ist["tüm_harf"],
            "proto_boy": round(ist["proto_boy"], 2),
        },
        "dallar": dallar,
        "kelimeler": kelimeler,
        "istisnalar": [[k, d] for k, d, _, _ in seri.istisnalar],
    }


def html_üret(seri):
    veri = _veri(seri)
    başlık = " ~ ".join(seri.dal_adları) + " Ön Dil Serisi"
    js = json.dumps(veri, ensure_ascii=False).replace("</", "<\\/")
    return (_ŞABLON.replace("__BAŞLIK__", _html.escape(başlık))
            .replace("__VERİ__", js))


_ŞABLON = r"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__BAŞLIK__</title>
<style>
:root {
  --bg: #f7f6f2; --panel: #ffffff; --ink: #1d1d1b; --muted: #6b6a64;
  --line: #e2e0d8; --accent: #2f5d8a; --accent-soft: #e3ecf5;
  --new: #1f7a4d; --new-soft: #dff2e7; --lost: #a23b2a; --lost-soft: #f7e1dc;
  --mark: #8a6d1f; --mark-soft: #f5edd6; --sel: #2f5d8a;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #151514; --panel: #1f1f1d; --ink: #ecebe6; --muted: #9c9a92;
    --line: #34332f; --accent: #7fb0e0; --accent-soft: #22303e;
    --new: #6fd19f; --new-soft: #1c3328; --lost: #f09483; --lost-soft: #3a211c;
    --mark: #e0c270; --mark-soft: #36301d; --sel: #7fb0e0;
  }
}
:root[data-theme="dark"] {
  --bg: #151514; --panel: #1f1f1d; --ink: #ecebe6; --muted: #9c9a92;
  --line: #34332f; --accent: #7fb0e0; --accent-soft: #22303e;
  --new: #6fd19f; --new-soft: #1c3328; --lost: #f09483; --lost-soft: #3a211c;
  --mark: #e0c270; --mark-soft: #36301d; --sel: #7fb0e0;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink);
  font: 15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 1200px; margin: 0 auto; padding: 24px 16px 64px; }
h1 { font-size: 1.5rem; margin: 0 0 4px; }
h2 { font-size: 1.1rem; margin: 0 0 10px; }
h3 { font-size: .95rem; margin: 18px 0 8px; color: var(--muted);
  text-transform: uppercase; letter-spacing: .04em; }
.sub { color: var(--muted); margin: 0 0 20px; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px; margin-bottom: 24px; }
.card { background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
  padding: 10px 14px; }
.card b { display: block; font-size: 1.4rem; font-variant-numeric: tabular-nums; }
.card span { color: var(--muted); font-size: .85rem; }
.card small { color: var(--muted); display: block; font-size: .78rem; }
.tree { background: var(--panel); border: 1px solid var(--line); border-radius: 12px;
  padding: 16px; margin-bottom: 20px; overflow-x: auto; }
.root { display: flex; justify-content: center; margin-bottom: 14px; }
.branches { display: grid; gap: 16px; }
.branch h4 { margin: 0 0 8px; text-align: center; font-size: .9rem; color: var(--muted); }
.col { display: flex; flex-direction: column; align-items: center; gap: 0; }
.node { border: 1px solid var(--line); background: var(--bg); color: var(--ink);
  border-radius: 8px; padding: 6px 12px; min-width: 190px; text-align: center;
  cursor: pointer; font: inherit; }
.node:hover { border-color: var(--accent); }
.node.sel { border-color: var(--sel); background: var(--accent-soft);
  box-shadow: 0 0 0 2px var(--sel) inset; }
.node .n { font-weight: 600; }
.node .m { color: var(--muted); font-size: .78rem; }
.node.proto, .node.leaf { font-weight: 600; }
.node.leaf { border-width: 2px; }
.edge { width: 2px; height: 14px; background: var(--line); }
.panel { background: var(--panel); border: 1px solid var(--line); border-radius: 12px;
  padding: 16px; }
.chips { display: flex; flex-wrap: wrap; gap: 5px; }
.chip { border: 1px solid var(--line); border-radius: 6px; padding: 1px 8px;
  font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: .95rem; }
.chip.new { background: var(--new-soft); border-color: var(--new); color: var(--new); }
.chip.tg { background: var(--mark-soft); border-color: var(--mark); color: var(--mark); }
.chip.lost { background: var(--lost-soft); border-color: var(--lost); color: var(--lost);
  text-decoration: line-through; }
.legend { color: var(--muted); font-size: .82rem; margin-top: 6px; }
.rules { columns: 3 240px; column-gap: 20px; font-family: ui-monospace, Menlo, monospace;
  font-size: .85rem; }
.rules div { break-inside: avoid; padding: 1px 0; }
.rules .cnt { color: var(--muted); }
.tools { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; margin: 8px 0; }
input[type=search] { font: inherit; padding: 5px 10px; border-radius: 6px;
  border: 1px solid var(--line); background: var(--bg); color: var(--ink); min-width: 200px; }
label { color: var(--muted); font-size: .88rem; }
.tbl { width: 100%; overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: .9rem; }
th, td { text-align: left; padding: 4px 8px; border-bottom: 1px solid var(--line);
  vertical-align: top; }
th { color: var(--muted); font-weight: 500; position: sticky; top: 0; background: var(--panel); }
tr.w { cursor: pointer; }
tr.w:hover td { background: var(--accent-soft); }
.f { font-family: ui-monospace, "SF Mono", Menlo, monospace; white-space: nowrap; }
.t { border-radius: 3px; padding: 0 1px; }
.t.ch { background: var(--new-soft); color: var(--new); font-weight: 600; }
.t.src { background: var(--accent-soft); color: var(--accent); font-weight: 600; }
.t.del { background: var(--lost-soft); color: var(--lost); text-decoration: line-through; }
.t.tg { color: var(--mark); }
.muted { color: var(--muted); }
dialog { border: 1px solid var(--line); border-radius: 12px; background: var(--panel);
  color: var(--ink); max-width: min(900px, 94vw); width: 100%; padding: 18px; }
dialog::backdrop { background: rgb(0 0 0 / .4); }
.path { display: grid; gap: 14px; }
.path ol { margin: 0; padding-left: 0; list-style: none; }
.path li { padding: 2px 0; display: flex; gap: 10px; }
.path li .ly { color: var(--muted); min-width: 130px; font-size: .85rem; }
.x { float: right; font: inherit; border: 1px solid var(--line); background: var(--bg);
  color: var(--ink); border-radius: 6px; padding: 2px 10px; cursor: pointer; }
.theme { position: fixed; top: 10px; right: 12px; }
</style>
</head>
<body>
<button class="x theme" id="tema" title="Açık / koyu">◐</button>
<main>
  <h1 id="başlık"></h1>
  <p class="sub" id="altbaşlık"></p>
  <div class="cards" id="kartlar"></div>
  <div class="tree">
    <div class="root" id="kök"></div>
    <div class="branches" id="dallar"></div>
  </div>
  <div class="panel" id="panel"></div>
</main>
<dialog id="yol"><button class="x" onclick="this.parentNode.close()">kapat</button><div id="yoliçi"></div></dialog>
<script>
const V = __VERİ__;
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const isTag = (t) => /[₀₁₂₃₄₅₆₇₈₉]/.test(t);
let seçili = {d: -1, j: 0};
let arama = '';

try { const t = localStorage.getItem('tema'); if (t) document.documentElement.dataset.theme = t; } catch (e) {}
$('#tema').onclick = () => {
  const koyu = matchMedia('(prefers-color-scheme: dark)').matches;
  const şimdi = document.documentElement.dataset.theme || (koyu ? 'dark' : 'light');
  const yeni = şimdi === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = yeni;
  try { localStorage.setItem('tema', yeni); } catch (e) {}
};

function tok(t, cls) {
  if (t === '0') t = '∅';
  return `<span class="t ${cls || (isTag(t) ? 'tg' : '')}">${esc(t)}</span>`;
}
function biçim(ts) { return ts.length ? ts.map(t => tok(t)).join('') : '<span class="muted">∅</span>'; }

function yeniBiçim(adımlar) {
  let s = '';
  for (const [kaynak, çıktı, k] of adımlar) {
    for (const t of çıktı) s += tok(t, k >= 0 && !(çıktı.length === 1 && çıktı[0] === kaynak) ? 'ch' : '');
  }
  return s || '<span class="muted">∅</span>';
}
function eskiBiçim(adımlar) {
  let s = '';
  for (const [kaynak, çıktı, k] of adımlar) {
    const değişti = k >= 0 && !(çıktı.length === 1 && çıktı[0] === kaynak);
    s += tok(kaynak, değişti ? (çıktı.length ? 'src' : 'del') : '');
  }
  return s || '<span class="muted">∅</span>';
}

function kartlar() {
  const Ö = V.özet;
  const derin = V.dallar.map(d => `${d.ad} ${d.L}`).join(' · ');
  const ort = V.dallar.map(d => `${d.ad} ${d.ortalama}`).join(' · ');
  const sil = V.dallar.map(d => `${d.ad} ${d.silme} (kaçınılmaz ${d.en_az_silme})`).join(' · ');
  const c = [
    [Ö.proto.length, 'Ön Dil harfi', `temel ${Ö.temel.length} + türetilmiş ${Ö.türetilmiş.length}`],
    [Ö.etiketler.length, 'ara katmanda etiketli harf', `seri boyunca ${Ö.tüm_harf} ayrı harf`],
    [V.dallar.map(d => d.L).join(' / '), 'katman (ön dile uzaklık)', derin],
    [Ö.ortalama, 'kural / katman (ortalama)', ort],
    [V.dallar.map(d => d.silme).join(' / '), 'ses düşmesi', sil],
    ['%' + Ö.düzenlilik, 'düzenlilik', `${Ö.istisna} istisna / ${Ö.türetim} türetim`],
  ];
  $('#kartlar').innerHTML = c.map(([b, s, m]) =>
    `<div class="card"><b>${esc(b)}</b><span>${esc(s)}</span><small>${esc(m)}</small></div>`).join('');
}

function ağaç() {
  $('#kök').innerHTML = `<button class="node proto ${seçili.d < 0 ? 'sel' : ''}" data-d="-1" data-j="0">
    <div class="n">*Ön Dil</div><div class="m">${V.özet.proto.length} harf</div></button>`;
  const dl = $('#dallar');
  dl.style.gridTemplateColumns = `repeat(${V.dallar.length}, minmax(200px, 1fr))`;
  dl.innerHTML = V.dallar.map((D, d) => {
    let s = `<div class="branch"><h4>${esc(D.ad)} dalı · ${D.L} katman</h4><div class="col">`;
    for (let j = 1; j <= D.L; j++) {
      const K = D.katmanlar[j];
      const son = j === D.L;
      const sel = seçili.d === d && seçili.j === j ? 'sel' : '';
      s += `<div class="edge"></div><button class="node ${son ? 'leaf' : ''} ${sel}" data-d="${d}" data-j="${j}">
        <div class="n">${esc(son ? D.ad : K.ad)}</div>
        <div class="m">katman ${j} · ${K.harf.length} harf (+${K.doğan.length}) · ${K.kurallar.length} kural</div></button>`;
    }
    return s + '</div></div>';
  }).join('');
  document.querySelectorAll('.node').forEach(b => b.onclick = () => {
    seçili = {d: +b.dataset.d, j: +b.dataset.j};
    history.replaceState(null, '', seçili.d < 0 ? '#' : `#d=${seçili.d}&j=${seçili.j}`);
    ağaç(); panel();
  });
}

function eşleşir(W) {
  if (!arama) return true;
  const q = arama.toLowerCase();
  return W.anlam.toLowerCase().includes(q) || W.hedef.some(h => h.toLowerCase().includes(q));
}

function araçlar() {
  return `<div class="tools">
    <input type="search" id="ara" placeholder="anlam ya da sözcük ara" value="${esc(arama)}">
    <span class="muted">Bir satıra basınca sözcüğün bütün yolu açılır.</span></div>`;
}
function araçBağla() {
  const a = $('#ara');
  a.oninput = () => { arama = a.value; tablo(); };
}

function panel() {
  const P = $('#panel');
  if (seçili.d < 0) {
    const Ö = V.özet;
    const sanal = new Set(Ö.sanal), tür = new Set(Ö.türetilmiş);
    P.innerHTML = `<h2>*Ön Dil (katman 0)</h2>
      <h3>Harf dağarcığı · ${Ö.proto.length} harf</h3>
      <div class="chips">${Ö.proto.map(t => `<span class="chip ${tür.has(t) ? 'tg' : ''}">${esc(t)}</span>`).join('')}</div>
      <p class="legend">Sarı: türetilmiş (alt simgeli) harf — yansımaları hiçbir doğal ortamla ya da yasa sırasıyla aynı yerdeki öbür sesten ayrılamadığı için ayrı ses sayılır.
      ${Ö.sanal.length ? 'Sanal harfler (' + Ö.sanal.map(esc).join(' ') + ') hiçbir yazıda yoktur, özellik uzayından kurulur. ' : ''}
      Ön dil sözcüğü, hizalamanın sütun başına bir sesidir (ortalama ${Ö.proto_boy} ses).</p>
      ${araçlar()}<div class="tbl" id="tablo"></div>`;
    araçBağla(); tablo(); return;
  }
  const D = V.dallar[seçili.d], K = D.katmanlar[seçili.j];
  const önceki = seçili.j === 1 ? '*Ön Dil' : D.katmanlar[seçili.j - 1].ad;
  const yeni = new Set(K.doğan);
  const kural = K.kurallar.map((r, i) => `<div>${esc(r.m)} <span class="cnt" id="kc${i}"></span></div>`).join('');
  P.innerHTML = `<h2>${esc(K.ad)} <span class="muted">· ${esc(D.ad)} dalı, katman ${seçili.j} / ${D.L}</span></h2>
    <p class="muted">${esc(önceki)} → ${esc(K.ad)}</p>
    <h3>Harf dağarcığı · ${K.harf.length} harf</h3>
    <div class="chips">${K.harf.map(t => `<span class="chip ${yeni.has(t) ? 'new' : isTag(t) ? 'tg' : ''}">${esc(t)}</span>`).join('')}
      ${K.yiten.map(t => `<span class="chip lost">${esc(t)}</span>`).join('')}</div>
    <p class="legend">Yeşil: bu katmanda doğan harf · üstü çizili: bu katmanda yiten harf · sarı: etiketli (alt simgeli) harf.</p>
    <h3>Bu katmanın kuralları · ${K.kurallar.length}</h3>
    <p class="legend">Aynı harfe birden çok yasa uyarsa üstteki önce işler.</p>
    <div class="rules">${kural || '<span class="muted">Bu katmanda kural yok.</span>'}</div>
    ${araçlar()}<div class="tbl" id="tablo"></div>`;
  const say = new Array(K.kurallar.length).fill(0);
  for (const W of V.kelimeler) for (const a of W.iz[seçili.d].a[seçili.j]) if (a[2] >= 0) say[a[2]]++;
  say.forEach((n, i) => { const e = $('#kc' + i); if (e) e.textContent = `(${n} konum)`; });
  araçBağla(); tablo();
}

function tablo() {
  const T = $('#tablo');
  const bozuk = new Set(V.istisnalar.map(([k, d]) => k + ':' + d));
  let s;
  if (seçili.d < 0) {
    s = `<table><thead><tr><th>#</th><th>anlam</th><th>*Ön Dil</th>${V.diller.map(d => `<th>${esc(d)}</th>`).join('')}</tr></thead><tbody>`;
    V.kelimeler.forEach((W, k) => {
      if (!eşleşir(W)) return;
      s += `<tr class="w" data-k="${k}"><td class="muted">${k + 1}</td><td>${esc(W.anlam)}</td>
        <td class="f">*${biçim(W.proto)}</td>${W.hedef.map(h => `<td class="f">${esc(h)}</td>`).join('')}</tr>`;
    });
  } else {
    const d = seçili.d, j = seçili.j, D = V.dallar[d];
    const önAd = j === 1 ? '*Ön Dil' : D.katmanlar[j - 1].ad;
    s = `<table><thead><tr><th>#</th><th>anlam</th><th>${esc(önAd)}</th><th>${esc(D.katmanlar[j].ad)}</th><th>hedef (${esc(D.ad)})</th></tr></thead><tbody>`;
    let değişen = 0;
    V.kelimeler.forEach((W, k) => {
      if (!eşleşir(W)) return;
      const a = W.iz[d].a[j];
      const ch = a.some(([x, y, r]) => r >= 0 && !(y.length === 1 && y[0] === x));
      if (ch) değişen++;
      const im = bozuk.has(k + ':' + d) ? ' ✗' : '';
      s += `<tr class="w" data-k="${k}"><td class="muted">${k + 1}</td><td>${esc(W.anlam)}</td>
        <td class="f">${eskiBiçim(a)}</td><td class="f">${yeniBiçim(a)}</td>
        <td class="f muted">${esc(W.hedef[d])}${im}</td></tr>`;
    });
    s = `<p class="muted">${değişen} sözcük bu katmanda değişti.</p>` + s;
  }
  T.innerHTML = s + '</tbody></table>';
  T.querySelectorAll('tr.w').forEach(r => r.onclick = () => yol(+r.dataset.k));
}

function yol(k) {
  const W = V.kelimeler[k];
  let s = `<h2>${k + 1}. ${esc(W.anlam)} <span class="muted">(${W.hedef.map(esc).join(' ~ ')})</span></h2>
    <p class="f">*${biçim(W.proto)}</p><div class="path">`;
  V.dallar.forEach((D, d) => {
    s += `<div><h3>${esc(D.ad)} dalı</h3><ol>`;
    for (let j = 1; j <= D.L; j++) {
      const a = W.iz[d].a[j];
      const ch = a.some(([x, y, r]) => r >= 0 && !(y.length === 1 && y[0] === x));
      const kurallar = [...new Set(a.filter(([x, y, r]) => r >= 0 && !(y.length === 1 && y[0] === x)).map(x => x[2]))]
        .map(r => D.katmanlar[j].kurallar[r].m);
      s += `<li><span class="ly">${j}. ${esc(D.katmanlar[j].ad)}</span><span class="f">${ch ? yeniBiçim(a) : '<span class="muted">' + biçim(W.iz[d].b[j]) + '</span>'}</span>
        <span class="muted" style="font-size:.8rem">${kurallar.map(esc).join(' · ')}</span></li>`;
    }
    s += '</ol></div>';
  });
  $('#yoliçi').innerHTML = s + '</div>';
  $('#yol').showModal();
}

$('#başlık').textContent = V.diller.join(' ~ ') + ' — Ön Dil Serisi';
$('#altbaşlık').textContent = 'Üstte ön ana dil, altında ara katmanlar, en altta girdi diller. Bir katmana basınca harfleri, kuralları ve sözcüklerin o katmandaki biçimini görürsünüz.';
const h = new URLSearchParams(location.hash.slice(1));
if (h.has('d')) {
  const d = +h.get('d'), j = +h.get('j');
  if (V.dallar[d] && j >= 1 && j <= V.dallar[d].L) seçili = {d, j};
}
kartlar(); ağaç(); panel();
if (h.has('k')) yol(+h.get('k'));
</script>
</body>
</html>
"""

