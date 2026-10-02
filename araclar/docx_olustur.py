#!/usr/bin/env python3
"""Carya Evreni: metin/ altindaki Markdown dosyalarindan Word (docx) belgeleri uretir.

Kullanim:
    python3 araclar/docx_olustur.py              # belgeler.json'daki tum belgeler -> docx/
    python3 araclar/docx_olustur.py Carya_Tarih  # yalnizca adi eslesen belge(ler)
    python3 araclar/docx_olustur.py --sablon     # araclar/Carya_Sablon.docx (bos sablon)

Tasarim: rehber/YAZIM_STANDARDI.md, bolum 3 (Yeryuzu Tapinagi stili).
Gerekli: python-docx.
"""
import json
import os
import re
import sys

from docx import Document
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.enum.section import WD_SECTION
from docx.shared import Cm
from docx.text.paragraph import Paragraph
from xml.sax.saxutils import escape

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METIN = os.path.join(KOK, "metin")
MANIFEST = os.path.join(KOK, "araclar", "belgeler.json")
SABLON = os.path.join(KOK, "araclar", "Carya_Sablon.docx")

FONT = "Georgia"
KOYU = "5B4A2E"      # H1, kapak cizgisi, tablo basligi
ORTA = "6E5A38"      # H2, H3, ayrac, alt bilgi
ACIK = "C9B681"      # kenarliklar
KREM = "FBF7EC"      # tablo govde dolgusu
SAYFA_GENISLIK = 11909 - 2 * 1440  # A4 - kenar bosluklari (twip)

FONTS_XML = f'<w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:cs="{FONT}" w:eastAsia="{FONT}"/>'


# --------------------------------------------------------------------------
# XML yardimcilari
# --------------------------------------------------------------------------
def rpr_xml(bold=False, italic=False, color=None, size=None):
    x = FONTS_XML
    if bold:
        x += '<w:b w:val="1"/><w:bCs w:val="1"/>'
    if italic:
        x += '<w:i w:val="1"/><w:iCs w:val="1"/>'
    if color:
        x += f'<w:color w:val="{color}"/>'
    if size:
        x += f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
    return f"<w:rPr>{x}</w:rPr>"


def set_ppr(p, inner):
    """Paragrafin pPr'ini verilen icerikle degistirir (sira: standart sema sirasi)."""
    old = p._p.find(qn("w:pPr"))
    if old is not None:
        p._p.remove(old)
    p._p.insert(0, parse_xml(f"<w:pPr {nsdecls('w')}>{inner}</w:pPr>"))


def sp(after=None, before=None, line=276):
    a = f' w:after="{after}"' if after is not None else ""
    b = f' w:before="{before}"' if before is not None else ""
    return f'<w:spacing{b}{a} w:line="{line}" w:lineRule="auto"/>'


def add_run(p, text, bold=False, italic=False, color=None, size=None):
    r = p.add_run(text)
    r._r.insert(0, parse_xml(rpr_xml(bold, italic, color, size).replace("<w:rPr>", f"<w:rPr {nsdecls('w')}>")))
    return r


# --------------------------------------------------------------------------
# Sayfa, stiller, numaralandirma
# --------------------------------------------------------------------------
def style_set(style, ppr, rpr):
    el = style.element
    for tag in ("w:pPr", "w:rPr"):
        for old in el.findall(qn(tag)):
            el.remove(old)
    el.append(parse_xml(f"<w:pPr {nsdecls('w')}>{ppr}</w:pPr>"))
    el.append(parse_xml(rpr_xml_ns(rpr)))


def rpr_xml_ns(inner_rpr):
    return inner_rpr.replace("<w:rPr>", f"<w:rPr {nsdecls('w')}>")


