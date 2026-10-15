#!/usr/bin/env python3
"""Carya Evreni: metin/ altindaki Markdown dosyalarindan tek sayfalik bir wiki sitesi uretir.

Kullanim:
    python3 araclar/site_olustur.py

Cikti (site/ klasoru):
    index.html      tam HTML belgesi (yerelde acmak ya da GitHub Pages icin)
    _artifact.html  ayni sayfanin govdesi (claude.ai Artifact olarak yayinlamak icin)
    img/            armalar, sehir amblemleri ve haritalar

Metin degistiginde bu betigi yeniden calistirmak yeterlidir. Gerekli: Pillow.
"""
import html
import json
import os
import re
import shutil

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METIN = os.path.join(KOK, "metin")
MEDIA = os.path.join(METIN, "gorseller", "media")
CIKTI = os.path.join(KOK, "site")
IMG = os.path.join(CIKTI, "img")

# --------------------------------------------------------------------------
# Icerik haritasi: (grup, [(belge kimligi, baslik, dosya), ...])
# --------------------------------------------------------------------------
GRUPLAR = [
    ("Tarih", "Yaratılıştan imparatorluğun kuruluşuna kadar diyarın çağları.", [
        ("baslangic", "Başlangıç", "tarih/01_baslangic.md"),
        ("ates-savasi", "Ateş Savaşı", "tarih/02_ates_savasi.md"),
        ("4-illet", "4 İllet", "tarih/03_4_illet.md"),
        ("kaos-savasi", "Kaos Savaşı", "tarih/04_kaos_savasi.md"),
        ("horusun-isyani", "Horus’un İsyanı", "tarih/05_horusun_isyani.md"),
        ("arcanin-yukselisi", "Arcan’ın Yükselişi", "tarih/06_arcanin_yukselisi.md"),
        ("imparatorlugun-kurulusu", "İmparatorluğun Kuruluşu", "tarih/08_imparatorlugun_kurulusu.md"),
        ("elf-cuce-savaslari", "Elf-Cüce Savaşları", "tarih/09_elf_cuce_savaslari.md"),
        ("irklarin-yaratilisi", "Irkların Yaratılışı", "tarih/10_irklarin_yaratilisi.md"),
        ("tanrilar-cetveli", "Tanrılar Cetveli", "tarih/07_tanrilar_cetveli.md"),
    ]),
    ("İmparatorluk", "Altı büyükşehir, onlara bağlı kasabalar ve soylu haneler.", [
        ("buyuksehirler", "Büyükşehirler", "imparatorluk/buyuksehirler.md"),
        ("kasabalar", "Kasabalar", "imparatorluk/kasabalar.md"),
        ("soylu-aileler", "Soylu Aileler", "imparatorluk/soylu_aileler.md"),
    ]),
    ("Diğer Diyarlar", "İmparatorluk sınırları dışındaki krallıklar ve şehirler.", [
        ("elf-federasyonu", "Elf Federasyonu", "diger_diyarlar/elf_federasyonu.md"),
        ("cuce-kralligi", "Cüce Krallığı", "diger_diyarlar/cuce_kralligi.md"),
        ("kuzey-kralligi", "Kuzey Krallığı", "diger_diyarlar/kuzey_kralligi.md"),
        ("ozgur-sehirler", "Özgür Şehirler", "diger_diyarlar/ozgur_sehirler.md"),
    ]),
    ("Din", "Tapınağın düzeni ve halkın elinde dolaşan dua kitapları.", [
        ("yeryuzu-tapinagi", "Yeryüzü Tapınağı", "din/yeryuzu_tapinagi.md"),
        ("tiamat-dua-kitabi", "Tiamat’ın Dua Kitabı", "din/tiamat_dua_kitabi.md"),
        ("benton-dua-kitabi", "Rahip Benton’un Dua Kitabı", "din/benton_dua_kitabi.md"),
    ]),
    ("Gruplar", "Diyarın başlıca birlikleri, loncaları ve tarikatları.", [
        ("gruplar", "Gruplar ve Tarikatlar", "gruplar.md"),
    ]),
    ("Edu’nun Kitabı", "Terzi çocuğu Edu’nun kendi ağzından hikâyesi.", [
        ("hikaye-1", "Terzi Çocuğu", "hikaye/kisim1_terzi_cocugu.md"),
        ("hikaye-2", "Kumar Gecesi", "hikaye/kisim2_kumar_gecesi.md"),
        ("hikaye-3", "Goblinler ve Kahramanlar", "hikaye/kisim3_goblinler_ve_kahramanlar.md"),
        ("hikaye-4", "Irklar, Şehirler ve Mahlukler", "hikaye/kisim4_irklar_sehirler_mahluklar.md"),
        ("hikaye-5", "Bilgi Tüccarlığı", "hikaye/kisim5_bilgi_tuccarligi.md"),
    ]),
]
# Sirali okunan gruplar: sayfa sonunda onceki/sonraki baglantisi alir
SIRALI = {"Tarih", "Edu’nun Kitabı"}
# Bu belgelerdeki basliklar madde (otomatik baglanti hedefi) sayilir
MADDE_BELGELERI = {"buyuksehirler", "kasabalar", "soylu-aileler", "elf-federasyonu", "cuce-kralligi",
                   "kuzey-kralligi", "ozgur-sehirler", "gruplar"}