def setup_document(doc):
    # docDefaults: Georgia 11 pt, Turkce
    st = doc.styles.element
    dd = st.find(qn("w:docDefaults"))
    if dd is not None:
        st.remove(dd)
    dd = parse_xml(
        f'<w:docDefaults {nsdecls("w")}><w:rPrDefault><w:rPr>{FONTS_XML}'
        '<w:sz w:val="22"/><w:szCs w:val="22"/><w:lang w:val="tr-TR" w:eastAsia="tr-TR" w:bidi="ar-SA"/>'
        '</w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="0" w:line="276" w:lineRule="auto"/>'
        "</w:pPr></w:pPrDefault></w:docDefaults>"
    )
    st.insert(0, dd)

    style_set(doc.styles["Normal"], '<w:spacing w:after="0" w:line="276" w:lineRule="auto"/>', rpr_xml(size=22))
    style_set(
        doc.styles["Heading 1"],
        '<w:keepNext w:val="1"/><w:keepLines w:val="1"/><w:spacing w:before="360" w:after="200" w:line="240" w:lineRule="auto"/><w:outlineLvl w:val="0"/>',
        rpr_xml(bold=True, color=KOYU, size=32),
    )
    style_set(
        doc.styles["Heading 2"],
        '<w:keepNext w:val="1"/><w:keepLines w:val="1"/><w:spacing w:before="240" w:after="140" w:line="240" w:lineRule="auto"/><w:outlineLvl w:val="1"/>',
        rpr_xml(bold=True, color=ORTA, size=26),
    )
    style_set(
        doc.styles["Heading 3"],
        '<w:keepNext w:val="1"/><w:keepLines w:val="1"/><w:spacing w:before="200" w:after="100" w:line="240" w:lineRule="auto"/><w:outlineLvl w:val="2"/>',
        rpr_xml(bold=True, italic=True, color=ORTA, size=23),
    )
    # baslik stillerinin bagli karakter stilleri (Heading1Char...) tema fontu tasimasin
    for sid in ("Heading1Char", "Heading2Char", "Heading3Char"):
        for s in st.findall(qn("w:style")):
            if s.get(qn("w:styleId")) == sid:
                st.remove(s)
    for name in ("Heading 1", "Heading 2", "Heading 3"):
        el = doc.styles[name].element
        for l in el.findall(qn("w:link")):
            el.remove(l)

    # Liste (madde imi) numaralandirmasi
    numbering = doc.part.numbering_part.element
    absn = parse_xml(
        f'<w:abstractNum {nsdecls("w")} w:abstractNumId="90"><w:multiLevelType w:val="hybridMultilevel"/>'
        '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:lvlJc w:val="left"/>'
        '<w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>'
        f"<w:rPr>{FONTS_XML}</w:rPr></w:lvl></w:abstractNum>"
    )
    first_num = numbering.find(qn("w:num"))
    if first_num is not None:
        first_num.addprevious(absn)
    else:
        numbering.append(absn)
    numbering.append(parse_xml(f'<w:num {nsdecls("w")} w:numId="90"><w:abstractNumId w:val="90"/></w:num>'))

    sec = doc.sections[0]
    sec.page_width, sec.page_height = 11909 * 635, 16834 * 635  # twip -> EMU
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(sec, side, 1440 * 635)
    sec.header_distance = sec.footer_distance = 720 * 635


def add_page_footer(section):
    section.footer.is_linked_to_previous = False
    p = section.footer.paragraphs[0]
    set_ppr(p, '<w:jc w:val="center"/>')
    rp = rpr_xml(color=ORTA, size=18)
    fld = parse_xml(
        f'<w:fldSimple {nsdecls("w")} w:instr=" PAGE "><w:r>{rp}<w:t>1</w:t></w:r></w:fldSimple>'
    )
    p._p.append(fld)


def restart_page_numbers(section):
    sp_ = section._sectPr
    for old in sp_.findall(qn("w:pgNumType")):
        sp_.remove(old)
    sp_.append(parse_xml(f'<w:pgNumType {nsdecls("w")} w:start="1"/>'))


# --------------------------------------------------------------------------
# Markdown -> bloklar
# --------------------------------------------------------------------------
HTML_RE = re.compile(r"<[^>]+>")
IMG_RE = re.compile(r"^!\[([^\]]*)\]\(([^)\s]+)\)\s*$")
RULE_RE = re.compile(r"^\s*(\*\s*\*\s*\*|-\s*-\s*-\s*-*|_\s*_\s*_)\s*$")
HEAD_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


def clean_line(s):
    s = s.rstrip()
    s = re.sub(r"\\+$", "", s).rstrip()
    s = s.replace("<br>", " ").replace("<br/>", " ").replace("<br />", " ")
    s = HTML_RE.sub("", s)
    s = re.sub(r"\\([\\`*_{}\[\]()#+\-.!|>])", r"\1", s)  # kacis isaretleri
    return s


def strip_marks(s):
    return re.sub(r"\*+", "", s).strip()


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def parse_markdown(text, md_path, warn):
    """Donus: [(tur, veri)]; tur: h1,h2,h3,p,li,quote,rule,img,table"""
    blocks = []
    lines = text.replace("﻿", "").replace("\r\n", "\n").split("\n")
    para = []

    def flush():
        if para:
            t = " ".join(x.strip() for x in para).strip()
            if t:
                blocks.append(("p", t))
            para.clear()

    i = 0
    while i < len(lines):
        raw = lines[i]
        ln = clean_line(raw)
        s = ln.strip()
        if raw.strip().startswith("<") and not s:
            i += 1  # yalnizca HTML olan satir (ornegin <img ...>)
            continue
        if not s:
            flush()
            i += 1
            continue
        m = HEAD_RE.match(s)
        if m:
            flush()
            lvl = min(len(m.group(1)), 3)
            title = strip_marks(m.group(2))
            if title:
                blocks.append((f"h{lvl}", title))
            i += 1
            continue
        m = IMG_RE.match(s)
        if m:
            flush()
            blocks.append(("img", (m.group(1), os.path.normpath(os.path.join(os.path.dirname(md_path), m.group(2))))))
            i += 1
            continue
        if RULE_RE.match(s):
            flush()
            blocks.append(("rule", None))
            i += 1
            continue
        if s.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and clean_line(lines[i]).strip().startswith("|"):
                row = clean_line(lines[i]).strip()
                if not TABLE_SEP_RE.match(row):
                    rows.append(split_row(row))
                i += 1
            if rows:
                blocks.append(("table", rows))
            continue
        if s.startswith(">"):
            flush()
            cur = []
            while i < len(lines) and clean_line(lines[i]).strip().startswith(">"):
                q = clean_line(lines[i]).strip().lstrip(">").strip()
                if q:
                    cur.append(q)
                elif cur:
                    blocks.append(("quote", " ".join(cur)))
                    cur = []
                i += 1
            if cur:
                blocks.append(("quote", " ".join(cur)))
            continue
        m = re.match(r"^[-*+]\s+(.*)$", s)
        if m:
            flush()
            item = [m.group(1)]
            i += 1
            # girintili devam satirlari
            while i < len(lines) and lines[i].startswith(("  ", "\t")) and lines[i].strip() and not re.match(r"^\s*[-*+]\s", lines[i]):
                item.append(clean_line(lines[i]).strip())
                i += 1
            blocks.append(("li", " ".join(item)))
            continue
        para.append(ln)
        i += 1
    flush()
    return blocks


# --------------------------------------------------------------------------
# Satir ici bicimler
# --------------------------------------------------------------------------
MARK_RE = re.compile(r"\*{1,3}")


def inline_tokens(text):
    """[(metin, kalin, italik)] - **kalin**, *italik*, ***ikisi***."""
    out = []
    bold = ital = False
    pos = 0
    buf = ""
    for m in MARK_RE.finditer(text):
        n = len(m.group(0))
        before = text[m.start() - 1] if m.start() > 0 else " "
        after = text[m.end()] if m.end() < len(text) else " "
        opening_ok = not after.isspace()
        closing_ok = not before.isspace()
        active = (bold if n == 2 else ital if n == 1 else (bold and ital))
        valid = closing_ok if active else opening_ok
        if n == 3 and not (bold and ital) and (bold or ital):
            # *** ile tek durumu kapatmak: orn. **kalin ***italik***... nadir; literal birak
            valid = False
        if not valid:
            continue
        buf += text[pos:m.start()]
        if buf:
            out.append((buf, bold, ital))
        buf = ""
        pos = m.end()
        if n == 3:
            bold = ital = not (bold and ital)
        elif n == 2:
            bold = not bold
        else:
            ital = not ital
    buf += text[pos:]
    if buf:
        out.append((buf, bold, ital))
    return out