GENEL_BASLIKLAR = {"Genel Yapı", "Kuruluş Hikâyesi"}

TR_ASCII = str.maketrans("çğıöşüâîûÇĞİÖŞÜÂÎÛ’'", "cgiosuaiuCGIOSUAIU  ")


def slug(s):
    s = s.translate(TR_ASCII).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "x"


def esc(s):
    return html.escape(s, quote=True)


# --------------------------------------------------------------------------
# Markdown ayristirici (YAZIM_STANDARDI.md'deki alt kume)
# --------------------------------------------------------------------------
def parse(text):
    """Bloklar: (tur, veri). Turler: h (seviye, metin), p, li, quote, rule, img, table."""
    blocks = []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i].rstrip()
        if not ln.strip():
            i += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if m:
            blocks.append(("h", (len(m.group(1)), m.group(2).strip())))
            i += 1
            continue
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", ln)
        if m:
            blocks.append(("img", (m.group(1), m.group(2))))
            i += 1
            continue
        if ln.strip() in ("* * *", "***", "---"):
            blocks.append(("rule", None))
            i += 1
            continue
        if ln.startswith(">"):
            paras, cur = [], []
            while i < len(lines) and lines[i].startswith(">"):
                t = lines[i][1:].strip()
                if t:
                    cur.append(t)
                elif cur:
                    paras.append(" ".join(cur))
                    cur = []
                i += 1
            if cur:
                paras.append(" ".join(cur))
            blocks.append(("quote", paras))
            continue
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            blocks.append(("table", rows))
            continue
        if re.match(r"^[-*]\s+", ln):
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i]):
                items.append(re.sub(r"^[-*]\s+", "", lines[i]).strip())
                i += 1
            blocks.append(("li", items))
            continue
        cur = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,4}\s|>|\||!\[|[-*]\s)", lines[i]):
            cur.append(lines[i].strip())
            i += 1
        if cur:
            blocks.append(("p", " ".join(cur)))
        else:
            i += 1
    return blocks