def add_inline(p, text, base_bold=False, base_italic=False, color=None, size=None):
    for t, b, i in inline_tokens(text):
        add_run(p, t, bold=base_bold or b, italic=(base_italic != i) if base_italic else i, color=color, size=size)


# --------------------------------------------------------------------------
# Blok yazicilari
# --------------------------------------------------------------------------
def write_heading(doc, level, text):
    p = doc.add_paragraph(style=f"Heading {level}")
    size, color, bold, ital = {1: (32, KOYU, True, False), 2: (26, ORTA, True, False), 3: (23, ORTA, True, True)}[level]
    sp_ = {1: (360, 200), 2: (240, 140), 3: (200, 100)}[level]
    set_ppr(
        p,
        f'<w:pStyle w:val="Heading{level}"/><w:keepNext w:val="1"/><w:keepLines w:val="1"/>'
        f'<w:spacing w:before="{sp_[0]}" w:after="{sp_[1]}" w:line="240" w:lineRule="auto"/>',
    )
    add_run(p, text, bold=bold, italic=ital, color=color, size=size)


def write_paragraph(doc, text):
    p = doc.add_paragraph()
    set_ppr(p, sp(after=160) + '<w:jc w:val="both"/>')
    add_inline(p, text)


def write_list_item(doc, text):
    p = doc.add_paragraph()
    set_ppr(p, '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="90"/></w:numPr>' + sp(after=80) + '<w:ind w:left="720" w:hanging="360"/>')
    add_inline(p, text)


def write_quote(doc, text):
    p = doc.add_paragraph()
    set_ppr(
        p,
        f'<w:pBdr><w:left w:val="single" w:sz="12" w:space="10" w:color="{ACIK}"/></w:pBdr>'
        + sp(after=120)
        + '<w:ind w:left="720"/><w:jc w:val="both"/>',
    )
    add_inline(p, text, base_italic=True)


def write_rule(doc):
    p = doc.add_paragraph()
    set_ppr(p, '<w:keepNext w:val="1"/>' + sp(before=120, after=200, line=240) + '<w:jc w:val="center"/>')
    add_run(p, "*  *  *", color=ORTA)


def kucult(path, hedef=480):
    """Amblemi Word dosyasini sisirmesin diye 480 px'e kucultur (3 cm icin yeterli)."""
    try:
        from io import BytesIO
        from PIL import Image
        im = Image.open(path)
        if max(im.size) <= hedef:
            return path
        im.thumbnail((hedef, hedef))
        buf = BytesIO()
        im.save(buf, "PNG", optimize=True)
        buf.seek(0)
        return buf
    except Exception:
        return path


def write_image(doc, alt, path, warn):
    if not os.path.isfile(path):
        warn(f"gorsel bulunamadi: {path}")
        return
    p = doc.add_paragraph()
    set_ppr(p, '<w:keepNext w:val="1"/>' + sp(before=60, after=160, line=240) + '<w:jc w:val="center"/>')
    try:
        p.add_run().add_picture(kucult(path), width=Cm(3))
    except Exception as e:  # bozuk gorsel
        warn(f"gorsel eklenemedi ({path}): {e}")
        return
    pic = p._p.xpath(".//wp:docPr")
    if pic:
        pic[0].set("descr", alt)
        pic[0].set("name", alt or "Amblem")


def write_table(doc, rows, warn):
    ncol = max(len(r) for r in rows)
    rows = [r + [""] * (ncol - len(r)) for r in rows]
    # sutun genisligi: iceriğe gore, makul alt/ust sinirla
    weights = []
    for c in range(ncol):
        ml = max(len(strip_marks(r[c])) for r in rows)
        avg = sum(len(strip_marks(r[c])) for r in rows[1:] or rows) / max(1, len(rows[1:] or rows))
        weights.append(max(8.0, min(0.5 * ml + 0.5 * avg, 70.0)) ** 0.9)
    tot = sum(weights)
    # her sutun en uzun kelimesini bolmeden sigdirmali (kelime basina ~160 twip + ic bosluk)
    mins = []
    for c in range(ncol):
        lw = max((len(w) for r in rows for w in strip_marks(r[c]).split()), default=1)
        mins.append(min(lw * 160 + 300, SAYFA_GENISLIK // 2))
    widths = [max(mins[c], int(SAYFA_GENISLIK * weights[c] / tot)) for c in range(ncol)]
    over = sum(widths) - SAYFA_GENISLIK
    while over > 0:
        # fazlayi, asgari genisligin ustundeki en genis sutundan al
        k = max(range(ncol), key=lambda c: widths[c] - mins[c])
        cut = min(over, widths[k] - mins[k])
        if cut <= 0:
            break
        widths[k] -= cut
        over -= cut
    widths[widths.index(max(widths))] += SAYFA_GENISLIK - sum(widths)

    tbl = doc.add_table(rows=len(rows), cols=ncol)
    t = tbl._tbl
    tblPr = t.tblPr
    for ch in list(tblPr):
        tblPr.remove(ch)
    borders = "".join(
        f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="{ACIK}"/>' for s in ("top", "left", "bottom", "right", "insideH", "insideV")
    )
    for x in (
        f'<w:tblW {nsdecls("w")} w:w="{SAYFA_GENISLIK}" w:type="dxa"/>',
        f'<w:tblBorders {nsdecls("w")}>{borders}</w:tblBorders>',
        f'<w:tblLayout {nsdecls("w")} w:type="fixed"/>',
        f'<w:tblCellMar {nsdecls("w")}><w:top w:w="80" w:type="dxa"/><w:left w:w="120" w:type="dxa"/>'
        '<w:bottom w:w="80" w:type="dxa"/><w:right w:w="120" w:type="dxa"/></w:tblCellMar>',
        f'<w:tblLook {nsdecls("w")} w:val="0000"/>',
    ):
        tblPr.append(parse_xml(x))
    grid = t.tblGrid
    for gc, w in zip(grid.findall(qn("w:gridCol")), widths):
        gc.set(qn("w:w"), str(w))

    cell_borders = "".join(
        f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="{ACIK}"/>' for s in ("top", "left", "bottom", "right")
    )
    for ri, row in enumerate(rows):
        tr = tbl.rows[ri]._tr
        trPr = tr.get_or_add_trPr()
        trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")} w:val="1"/>'))
        if ri == 0:
            trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")} w:val="1"/>'))
        for ci, txt in enumerate(row):
            cell = tbl.rows[ri].cells[ci]
            tcPr = cell._tc.get_or_add_tcPr()
            for ch in list(tcPr):
                tcPr.remove(ch)
            fill = KOYU if ri == 0 else KREM
            for x in (
                f'<w:tcW {nsdecls("w")} w:w="{widths[ci]}" w:type="dxa"/>',
                f'<w:tcBorders {nsdecls("w")}>{cell_borders}</w:tcBorders>',
                f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="{fill}"/>',
                f'<w:tcMar {nsdecls("w")}><w:top w:w="80" w:type="dxa"/><w:left w:w="120" w:type="dxa"/>'
                '<w:bottom w:w="80" w:type="dxa"/><w:right w:w="120" w:type="dxa"/></w:tcMar>',
            ):
                tcPr.append(parse_xml(x))
            p = cell.paragraphs[0]
            set_ppr(p, sp(line=264))
            if ri == 0:
                add_run(p, strip_marks(txt), bold=True, color="FFFFFF")
            else:
                add_inline(p, txt)
    # tablodan sonra bosluk
    p = doc.add_paragraph()
    set_ppr(p, sp(after=0, line=240) + '<w:rPr><w:sz w:val="12"/></w:rPr>')


# --------------------------------------------------------------------------
# Kapak
# --------------------------------------------------------------------------
def write_cover(doc, d):
    p = doc.add_paragraph()
    set_ppr(p, sp(before=1200, after=120, line=240) + '<w:jc w:val="center"/>')
    add_run(p, d["baslik"], bold=True, size=52)
    if d.get("altbaslik"):
        p = doc.add_paragraph()
        set_ppr(p, sp(after=80, line=240) + '<w:jc w:val="center"/>')
        add_run(p, d["altbaslik"], italic=True, size=28)
    p = doc.add_paragraph()
    set_ppr(p, f'<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="8" w:color="{KOYU}"/></w:pBdr>' + sp(after=1400, line=240) + '<w:jc w:val="center"/>')
    if d.get("yazar"):
        p = doc.add_paragraph()
        set_ppr(p, sp(after=80, line=240) + '<w:jc w:val="center"/>')
        add_run(p, d["yazar"], italic=True, size=24)
    if d.get("not"):
        p = doc.add_paragraph()
        set_ppr(p, sp(after=0, line=240) + '<w:jc w:val="center"/>')
        add_run(p, d["not"], italic=True)


# --------------------------------------------------------------------------
# Belge
# --------------------------------------------------------------------------
def build_document(d, out_path, warn):
    doc = Document()
    setup_document(doc)
    # python-docx sablonundaki ilk (bos) govdeyi temizle
    cp = doc.core_properties
    cp.title = d["baslik"].title() if d["baslik"].isupper() else d["baslik"]
    cp.author = d.get("yazar") or "Carya Evreni"
    cp.subject = d.get("altbaslik", "")
    cp.language = "tr-TR"
    cp.comments = ""

    write_cover(doc, d)
    body_sec = doc.add_section(WD_SECTION.NEW_PAGE)
    restart_page_numbers(body_sec)
    add_page_footer(body_sec)

    n_blocks = 0
    first_file = True
    for rel in d["metinler"]:
        path = os.path.join(METIN, rel)
        if not os.path.isfile(path):
            warn(f"EKSIK DOSYA, atlandi: metin/{rel}")
            continue
        with open(path, encoding="utf-8") as f:
            blocks = parse_markdown(f.read(), path, lambda m, r=rel: warn(f"{r}: {m}"))
        if not blocks:
            warn(f"bos dosya: metin/{rel}")
        for kind, data in blocks:
            n_blocks += 1
            if kind in ("h1", "h2", "h3"):
                write_heading(doc, int(kind[1]), data)
            elif kind == "p":
                write_paragraph(doc, data)
            elif kind == "li":
                write_list_item(doc, data)
            elif kind == "quote":
                write_quote(doc, data)
            elif kind == "rule":
                write_rule(doc)
            elif kind == "img":
                write_image(doc, data[0], data[1], lambda m, r=rel: warn(f"{r}: {m}"))
            elif kind == "table":
                write_table(doc, data, warn)
    # python-docx'in baslangicta olusturdugu bos ilk paragraf yok; son bos sectPr sorunu yok
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    doc.save(out_path)
    return n_blocks


def build_template():
    doc = Document()
    setup_document(doc)
    doc.core_properties.title = "Carya Sablon"
    doc.core_properties.author = "Carya Evreni"
    doc.core_properties.language = "tr-TR"
    write_heading(doc, 1, "Bolum Basligi")
    write_heading(doc, 2, "Alt Baslik")
    write_heading(doc, 3, "Ucuncu Duzey Baslik")
    write_paragraph(doc, "Govde metni.")
    doc.save(SABLON)
    print(f"Sablon yazildi: {os.path.relpath(SABLON, KOK)}")


def main(argv):
    if "--sablon" in argv:
        build_template()
        return 0
    with open(MANIFEST, encoding="utf-8") as f:
        man = json.load(f)
    out_dir = os.path.join(KOK, man.get("cikti_klasoru", "docx"))
    filt = [a.lower() for a in argv if not a.startswith("--")]
    warnings = []
    for d in man["belgeler"]:
        if filt and not any(a in d["dosya"].lower() for a in filt):
            continue
        local = []

        def warn(m, local=local):
            local.append(m)
            warnings.append(f"{d['dosya']}: {m}")

        out = os.path.join(out_dir, d["dosya"])
        n = build_document(d, out, warn)
        print(f"{d['dosya']}: {n} blok, {len(d['metinler']) - sum('EKSIK' in w for w in local)}/{len(d['metinler'])} dosya")
        for w in local:
            print(f"   UYARI: {w}")
    if warnings:
        print(f"\n{len(warnings)} uyari.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