def inline(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    return s


def plain(s):
    return re.sub(r"\*+", "", s)


# --------------------------------------------------------------------------
# Belgeleri oku
# --------------------------------------------------------------------------
class Belge:
    def __init__(self, grup, bid, baslik, dosya):
        self.grup, self.id, self.baslik, self.dosya = grup, bid, baslik, dosya
        with open(os.path.join(METIN, dosya), encoding="utf-8") as f:
            blocks = parse(f.read())
        # Dosya tek bir H1 ile basliyorsa o H1 belgenin basligidir; birden cok H1 varsa
        # basliklar bir kademe asagi kaydirilir (H1 -> H2 ...).
        h1 = [b for b in blocks if b[0] == "h" and b[1][0] == 1]
        if blocks and blocks[0][0] == "h" and blocks[0][1][0] == 1 and len(h1) == 1:
            self.ust_baslik = blocks[0][1][1]
            blocks = blocks[1:]
        else:
            self.ust_baslik = None
            if h1:
                blocks = [("h", (b[1][0] + 1, b[1][1])) if b[0] == "h" else b for b in blocks]
        self.blocks = blocks
        self.bolumler = []  # (seviye, baslik, id)
        seen = set()
        for k, d in blocks:
            if k == "h" and d[0] in (2, 3):
                sid = f"{self.id}.{slug(d[1])}"
                n = 2
                while sid in seen:
                    sid = f"{self.id}.{slug(d[1])}-{n}"
                    n += 1
                seen.add(sid)
                self.bolumler.append((d[0], d[1], sid))


BELGELER = []
for grup, aciklama, belgeler in GRUPLAR:
    for bid, baslik, dosya in belgeler:
        BELGELER.append(Belge(grup, bid, baslik, dosya))
BID = {b.id: b for b in BELGELER}


def bolum_id(bid, baslik):
    for lv, t, sid in BID[bid].bolumler:
        if t == baslik:
            return sid
    return None


# --------------------------------------------------------------------------
# Iliskiler: sehirler, haneler, kasabalar, tanrilar
# --------------------------------------------------------------------------
def grup_altlari(bid, sonek):
    """'X Soylu Aileleri' gibi H2'lerin altindaki H3'leri {X: [(baslik, id)]} olarak dondurur."""
    out, cur = {}, None
    for lv, t, sid in BID[bid].bolumler:
        if lv == 2:
            cur = t[: -len(sonek)].strip() if t.endswith(sonek) else None
            if cur:
                out[cur] = []
        elif lv == 3 and cur:
            out[cur].append((t, sid))
    return out


SEHIRLER = [(t, sid) for lv, t, sid in BID["buyuksehirler"].bolumler if lv == 2]
HANELER = grup_altlari("soylu-aileler", "Soylu Aileleri")
KASABALAR = grup_altlari("kasabalar", "Kasabaları")
HANE_SEHIR = {h: s for s, hs in HANELER.items() for h, _ in hs}
KASABA_SEHIR = {k: s for s, ks in KASABALAR.items() for k, _ in ks}

# Gorseller: belge basliklarinin altindaki ![..](..) satirlarindan
GORSEL = {}  # bolum id -> dosya adi
for b in BELGELER:
    cur = None
    for k, d in b.blocks:
        if k == "h" and d[0] in (2, 3):
            cur = bolum_id(b.id, d[1])
        elif k == "img" and cur:
            GORSEL[cur] = os.path.basename(d[1])

TANRILAR = []  # (ad, id)
for k, d in BID["tanrilar-cetveli"].blocks:
    if k == "table":
        for row in d[1:]:
            TANRILAR.append((plain(row[0]), f"tanrilar-cetveli.{slug(row[0])}"))

# --------------------------------------------------------------------------
# Otomatik baglanti sozlugu: ad -> hedef id
# --------------------------------------------------------------------------
HEDEF = {}


def ekle(ad, hedef):
    if ad and ad not in HEDEF and ad not in GENEL_BASLIKLAR:
        HEDEF[ad] = hedef


for t, sid in SEHIRLER:
    ekle(t, sid)
for b in BELGELER:
    if b.id in MADDE_BELGELERI:
        for lv, t, sid in b.bolumler:
            if b.id == "soylu-aileler" and lv == 2:
                continue
            if b.id == "kasabalar" and lv == 2:
                continue
            ekle(t, sid)
for b in BELGELER:
    if b.grup in ("Tarih", "Diğer Diyarlar", "Din", "Gruplar") and b.id not in ("baslangic", "gruplar"):
        ekle(b.baslik, b.id)
ekle("Gözyaşı Şövalyeleri", bolum_id("gruplar", "Gözyaşı Şövalyeleri"))
for ad, tid in TANRILAR:
    ekle(ad, tid)

HARF = "A-Za-z0-9ÇçĞğİıÖöŞşÜüÂâÎîÛû"


def _desen(ad):
    parca = re.escape(ad).replace("’", "[’']").replace("\\'", "[’']").replace("'", "[’']")
    return parca


_adlar = sorted(HEDEF, key=len, reverse=True)
BAGLANTI_RE = re.compile(
    rf"(?<![{HARF}])(" + "|".join(_desen(a) for a in _adlar) + rf")((?:[’'][{HARF}]+)?)(?![{HARF}])"
)
NORM = {a.replace("'", "’"): a for a in _adlar}


def baglantila(html_s, kullanilan, kendi):
    """Metindeki bilinen adlari ilk geciste baglantiya cevirir; etiketlerin icine dokunmaz."""
    parcalar = re.split(r"(<[^>]+>)", html_s)
    out, a_icinde = [], False
    for p in parcalar:
        if p.startswith("<"):
            if p.startswith("<a "):
                a_icinde = True
            elif p == "</a>":
                a_icinde = False
            out.append(p)
            continue
        if a_icinde:
            out.append(p)
            continue

        def rep(m):
            ad = NORM.get(m.group(1).replace("'", "’"), m.group(1))
            hedef = HEDEF.get(ad)
            if not hedef or hedef in kullanilan or hedef in kendi:
                return m.group(0)
            kullanilan.add(hedef)
            return f'<a class="xl" href="#{hedef}">{m.group(0)}</a>'

        out.append(BAGLANTI_RE.sub(rep, p))
    return "".join(out)


# --------------------------------------------------------------------------
# HTML uretimi
# --------------------------------------------------------------------------
def img_src(dosya):
    return f"img/{dosya}"


def bilgi_kutusu(b, baslik, sid):
    """Hane, sehir ve kasaba basliklarinin yanina wiki bilgi kutusu."""
    g = GORSEL.get(sid)
    satirlar = []
    tur = None
    if b.id == "soylu-aileler" and baslik in HANE_SEHIR:
        tur = "Soylu hane"
        s = HANE_SEHIR[baslik]
        satirlar.append(("Şehir", f'<a href="#{bolum_id("buyuksehirler", s)}">{esc(s)}</a>'))
        satirlar.append(("Aynı şehirden", ", ".join(
            f'<a href="#{hid}">{esc(h)}</a>' for h, hid in HANELER[s] if h != baslik)))
    elif b.id == "buyuksehirler":
        tur = "Büyükşehir"
        hs = HANELER.get(baslik, [])
        ks = KASABALAR.get(baslik, [])
        if hs:
            satirlar.append(("Soylu haneler", f"{len(hs)}"))
        if ks:
            satirlar.append(("Kasabalar", ", ".join(
                f'<a href="#{kid}">{esc(k.replace(" Kasabası", ""))}</a>' for k, kid in ks)))
    elif b.id == "kasabalar" and baslik in KASABA_SEHIR:
        tur = "Kasaba"
        s = KASABA_SEHIR[baslik]
        satirlar.append(("Bağlı olduğu şehir", f'<a href="#{bolum_id("buyuksehirler", s)}">{esc(s)}</a>'))
    if not tur:
        return ""
    h = [f'<aside class="infobox" aria-label="{esc(baslik)} bilgi kutusu">']
    h.append(f'<p class="ib-kind">{tur}</p><p class="ib-name">{esc(baslik)}</p>')
    if g:
        alt = f"{baslik} arması" if tur == "Soylu hane" else f"{baslik} amblemi"
        h.append(f'<img class="ib-img" src="{img_src(g)}" alt="{esc(alt)}" width="180" height="180" loading="lazy">')
    if satirlar:
        h.append("<dl>")
        for k, v in satirlar:
            h.append(f"<dt>{k}</dt><dd>{v}</dd>")
        h.append("</dl>")
    h.append("</aside>")
    return "".join(h)


def sehir_haneleri(baslik):
    hs = HANELER.get(baslik, [])
    if not hs:
        return ""
    h = ['<div class="crest-row" role="list">']
    for ad, hid in hs:
        g = GORSEL.get(hid)
        h.append(f'<a role="listitem" class="crest" href="#{hid}">'
                 + (f'<img src="{img_src(g)}" alt="" width="72" height="72" loading="lazy">' if g else "")
                 + f"<span>{esc(ad)}</span></a>")
    h.append("</div>")
    return f'<div class="houses"><p class="label">{esc(baslik)} soylu haneleri</p>{"".join(h)}</div>'


def belge_html(b):
    out = []
    kullanilan = set()
    kendi = {b.id}
    yigin = []  # (seviye, bolum sonuna eklenecek html)
    bolum_sira = iter(b.bolumler)

    def kapat(seviye):
        while yigin and yigin[-1][0] >= seviye:
            out.append(yigin.pop()[1] + "</section>")

    for k, d in b.blocks:
        if k == "h":
            lv, t = d
            if lv in (2, 3):
                _, _, sid = next(bolum_sira)
                kapat(lv)
                out.append(f'<section class="s{lv}" id="{sid}">')
                yigin.append((lv, sehir_haneleri(t) if b.id == "buyuksehirler" and lv == 2 else ""))
                kullanilan = set()
                kendi = {b.id, sid}
                out.append(f'<h{lv}>{inline(t)}<a class="pilcrow" href="#{sid}" aria-label="Bu bölüme bağlantı">§</a></h{lv}>')
                out.append(bilgi_kutusu(b, t, sid))
            else:
                out.append(f"<h4>{inline(t)}</h4>")
        elif k == "img":
            continue  # gorseller bilgi kutusunda
        elif k == "p":
            out.append(f"<p>{baglantila(inline(d), kullanilan, kendi)}</p>")
        elif k == "li":
            out.append("<ul>" + "".join(f"<li>{baglantila(inline(x), kullanilan, kendi)}</li>" for x in d) + "</ul>")
        elif k == "quote":
            out.append("<blockquote>" + "".join(f"<p>{inline(x)}</p>" for x in d) + "</blockquote>")
        elif k == "rule":
            out.append('<p class="rule" aria-hidden="true">✦ ✦ ✦</p>')
        elif k == "table":
            rows = d
            t = ['<div class="table-wrap"><table><thead><tr>']
            t += [f"<th>{inline(c)}</th>" for c in rows[0]]
            t.append("</tr></thead><tbody>")
            for r in rows[1:]:
                rid = f' id="{b.id}.{slug(r[0])}"' if b.id == "tanrilar-cetveli" else ""
                t.append(f"<tr{rid}>" + "".join(
                    f"<td>{inline(c) if j == 0 else baglantila(inline(c), kullanilan, kendi)}</td>"
                    for j, c in enumerate(r)) + "</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t))
    kapat(0)
    return "".join(out)


def toc_html(b):
    if len(b.bolumler) < 2:
        return ""
    items = "".join(
        f'<li class="t{lv}"><a href="#{sid}">{esc(plain(t))}</a></li>' for lv, t, sid in b.bolumler)
    return (f'<details class="toc" data-toc><summary>Bu sayfada</summary>'
            f'<ol>{items}</ol></details>')


def onceki_sonraki(b):
    if b.grup not in SIRALI:
        return ""
    sira = [x for x in BELGELER if x.grup == b.grup]
    i = sira.index(b)
    h = ['<nav class="pager" aria-label="Önceki ve sonraki">']
    if i > 0:
        h.append(f'<a class="prev" href="#{sira[i-1].id}"><span>Önceki</span>{esc(sira[i-1].baslik)}</a>')
    else:
        h.append("<span></span>")
    if i < len(sira) - 1:
        h.append(f'<a class="next" href="#{sira[i+1].id}"><span>Sonraki</span>{esc(sira[i+1].baslik)}</a>')
    h.append("</nav>")
    return "".join(h)


def ilk_cumle(b, n=170):
    for k, d in b.blocks:
        if k == "p":
            t = plain(d)
            m = re.match(r"(.{40,}?[.!?])\s", t + " ")
            t = m.group(1) if m else t
            return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"
    return ""


def kelime(b):
    n = 0
    for k, d in b.blocks:
        if k in ("p",):
            n += len(d.split())
        elif k in ("li", "quote"):
            n += sum(len(x.split()) for x in d)
    return n


def article_html(b):
    sira_no = ""
    if b.grup in SIRALI:
        sira = [x for x in BELGELER if x.grup == b.grup]
        sira_no = f'<span class="eyebrow-n">{sira.index(b) + 1}. bölüm</span>'
    dk = max(1, round(kelime(b) / 200))
    alt = f'<p class="subtitle">{esc(b.ust_baslik)}</p>' if b.ust_baslik and b.ust_baslik != b.baslik else ""
    return (f'<article class="doc" id="{b.id}" data-title="{esc(b.baslik)}" hidden>'
            f'<header class="doc-head"><p class="eyebrow">{esc(b.grup)}{sira_no}</p>'
            f'<h1>{esc(b.baslik)}</h1>{alt}<p class="meta">Yaklaşık {dk} dakikalık okuma</p></header>'
            f'{toc_html(b)}<div class="prose">{belge_html(b)}</div>{onceki_sonraki(b)}</article>')


def nav_html():
    h = ['<nav class="sidenav" id="sidenav" aria-label="Ansiklopedi dizini">',
         '<a class="nav-home" href="#ana-sayfa">Ana sayfa</a>',
         '<a class="nav-home" href="#harita">Harita</a>',
         '<a class="nav-home" href="#armalar">Armalar</a>']
    for grup, _, belgeler in GRUPLAR:
        h.append(f'<p class="nav-group">{esc(grup)}</p><ul>')
        for bid, baslik, _ in belgeler:
            h.append(f'<li><a href="#{bid}">{esc(baslik)}</a></li>')
        h.append("</ul>")
    h.append("</nav>")
    return "".join(h)


def ana_sayfa():
    n_hane = sum(len(v) for v in HANELER.values())
    n_kasaba = sum(len(v) for v in KASABALAR.values())
    n_kelime = sum(kelime(b) for b in BELGELER)
    h = ['<article class="doc home" id="ana-sayfa">']
    h.append('<header class="hero"><div class="hero-text">'
             '<p class="eyebrow">Diyarın ansiklopedisi</p>'
             '<h1 class="wordmark">Carya</h1>'
             '<p class="lede">Tanrıların ilk savaşından Florentina tahtına, altı büyükşehirden kuzeyin buzlu '
             'krallıklarına kadar Carya diyarı hakkında yazılmış her şey burada.</p>'
             '<dl class="facts">'
             f'<div><dt>Büyükşehir</dt><dd>{len(SEHIRLER)}</dd></div>'
             f'<div><dt>Soylu hane</dt><dd>{n_hane}</dd></div>'
             f'<div><dt>Kasaba</dt><dd>{n_kasaba}</dd></div>'
             f'<div><dt>Tanrı</dt><dd>{len(TANRILAR)}</dd></div>'
             '</dl>'
             f'<p class="meta">{len(BELGELER)} madde, yaklaşık {n_kelime // 1000} bin kelime.</p>'
             '</div>'
             '<a class="hero-map" href="#harita" aria-label="Haritayı aç">'
             '<img src="img/carya_haritasi_etiketli.jpg" alt="Carya kıtasının etiketli haritası" width="1414" height="2000">'
             '<span>Haritayı aç</span></a></header>')

    h.append('<section class="home-block"><h2>Altı Büyükşehir</h2><div class="city-grid">')
    for t, sid in SEHIRLER:
        g = GORSEL.get(sid)
        n = len(HANELER.get(t, []))
        k = len(KASABALAR.get(t, []))
        bilgi = f"{n} hane" + (f", {k} kasaba" if k else "")
        h.append(f'<a class="city" href="#{sid}">'
                 + (f'<img src="{img_src(g)}" alt="" width="96" height="96" loading="lazy">' if g else "")
                 + f'<span class="city-name">{esc(t)}</span><span class="city-meta">{bilgi}</span></a>')
    h.append("</div></section>")

    h.append('<section class="home-block"><h2>Bölümler</h2><div class="sections-grid">')
    for grup, aciklama, belgeler in GRUPLAR:
        ilk = belgeler[0][0]
        lst = "".join(f'<li><a href="#{bid}">{esc(bas)}</a></li>' for bid, bas, _ in belgeler[:6])
        more = f'<li class="more">ve {len(belgeler) - 6} madde daha</li>' if len(belgeler) > 6 else ""
        h.append(f'<div class="section-card"><h3><a href="#{ilk}">{esc(grup)}</a></h3>'
                 f'<p>{esc(aciklama)}</p><ul>{lst}{more}</ul></div>')
    h.append("</div></section>")

    h.append('<section class="home-block"><h2>Çağlar</h2><ol class="timeline">')
    for b in BELGELER:
        if b.grup == "Tarih" and b.id != "tanrilar-cetveli":
            h.append(f'<li><a href="#{b.id}">{esc(b.baslik)}</a><p>{esc(ilk_cumle(b))}</p></li>')
    h.append("</ol></section>")
    h.append("</article>")
    return "".join(h)


def armalar_sayfasi():
    h = ['<article class="doc" id="armalar" data-title="Armalar" hidden>',
         '<header class="doc-head"><p class="eyebrow">Hanedanlık armaları</p><h1>Armalar</h1>'
         '<p class="subtitle">Büyükşehirlerin mühürleri ve onlara bağlı soylu hanelerin armaları.</p></header>',
         '<div class="prose wide">']
    for t, sid in SEHIRLER:
        g = GORSEL.get(sid)
        h.append(f'<section class="armory"><div class="armory-head">'
                 + (f'<img src="{img_src(g)}" alt="{esc(t)} amblemi" width="88" height="88" loading="lazy">' if g else "")
                 + f'<div><h2><a href="#{sid}">{esc(t)}</a></h2><p class="meta">{len(HANELER.get(t, []))} soylu hane</p></div></div>'
                 '<div class="armory-grid">')
        for ad, hid in HANELER.get(t, []):
            gg = GORSEL.get(hid)
            h.append(f'<a class="arm" href="#{hid}">'
                     + (f'<img src="{img_src(gg)}" alt="" width="140" height="140" loading="lazy">' if gg else "")
                     + f"<span>{esc(ad)}</span></a>")
        h.append("</div></section>")
    h.append("</div></article>")
    return "".join(h)


def harita_sayfasi():
    return ('<article class="doc" id="harita" data-title="Harita" hidden>'
            '<header class="doc-head"><p class="eyebrow">Atlas</p><h1>Carya Haritası</h1>'
            '<p class="subtitle">Kıtanın şehir adlarıyla işaretlenmiş haritası. Yakınlaştırıp sürükleyerek gezebilirsiniz.</p></header>'
            '<div class="map-tools" role="toolbar" aria-label="Harita araçları">'
            '<div class="seg" role="group" aria-label="Harita türü">'
            '<button type="button" id="map-etiketli" aria-pressed="true">Etiketli</button>'
            '<button type="button" id="map-bos" aria-pressed="false">Etiketsiz</button></div>'
            '<div class="seg" role="group" aria-label="Yakınlaştırma">'
            '<button type="button" id="map-out" aria-label="Uzaklaştır">−</button>'
            '<button type="button" id="map-fit">Sığdır</button>'
            '<button type="button" id="map-in" aria-label="Yakınlaştır">+</button></div></div>'
            '<div class="map-frame" id="map-frame" tabindex="0" aria-label="Harita alanı">'
            '<img id="map-img" src="img/carya_haritasi_etiketli.jpg" alt="Carya kıtasının haritası" width="1414" height="2000"></div>'
            '<p class="meta map-note">Haritadaki bazı adlar metinlerdeki yazımdan farklıdır (örneğin haritada Ventura, '
            'metinde Venture; haritada Cortas, metinde Cortax). Ansiklopedide metindeki yazım kullanılır.</p>'
            '</article>')


def arama_dizini():
    idx = []
    for b in BELGELER:
        idx.append({"id": b.id, "t": b.baslik, "d": b.grup, "x": ""})
        # bolum metinleri
        cur, buf = None, []
        sira = iter(b.bolumler)

        def bitir():
            if cur:
                idx.append({"id": cur[1], "t": plain(cur[0]), "d": b.baslik, "x": " ".join(buf)[:1500]})

        giris = []
        for k, d in b.blocks:
            if k == "h" and d[0] in (2, 3):
                bitir()
                _, t, sid = next(sira)
                cur, buf = (t, sid), []
            elif k == "p":
                (buf if cur else giris).append(plain(d))
            elif k in ("li", "quote"):
                (buf if cur else giris).extend(plain(x) for x in d)
        bitir()
        idx[[i for i, e in enumerate(idx) if e["id"] == b.id][0]]["x"] = " ".join(giris)[:1500]
    for ad, tid in TANRILAR:
        for k, d in BID["tanrilar-cetveli"].blocks:
            if k == "table":
                for r in d[1:]:
                    if plain(r[0]) == ad:
                        idx.append({"id": tid, "t": ad, "d": "Tanrılar Cetveli", "x": plain(r[1])})
    return idx


# --------------------------------------------------------------------------
# Gorselleri kopyala
# --------------------------------------------------------------------------
def gorselleri_kopyala():
    os.makedirs(IMG, exist_ok=True)
    for g in set(GORSEL.values()):
        shutil.copy(os.path.join(MEDIA, g), os.path.join(IMG, g))
    for g in ("carya_haritasi_etiketli.jpg", "carya_haritasi_bos.png"):
        src = os.path.join(KOK, "harita", g)
        dst = os.path.join(IMG, g)
        if g.endswith(".png"):
            from PIL import Image
            Image.open(src).convert("RGB").save(dst[:-4] + ".jpg", quality=82, optimize=True)
        else:
            shutil.copy(src, dst)


SABLON_YOLU = os.path.join(KOK, "araclar", "site_sablon.html")


def main():
    gorselleri_kopyala()
    with open(SABLON_YOLU, encoding="utf-8") as f:
        sablon = f.read()
    govde = (sablon
             .replace("{{NAV}}", nav_html())
             .replace("{{HOME}}", ana_sayfa())
             .replace("{{ARTICLES}}", "".join(article_html(b) for b in BELGELER) + armalar_sayfasi() + harita_sayfasi())
             .replace("{{INDEX}}", json.dumps(arama_dizini(), ensure_ascii=False).replace("</", "<\\/")))
    with open(os.path.join(CIKTI, "_artifact.html"), "w", encoding="utf-8") as f:
        f.write(govde)
    bas, govde_ici = govde.split("</style>", 1)
    tam = ('<!doctype html>\n<html lang="tr">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
           + bas + "</style>\n</head>\n<body>\n" + govde_ici + "\n</body>\n</html>\n")
    with open(os.path.join(CIKTI, "index.html"), "w", encoding="utf-8") as f:
        f.write(tam)
    print(f"site/index.html: {len(BELGELER)} belge, {len(HEDEF)} baglanti hedefi, "
          f"{len(set(GORSEL.values()))} gorsel, {os.path.getsize(os.path.join(CIKTI, 'index.html')) // 1024} KB")


if __name__ == "__main__":
    main()
