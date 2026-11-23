#!/usr/bin/env python3
"""Review My CV v1.0 document builder.

Lays out two Word files from structured JSON written by the model:
  --kind report : the branded "Assessment of Your Original CV" (CARLY design language)
  --kind cv     : the clean, unbranded suggested improved CV

It formats and validates structure only. It does not evaluate candidates or verify facts.
Needs Python 3 and python-docx. matplotlib is optional (adds the scorecard chart).
Usage: --kind fit|report|cv --input data.json [--output file.docx] [--source original.txt]\nDesign primitives are ported from the CARLY(TM) Profile Report builder so both reports match.
(c) Career Agility International Pte Ltd.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import tempfile

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_LINE_SPACING
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Emu, Twips, RGBColor, Inches

PRODUCT = 'Review My CV'
VERSION = 'v1.0'
CONTACT = 'info@CareerAgility.org'
CARLY_LINK = 'https://www.careeragility.org/carly'
CARLY_LINK_TEXT = 'www.careeragility.org/carly'
ACCURACY_NOTICE = ('This AI-assisted CV and assessment are suggestions, not a guarantee of employment; '
                   'you are responsible for checking all facts and claims before using them.')

NAVY, NAVY2, GOLD, DGOLD, SLATE = '0F1B2D', '1C2C44', 'C8A24A', 'A9853A', '5A6779'
CREAM, CREAM2, DIV, LIGHT, WHITE, BARE = 'F7F4EE', 'EFE9DF', 'E4DDD0', 'D4DCEB', 'FFFFFF', 'D9DEE6'
GREEN, RED = '2E7D5B', 'B5483B'
HF, BF = 'Georgia', 'Arial'
W = 9026  # A4 width minus 1" side margins, in twips

AREAS = ['Positioning and value', 'Scope and accountability', 'Achievement evidence',
         'Leadership or specialist contribution', 'Career story and relevance',
         'Clarity and usability', 'Skills language']
RATING_NAME = {1: 'Weak', 2: 'Adequate', 3: 'Strong'}
STATUSES = {
    'Clearly demonstrated': ('●', GREEN),
    'Partly demonstrated': ('●', GOLD),
    'Not demonstrated in supplied material': ('○', SLATE),
    'Confirmed gap': ('●', RED),
}
LABELS = ('Applied in suggested CV', 'Additional evidence needed')
LEVEL = {'match': 'In line with the brief', 'over': 'Above the brief', 'under': 'Below the brief',
         'unclear': 'Not clear from the job description'}
MODULES = {
    'Skills': 'maps your experience to the market-standard skills recruiters search for.',
    'Adjacencies': 'tests which adjacent roles and industries your experience transfers to, and what it takes to cross.',
    'Target Map': 'maps the companies and contacts worth approaching for your target role.',
    'Headhunter Call-list': 'finds the search consultants who cover your field and level.',
    'Daily Alert': 'watches the market each day for roles that match your profile.',
    'Diagnose': 'pinpoints why a job search is stalling and what to fix first.',
}
FIT_COLOUR = {'Strong': '2E7D5B', 'Partial': 'C8A24A', 'Weak': 'B5483B'}
HYGIENE = {'ok': ('✓', GREEN, 'Fine'), 'fix': ('!', DGOLD, 'Fixed in suggestion'),
           'flag': ('✗', RED, 'Your action')}
PLACEHOLDER = re.compile(r'\[[^\]]{1,60}\]|\bTBD\b|\bXX+\b|lorem ipsum', re.I)


def fix_zoom(doc):
    z = doc.settings.element.find(qn('w:zoom'))
    if z is not None and z.get(qn('w:percent')) is None:
        z.set(qn('w:percent'), '100')


def has(x):
    return x not in (None, '', [], {})


def long_date(iso):
    try:
        d = dt.date.fromisoformat(str(iso)[:10])
        return f'{d.day} {d.strftime("%B")} {d.year}'
    except ValueError:
        return str(iso)


def role_fit(reqs):
    """Role fit from the requirement statuses. Desirable items are shown but not scored, unless nothing else is."""
    pts = {'Clearly demonstrated': 1.0, 'Partly demonstrated': 0.5,
           'Not demonstrated in supplied material': 0.0, 'Confirmed gap': 0.0}
    missing = ('Not demonstrated in supplied material', 'Confirmed gap')
    scored = [r for r in reqs if r.get('priority') != 'Desirable'] or reqs
    score = sum(pts[r['status']] for r in scored) / len(scored)
    core = [r for r in reqs if r.get('core') or r.get('priority') == 'Essential']
    n_missing = sum(1 for r in reqs if r['status'] in missing)
    if any(r['status'] in missing for r in core) or n_missing * 2 >= len(reqs) or score < 0.5:
        return 'Weak', (f'{n_missing} of {len(reqs)} requirements are not shown in your CV, including what the role '
                        'treats as core. Better wording cannot close this; only evidence can.')
    if any(r['status'] == 'Partly demonstrated' for r in core) or score < 0.8:
        return 'Partial', ('Your CV shows much of what the role asks for, but at least one core requirement is only '
                           'partly shown. That is where a hiring manager will press.')
    return 'Strong', 'Your CV shows evidence for the core requirements of this role.'


def verdict(ratings):
    vals = [r for r in ratings if isinstance(r, int)]
    weak, strong = vals.count(1), vals.count(3)
    if weak >= 3:
        return 'Needs rework', 'Several core areas need rebuilding before this CV competes.'
    if weak == 0 and strong >= 4:
        return 'Ready to send', 'Your original CV already makes a credible case. The suggestion sharpens it.'
    return 'Needs sharpening', 'The experience is there, but the original CV undersells or obscures it.'


# --------------------------------------------------------------------------------------------
# Shared Word primitives (ported from the CARLY report builder)
# --------------------------------------------------------------------------------------------
class Base:
    def __init__(self):
        self.doc = Document()
        self.body = self.doc.element.body
        for p0 in list(self.body.findall(qn('w:p'))):
            self.body.remove(p0)
        self._numbering_setup()
        self._styles()

    @staticmethod
    def _el(tag, **attrs):
        e = OxmlElement(tag)
        for k, v in attrs.items():
            e.set(qn(k), str(v))
        return e

    def _fonts(self, rpr, font):
        rf = rpr.find(qn('w:rFonts'))
        if rf is None:
            rf = self._el('w:rFonts')
            rpr.insert(0, rf)
        for a in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
            rf.set(qn(a), font)
        for a in ('w:asciiTheme', 'w:hAnsiTheme', 'w:cstheme', 'w:eastAsiaTheme'):
            if rf.get(qn(a)) is not None:
                del rf.attrib[qn(a)]

    def _styles(self):
        n = self.doc.styles['Normal']
        n.font.name = BF
        n.font.size = Pt(10)
        n.font.color.rgb = RGBColor.from_string(NAVY)
        self._fonts(n.element.get_or_add_rPr(), BF)
        n.paragraph_format.space_after = Pt(0)
        h = self.doc.styles['Heading 1']
        h.font.name = HF
        h.font.size = Pt(17)
        h.font.bold = False
        h.font.color.rgb = RGBColor.from_string(NAVY)
        self._fonts(h.element.get_or_add_rPr(), HF)
        h.paragraph_format.space_before = Pt(0)

    def _numbering_setup(self):
        numbering = self.doc.part.numbering_part.element
        self.numbering = numbering
        first_num = numbering.find(qn('w:num'))

        def abstract(aid, fmt, text, color, bold):
            a = self._el('w:abstractNum', **{'w:abstractNumId': aid})
            a.append(self._el('w:multiLevelType', **{'w:val': 'singleLevel'}))
            lvl = self._el('w:lvl', **{'w:ilvl': 0})
            lvl.append(self._el('w:start', **{'w:val': 1}))
            lvl.append(self._el('w:numFmt', **{'w:val': fmt}))
            lvl.append(self._el('w:lvlText', **{'w:val': text}))
            lvl.append(self._el('w:lvlJc', **{'w:val': 'left'}))
            ppr = self._el('w:pPr')
            ppr.append(self._el('w:ind', **{'w:left': 400, 'w:hanging': 280}))
            lvl.append(ppr)
            rpr = self._el('w:rPr')
            if bold:
                rpr.append(self._el('w:b'))
            rpr.append(self._el('w:color', **{'w:val': color}))
            lvl.append(rpr)
            a.append(lvl)
            if first_num is not None:
                first_num.addprevious(a)
            else:
                numbering.append(a)

        abstract(9001, 'bullet', '•', self.bullet_color(), False)
        abstract(9002, 'decimal', '%1.', DGOLD, True)
        self.next_num = 9100
        self.bullet_num = self._new_num(9001)

    def bullet_color(self):
        return GOLD

    def _new_num(self, abstract_id, restart=False):
        nid = self.next_num
        self.next_num += 1
        num = self._el('w:num', **{'w:numId': nid})
        num.append(self._el('w:abstractNumId', **{'w:val': abstract_id}))
        if restart:
            ov = self._el('w:lvlOverride', **{'w:ilvl': 0})
            ov.append(self._el('w:startOverride', **{'w:val': 1}))
            num.append(ov)
        self.numbering.append(num)
        return nid

    def _run(self, para, text, size=20, color=NAVY, bold=False, italics=False, font=BF, spacing=None):
        r = para.add_run(text)
        rpr = r._r.get_or_add_rPr()
        self._fonts(rpr, font)
        r.font.size = Pt(size / 2)
        r.font.color.rgb = RGBColor.from_string(color)
        r.font.bold = bold
        r.font.italic = italics
        if spacing:
            sp = self._el('w:spacing', **{'w:val': spacing})
            # keep CT_RPr child order valid: spacing sits before w:sz
            sz = rpr.find(qn('w:sz'))
            if sz is not None:
                sz.addprevious(sp)
            else:
                rpr.append(sp)
        return r

    def _para(self, container=None, before=None, after=100, line=276, keep_next=False, align=None,
              page_break=False, border_bottom=None, border_top=None, numbering=None, tab_right=None):
        container = container if container is not None else self.doc
        p = container.add_paragraph()
        pf = p.paragraph_format
        if numbering:
            ppr = p._p.get_or_add_pPr()
            numpr = self._el('w:numPr')
            numpr.append(self._el('w:ilvl', **{'w:val': 0}))
            numpr.append(self._el('w:numId', **{'w:val': numbering}))
            ppr.append(numpr)
        if keep_next:
            pf.keep_with_next = True
        if page_break:
            pf.page_break_before = True
        if border_bottom or border_top:
            ppr = p._p.get_or_add_pPr()
            pbdr = self._el('w:pBdr')
            for side, b in (('top', border_top), ('bottom', border_bottom)):
                if b:
                    pbdr.append(self._el(f'w:{side}', **{'w:val': 'single', 'w:sz': b[1], 'w:space': b[2], 'w:color': b[0]}))
            ppr.append(pbdr)
        if tab_right:
            pf.tab_stops.add_tab_stop(Twips(tab_right), WD_TAB_ALIGNMENT.RIGHT)
        if before is not None:
            pf.space_before = Twips(before)
        if after is not None:
            pf.space_after = Twips(after)
        if line:
            pf.line_spacing = line / 240
            pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        if align == 'center':
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        self._fix_ppr_order(p)
        return p

    def _fix_ppr_order(self, p):
        """python-docx and manual appends can disorder w:pPr children; sort to schema order."""
        order = ['pStyle', 'keepNext', 'keepLines', 'pageBreakBefore', 'framePr', 'widowControl', 'numPr',
                 'suppressLineNumbers', 'pBdr', 'shd', 'tabs', 'suppressAutoHyphens', 'kinsoku', 'wordWrap',
                 'overflowPunct', 'topLinePunct', 'autoSpaceDE', 'autoSpaceDN', 'bidi', 'adjustRightInd',
                 'snapToGrid', 'spacing', 'ind', 'contextualSpacing', 'mirrorIndents', 'suppressOverlap', 'jc',
                 'textDirection', 'textAlignment', 'textboxTightWrap', 'outlineLvl', 'divId', 'cnfStyle', 'rPr',
                 'sectPr', 'pPrChange']
        ppr = p._p.pPr
        if ppr is None:
            return
        kids = list(ppr)
        kids.sort(key=lambda e: order.index(e.tag.split('}')[1]) if e.tag.split('}')[1] in order else 99)
        for k in kids:
            ppr.remove(k)
        for k in kids:
            ppr.append(k)

    def p(self, runs, **o):
        para = self._para(o.pop('container', None), **o)
        if isinstance(runs, str):
            runs = [(runs, {})]
        for text, ro in runs:
            if text == '__LINK__':
                self._hyperlink(para, ro['url'], ro['text'], ro.get('size', 19))
            else:
                self._run(para, text, **ro)
        return para

    def _hyperlink(self, para, url, text, size):
        rid = para.part.relate_to(url, RT.HYPERLINK, is_external=True)
        h = self._el('w:hyperlink', **{'r:id': rid})
        r = self._el('w:r')
        rpr = self._el('w:rPr')
        rpr.append(self._el('w:rFonts', **{'w:ascii': BF, 'w:hAnsi': BF, 'w:cs': BF}))
        rpr.append(self._el('w:b'))
        rpr.append(self._el('w:color', **{'w:val': DGOLD}))
        rpr.append(self._el('w:sz', **{'w:val': size}))
        rpr.append(self._el('w:u', **{'w:val': 'single'}))
        r.append(rpr)
        t = self._el('w:t')
        t.text = text
        t.set(qn('xml:space'), 'preserve')
        r.append(t)
        h.append(r)
        para._p.append(h)

    def gap(self, n=160):
        return self._para(after=n, line=None)

    def bullet(self, text, container=None, size=20):
        para = self._para(container, after=60, numbering=self.bullet_num)
        self._run(para, text, size=size)
        return para

    # ---- tables ----
    def _table(self, widths, rows_n, total=W):
        t = self.doc.add_table(rows=rows_n, cols=len(widths))
        t.alignment = WD_TABLE_ALIGNMENT.LEFT
        tblPr = t._tbl.tblPr
        for tag in ('w:tblW', 'w:tblLayout', 'w:tblBorders', 'w:tblInd', 'w:tblLook'):
            old = tblPr.find(qn(tag))
            if old is not None:
                tblPr.remove(old)
        # CT_TblPr order: tblStyle, tblpPr, tblOverlap, bidiVisual, tblStyleRowBandSize, tblStyleColBandSize,
        # tblW, jc, tblCellSpacing, tblInd, tblBorders, shd, tblLayout, tblCellMar, tblLook
        jc = tblPr.find(qn('w:jc'))
        tw = self._el('w:tblW', **{'w:w': total, 'w:type': 'dxa'})
        if jc is not None:
            jc.addprevious(tw)
            anchor = jc
        else:
            tblPr.append(tw)
            anchor = tw
        b = self._el('w:tblBorders')
        for s in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
            b.append(self._el(f'w:{s}', **{'w:val': 'nil'}))
        anchor.addnext(b)
        b.addnext(self._el('w:tblLayout', **{'w:type': 'fixed'}))
        for gc, wv in zip(t._tbl.tblGrid.findall(qn('w:gridCol')), widths):
            gc.set(qn('w:w'), str(wv))
        for row in t.rows:
            for c, wv in zip(row.cells, widths):
                c.width = Twips(wv)
        return t

    def _cell_fmt(self, cell, fill=None, borders=None, margins=(80, 80, 140, 140), valign=None):
        tcPr = cell._tc.get_or_add_tcPr()
        if borders:
            tb = self._el('w:tcBorders')
            for side in ('top', 'left', 'bottom', 'right'):
                bb = borders.get(side)
                if bb is None:
                    tb.append(self._el(f'w:{side}', **{'w:val': 'nil'}))
                else:
                    tb.append(self._el(f'w:{side}', **{'w:val': 'single', 'w:sz': bb[1], 'w:space': 0, 'w:color': bb[0]}))
            tcPr.append(tb)
        if fill:
            tcPr.append(self._el('w:shd', **{'w:val': 'clear', 'w:color': 'auto', 'w:fill': fill}))
        mar = self._el('w:tcMar')
        for side, v in zip(('top', 'left', 'bottom', 'right'), (margins[0], margins[2], margins[1], margins[3])):
            mar.append(self._el(f'w:{side}', **{'w:w': v, 'w:type': 'dxa'}))
        tcPr.append(mar)
        if valign:
            tcPr.append(self._el('w:vAlign', **{'w:val': valign}))

    @staticmethod
    def _row_props(row, header=False):
        trPr = row._tr.get_or_add_trPr()
        trPr.append(OxmlElement('w:cantSplit'))
        if header:
            trPr.append(OxmlElement('w:tblHeader'))

    def _cell_text(self, cell, text, size=18, color=NAVY, bold=False, before=40, after=40, italics=False, font=BF):
        para = cell.paragraphs[0]
        pf = para.paragraph_format
        pf.space_before = Twips(before)
        pf.space_after = Twips(after)
        pf.line_spacing = 1.0
        self._run(para, '' if text is None else str(text), size=size, color=color, bold=bold, italics=italics, font=font)
        return para


# --------------------------------------------------------------------------------------------
# The assessment report
# --------------------------------------------------------------------------------------------
class Report(Base):
    def __init__(self, D, logo):
        super().__init__()
        self.D = D
        self.logo = logo
        self.sec = 0

    # ---- design blocks ----
    def eyebrow(self, text, before=360):
        para = self._para(before=before, after=40, line=None, keep_next=True)
        self._run(para, text.upper(), size=16, bold=True, color=DGOLD, spacing=40)

    def h1(self, text):
        para = self._para(after=160, line=None, keep_next=True, border_bottom=(GOLD, 6, 6))
        para.style = self.doc.styles['Heading 1']
        self._run(para, text, size=34, color=NAVY, font=HF)

    def h3(self, text):
        para = self._para(before=220, after=80, line=None, keep_next=True)
        self._run(para, text, size=23, bold=True, color=NAVY2, font=HF)

    def section(self, title, break_before=True):
        self.sec += 1
        if break_before:
            self._para(after=None, line=None, page_break=True)
        self.eyebrow(f'Section {self.sec}', before=0 if break_before else 360)
        self.h1(title)

    def _box(self, fill, left_color, left_size, margins):
        t = self._table([W], 1)
        row = t.rows[0]
        self._row_props(row)
        cell = row.cells[0]
        self._cell_fmt(cell, fill, {'left': (left_color, left_size)} if left_size else None, margins=margins)
        return cell

    def callout(self, label, value, note=None):
        cell = self._box(NAVY, GOLD, 24, (200, 200, 280, 280))
        p1 = cell.paragraphs[0]
        p1.paragraph_format.space_after = Twips(40)
        self._run(p1, label.upper(), size=16, bold=True, color=GOLD, spacing=40)
        p2 = cell.add_paragraph()
        p2.paragraph_format.space_after = Twips(60 if note else 0)
        self._run(p2, value, size=28, color=WHITE, font=HF)
        if note:
            p3 = cell.add_paragraph()
            self._run(p3, note, size=19, color=LIGHT)
        self.gap(120)

    def note(self, title, text, link=None):
        cell = self._box(CREAM2, GOLD, 18, (160, 160, 240, 240))
        p1 = cell.paragraphs[0]
        p1.paragraph_format.space_after = Twips(60)
        self._run(p1, title, size=21, bold=True, color=NAVY, font=HF)
        items = text if isinstance(text, list) else [text]
        for i, x in enumerate(items):
            pp = cell.add_paragraph()
            pp.paragraph_format.space_after = Twips(80 if i < len(items) - 1 else 0)
            self._run(pp, x, size=19)
        if link:
            pp = cell.add_paragraph()
            pp.paragraph_format.space_before = Twips(80)
            self._hyperlink(pp, link[0], link[1], 19)
        self.gap(120)

    def tiles(self, items, gold_first=False):
        """Cream stat tiles: [(big, small), ...]."""
        n = len(items)
        w = [W // n] * n
        w[-1] = W - sum(w[:-1])
        t = self._table(w, 1)
        row = t.rows[0]
        self._row_props(row)
        white = (WHITE, 24)
        for i, (big, small, *col) in enumerate(items):
            c = row.cells[i]
            self._cell_fmt(c, CREAM, {'left': white, 'right': white, 'top': (GOLD, 12)}, margins=(140, 140, 160, 160))
            p1 = c.paragraphs[0]
            p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p1.paragraph_format.space_after = Twips(20)
            colour = col[0] if col else (GOLD if (gold_first and i == 0) else NAVY)
            self._run(p1, str(big), size=30 if len(str(big)) < 12 else 24, bold=True, color=colour, font=HF)
            p2 = c.add_paragraph()
            p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
            self._run(p2, str(small), size=17, color=SLATE)
        self.gap(160)

    def table(self, headers, rows, widths, cell_fn=None):
        div = (DIV, 4)
        allb = {'top': div, 'bottom': div, 'left': div, 'right': div}
        t = self._table(widths, 1 + len(rows))
        hr = t.rows[0]
        self._row_props(hr, header=True)
        for i, h in enumerate(headers):
            c = hr.cells[i]
            self._cell_fmt(c, NAVY, allb)
            self._cell_text(c, h, size=18, color=WHITE, bold=True)
        for ri, r in enumerate(rows):
            row = t.rows[ri + 1]
            self._row_props(row)
            for i, v in enumerate(r):
                c = row.cells[i]
                self._cell_fmt(c, CREAM if ri % 2 else WHITE, allb)
                if cell_fn and cell_fn(c, i, v):
                    continue
                self._cell_text(c, v, size=18, bold=(i == 0))
        self.gap(160)
        return t

    def facts(self, pairs):
        w = [2600, W - 2600]
        div = (DIV, 4)
        allb = {'top': div, 'bottom': div, 'left': div, 'right': div}
        t = self._table(w, len(pairs))
        for row, (k, v) in zip(t.rows, pairs):
            self._row_props(row)
            self._cell_fmt(row.cells[0], CREAM, allb)
            self._cell_text(row.cells[0], k, size=19, bold=True, color=NAVY2)
            self._cell_fmt(row.cells[1], None, allb)
            self._cell_text(row.cells[1], v, size=19)
        self.gap(160)

    def meter(self, cell, rating):
        para = cell.paragraphs[0]
        pf = para.paragraph_format
        pf.space_before, pf.space_after, pf.line_spacing = Twips(40), Twips(40), 1.0
        if not isinstance(rating, int):
            self._run(para, 'Unassessed', size=17, color=SLATE, italics=True)
            return
        on = GOLD if rating == 3 else NAVY
        for i in range(1, 4):
            self._run(para, '■', size=22, color=on if i <= rating else BARE)
        self._run(para, '  ' + RATING_NAME[rating], size=17, color=NAVY2)

    def mark(self, cell, symbol, colour, text):
        para = cell.paragraphs[0]
        pf = para.paragraph_format
        pf.space_before, pf.space_after, pf.line_spacing = Twips(40), Twips(40), 1.0
        self._run(para, symbol + '  ', size=20, color=colour, bold=True)
        self._run(para, text, size=17, color=NAVY2)

    def chart(self, ratings):
        """Optional radar chart of the seven areas. Skipped quietly if matplotlib is missing."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import math
        except Exception:
            return False
        labels = ['Positioning', 'Scope', 'Achievements', 'Leadership', 'Career story', 'Clarity', 'Skills\nlanguage']
        vals = [r if isinstance(r, int) else 0 for r in ratings]
        n = len(vals)
        ang = [i / n * 2 * math.pi for i in range(n)]
        fig = plt.figure(figsize=(5.6, 3.3), dpi=200)
        ax = fig.add_subplot(111, polar=True)
        ax.set_theta_offset(math.pi / 2)
        ax.set_theta_direction(-1)
        ax.set_ylim(0, 3.15)
        ax.set_yticks([1, 2, 3])
        ax.set_yticklabels(['Weak', 'Adequate', 'Strong'], fontsize=6.5, color='#' + SLATE, family='DejaVu Sans')
        ax.set_rlabel_position(180 / 7)
        ax.set_xticks(ang)
        ax.set_xticklabels(labels, fontsize=8, color='#' + NAVY, family='DejaVu Sans')
        ax.tick_params(axis='x', pad=14)
        ax.grid(color='#' + DIV, linewidth=0.8)
        ax.spines['polar'].set_color('#' + DIV)
        ax.fill(ang + ang[:1], [3] * (n + 1), color='#' + CREAM, zorder=0)
        ax.plot(ang + ang[:1], vals + vals[:1], color='#' + GOLD, linewidth=2, zorder=3)
        ax.fill(ang + ang[:1], vals + vals[:1], color='#' + NAVY, alpha=0.18, zorder=2)
        ax.scatter(ang, vals, s=22, color='#' + NAVY, zorder=4)
        fig.tight_layout()
        path = os.path.join(tempfile.mkdtemp(), 'scorecard.png')
        fig.savefig(path, facecolor='white')
        plt.close(fig)
        para = self._para(after=120, line=None, align='center')
        para.add_run().add_picture(path, width=Inches(3.6))
        return True

    # ---- page furniture ----
    def _page_setup(self):
        s = self.doc.sections[0]
        s.page_width, s.page_height = Twips(11906), Twips(16838)
        s.top_margin, s.bottom_margin = Twips(1800), Twips(1300)
        s.left_margin = s.right_margin = Twips(1440)
        s.header_distance = Twips(600)
        s.footer_distance = Twips(720)
        s.different_first_page_header_footer = True
        year = str(self.D.get('date', ''))[:4] or str(dt.date.today().year)
        footer = f'© {year} Career Agility International Pte Ltd. {PRODUCT} {VERSION}. AI-assisted.  Contact: {CONTACT}'
        who = str(self.D.get('candidate') or '').upper()
        label = f'\t{PRODUCT.upper()}  ·  ASSESSMENT' + (f'  ·  {who}' if who else '')

        def clear(container):
            for pp in list(container.paragraphs):
                pp._p.getparent().remove(pp._p)

        logo_w, logo_h = Emu(240 * 9525), Emu(61 * 9525)
        hdr = s.header
        clear(hdr)
        hp = self._para(hdr, after=None, line=None, border_bottom=(DIV, 4, 6), tab_right=W)
        hp.add_run().add_picture(self.logo, width=logo_w, height=logo_h)
        self._run(hp, label, size=15, color=SLATE, spacing=30)
        fh = s.first_page_header
        clear(fh)
        fp = self._para(fh, after=None, line=None)
        fp.add_run().add_picture(self.logo, width=logo_w, height=logo_h)
        for ftr, numbered in ((s.footer, True), (s.first_page_footer, False)):
            clear(ftr)
            fpar = self._para(ftr, after=None, line=None, border_top=(DIV, 4, 4), tab_right=W)
            self._run(fpar, footer, size=14, color=SLATE)
            if numbered:
                self._run(fpar, '\tPage ', size=14, color=SLATE)
                fld = self._el('w:fldSimple', **{'w:instr': 'PAGE'})
                r = self._el('w:r')
                rpr = self._el('w:rPr')
                rpr.append(self._el('w:rFonts', **{'w:ascii': BF, 'w:hAnsi': BF}))
                rpr.append(self._el('w:color', **{'w:val': SLATE}))
                rpr.append(self._el('w:sz', **{'w:val': 14}))
                r.append(rpr)
                tt = self._el('w:t')
                tt.text = '1'
                r.append(tt)
                fld.append(r)
                fpar._p.append(fld)

    # ---- the report ----
    def build(self, out):
        D = self.D
        ratings_by_area = {r['area']: r for r in D['ratings']}
        ratings = [ratings_by_area[a]['rating'] for a in AREAS]
        v_name, v_note = verdict(ratings)
        reqs = D.get('requirements') or []
        has_target = has(reqs)
        fit_name, fit_note = role_fit(reqs) if has_target else (None, None)
        carly = D['carly_next']

        # ---------- Cover ----------
        cell = self._box(NAVY, None, 0, (600, 600, 480, 480))
        c1 = cell.paragraphs[0]
        c1.paragraph_format.space_after = Twips(80)
        self._run(c1, f'{PRODUCT.upper()}  ·  ASSESSMENT REPORT', size=18, bold=True, color=GOLD, spacing=60)
        c2 = cell.add_paragraph()
        c2.paragraph_format.space_after = Twips(120)
        self._run(c2, D.get('candidate') or 'Your CV Assessment', size=60, color=WHITE, font=HF)
        if has(D.get('subtitle')):
            c3 = cell.add_paragraph()
            c3.paragraph_format.space_after = Twips(360)
            self._run(c3, D['subtitle'], size=28, italics=True, color=LIGHT, font=HF)
        c4 = cell.add_paragraph()
        self._run(c4, f'Assessed {long_date(D.get("date"))}', size=18, color=LIGHT)
        if has(D.get('source')):
            self._run(c4, f'   ·   Source: {D["source"]}', size=18, color=LIGHT)

        self.eyebrow('At a glance')
        evidenced = sum(1 for r in reqs if r['status'] == 'Clearly demonstrated')
        if has_target:
            glance = [(v_name, 'Writing verdict', GOLD),
                      (fit_name, 'Role fit', FIT_COLOUR[fit_name]),
                      (f'{evidenced} of {len(reqs)}', 'Requirements clearly evidenced')]
        else:
            glance = [(v_name, 'Writing verdict', GOLD),
                      (f'{ratings.count(3)} of 7', 'Areas rated strong'),
                      ('Not assessed', 'Role fit: no job description supplied', SLATE)]
        self.tiles(glance)

        self.eyebrow('The 30-second read', before=200)
        s = D['summary']
        self.facts([("What's strong", s['strong']), ('What changed', s['changed']),
                    ('What still needs evidence', s['needs_evidence'])])
        self.note('Your CV, read through the eyes of the person who decides',
                  ['Most CV tools write from the candidate’s side, to make you sound good. This assessment reads your CV '
                   'the way a hiring manager or C-suite headhunter does: what they notice first, what makes them doubt you, and '
                   'what gets you shortlisted.',
                   'The method draws on more than 50 years of combined C-suite headhunting and career coaching, and tens of '
                   'thousands of CVs reviewed, by Adrian Choo and Sze-Yen Chee. This report is AI-assisted: it applies their '
                   'method, and they have not personally reviewed it.'])

        # ---------- 1. Hiring manager read ----------
        hm = D['hiring_manager_read']
        self.section('Here Is How a Hiring Manager Reads Your CV')
        self.callout('In the first 30 seconds', hm['first_impression'])
        self.h3('What makes them hesitate')
        for x in hm['hesitations']:
            self.bullet(x)
        self.h3('What gets you shortlisted')
        self.p(hm['shortlist_case'], after=120)
        if has(hm.get('interview_probe')):
            self.gap(80)
            self.note('What an interviewer will probe', hm['interview_probe'])

        # ---------- 2. Scorecard ----------
        self.section('Here Is How Your Original CV Scores')
        self.callout('Verdict on the writing', v_name,
                     v_note + ' This rates the document, not you or your chances.'
                     + (' Fit for the target role is assessed separately in the next section.' if has_target else ''))
        self.chart(ratings)
        rows = [[a, ratings_by_area[a]['rating'], ratings_by_area[a]['evidence'] + '  Fix: ' + ratings_by_area[a]['fix']]
                for a in AREAS]

        def rating_cell(c, i, v):
            if i == 1:
                self.meter(c, v)
                return True
            return False
        self.table(['Area', 'Rating', 'What we saw in your original CV, and the fix'], rows,
                   [2150, 1700, 5176], rating_cell)

        # ---------- 3. Target fit (only when a target was supplied) ----------
        if has_target:
            self.section('Here Is How You Match the Role')
            if has(D.get('target')):
                self.p([('Target: ', {'bold': True, 'color': DGOLD}), (D['target'], {})], after=140)
            self.callout('Role fit', fit_name, fit_note)
            lc = D['level_check']
            self.note(f'Level check: {LEVEL[lc["result"]]}',
                      [f'The role asks for: {lc["brief"]}', f'Your CV shows: {lc["cv"]}', lc['note']])
            rows = [[r['requirement'] + (' (core)' if r.get('core') else ''), r.get('priority', 'Stated'), r['status'],
                     r['evidence'], r['action']] for r in reqs]

            def status_cell(c, i, v):
                if i == 2:
                    sym, col = STATUSES[v]
                    self.mark(c, sym, col, v)
                    return True
                return False
            self.table(['Requirement', 'Priority', 'Evidence status', 'Where it shows in your CV', 'Next action'], rows,
                       [1950, 1250, 1900, 2126, 1800], status_cell)
            kws = D.get('keywords') or []
            if kws:
                self.h3('Key terms from the job description')
                before = sum(1 for k in kws if k['original'])
                after = sum(1 for k in kws if k['suggested'])
                self.p(f'{before} of {len(kws)} key terms appeared in your original CV; {after} of {len(kws)} appear in the '
                       'suggested CV, added only where your own experience supports them.', after=120, keep_next=True)
                kept = [k['term'] for k in kws if k['original']]
                added = [f"{k['term']} ({k['note'].rstrip('.')})" if has(k.get('note')) else k['term']
                         for k in kws if k['suggested'] and not k['original']]
                left = [k['term'] for k in kws if not k['suggested']]
                pairs = []
                if kept: pairs.append(('\u2713  Already in your CV', ', '.join(kept)))
                if added: pairs.append(('+  Added, with evidence', '; '.join(added)))
                if left: pairs.append(('\u2013  Not added: no evidence', ', '.join(left)))
                self.facts(pairs)

        # ---------- Health check ----------
        self.section('Here Is Your CV Health Check', break_before=False)
        self.p('Basic checks a hiring manager or recruiter makes before reading properly. '
               'Items marked ✗ need your action in Word.', after=140, keep_next=True)

        def hy_cell(c, i, v):
            if i == 1:
                sym, col, txt = HYGIENE[v]
                self.mark(c, sym, col, txt)
                return True
            return False
        self.table(['Check', 'Result', 'Detail'], [[h['check'], h['result'], h['note']] for h in D['hygiene']],
                   [2600, 2000, 4426], hy_cell)

        # ---------- Changes ----------
        self.section('Here Is What We Changed, and Why')
        if not has_target:
            self.p([('No job description supplied: ', {'bold': True, 'color': DGOLD}),
                    ('your CV was improved against general best practice for experienced professionals. Run Review My CV '
                     'again with a job description to see how you match a specific role.', {})], after=140)
        nid = self._new_num(9002, restart=True)
        for ch in D['changes']:
            para = self._para(after=80, numbering=nid)
            colour = GREEN if ch['label'] == LABELS[0] else DGOLD
            self._run(para, ch['label'] + ':  ', size=19, bold=True, color=colour)
            self._run(para, ch['text'], size=20)
        if has(D.get('before_after')):
            self.h3('Before and after')
            self.table(['Your original CV', 'Suggested CV', 'Why it reads better'],
                       [[x['before'], x['after'], x['why']] for x in D['before_after']],
                       [3000, 3326, 2700], lambda c, i, v: (self._cell_text(c, v, size=18, italics=(i == 0),
                                                                            color=SLATE if i == 0 else NAVY), True)[1])
        if has(D.get('not_inflated')):
            self.note('What we refused to inflate, and why', D['not_inflated'])
        if has(D.get('layout_notes')):
            self.note('How we read your file', D['layout_notes'])

        # ---------- Skills language and the CARLY next step ----------
        sk = ratings_by_area['Skills language']
        self.section('Here Is the Skills Language Recruiters Search For')
        self.p('Recruiters and applicant tracking systems search for specific, named capabilities. Most CVs describe '
               'the work in job titles, tools or in-house language instead, so strong candidates never surface.',
               after=140, keep_next=True)
        t = self._table([2600, W - 2600], 1)
        self._row_props(t.rows[0])
        box = {'top': (DIV, 4), 'bottom': (DIV, 4), 'left': (DIV, 4), 'right': (DIV, 4)}
        self._cell_fmt(t.rows[0].cells[0], CREAM, box)
        self._cell_text(t.rows[0].cells[0], 'Your original CV', size=19, bold=True, color=NAVY2)
        self._cell_fmt(t.rows[0].cells[1], None, box)
        self.meter(t.rows[0].cells[1], sk['rating'])
        self._run(t.rows[0].cells[1].paragraphs[0], '   ' + sk['evidence'], size=18)
        self.gap(160)
        self.h3('A sample of what your experience already supports')
        self.table(['Skill, in recruiter language', 'Your evidence'],
                   [[x['skill'], x['evidence']] for x in D['skills_teaser']], [3000, W - 3000])
        self.p([('Optional next step: ', {'bold': True, 'color': DGOLD}),
                (f'CARLY\u2122 {carly["module"]}, from Career Agility International, '
                 f'{MODULES[carly["module"]]} {carly["why"]} ', {}),
                ('__LINK__', {'url': D.get('carly_link') or CARLY_LINK, 'text': D.get('carly_link_text') or CARLY_LINK_TEXT})],
               before=160, after=120)

        # ---------- Next steps and notes ----------
        self.eyebrow('Your next steps', before=200)
        for x in ['Open your suggested improved CV in Word and check every date, number, title and claim.',
                  'Add any evidence marked “Additional evidence needed”, if you have it. Wording cannot create experience you do not have.',
                  'Fix any health-check items marked ✗.']:
            self.bullet(x, size=19)
        self.eyebrow('Important notes', before=200)
        for x in [ACCURACY_NOTICE,
                  'AI-assisted assessment using the Career Agility International method. Ratings describe the original '
                  'supplied CV, not hiring probabilities. Evidence statuses describe what your CV shows: '
                  '“Not demonstrated in supplied material” means we could not see it, not that you lack it.',
                  f'Questions about this report? Contact: {CONTACT}']:
            self.p([(x, {'size': 16, 'color': SLATE})], after=80)

        self._page_setup()
        fix_zoom(self.doc)
        cp = self.doc.core_properties
        cp.author = 'Career Agility International'
        cp.title = f'Assessment of Your Original CV' + (f' - {D["candidate"]}' if D.get('candidate') else '')
        cp.subject = f'{PRODUCT} {VERSION}'
        cp.comments = ''
        self.doc.save(out)


# --------------------------------------------------------------------------------------------
# The suggested improved CV (clean, unbranded)
# --------------------------------------------------------------------------------------------
class CV(Base):
    CW = 11906 - 2 * 1080  # A4 width minus 0.75" margins

    def bullet_color(self):
        return NAVY

    def __init__(self, D):
        super().__init__()
        self.D = D

    def heading(self, text):
        para = self._para(before=220, after=80, line=None, keep_next=True, border_bottom=(DIV, 6, 4))
        self._run(para, text.upper(), size=19, bold=True, color=NAVY, spacing=30)

    def role(self, r, compact=False):
        para = self._para(before=40 if compact else 140, after=20, line=None, keep_next=True, tab_right=self.CW)
        self._run(para, r['title'], size=20 if compact else 21, bold=True)
        emp = ', '.join(x for x in [r.get('employer'), r.get('location')] if has(x))
        if emp:
            self._run(para, '  |  ' + emp, size=20, color=NAVY2)
        if has(r.get('dates')):
            self._run(para, '\t' + r['dates'], size=19, color=SLATE)
        if has(r.get('scope')):
            self.p([(r['scope'], {'size': 19, 'italics': True, 'color': SLATE})], after=60, line=264)
        for b in r.get('bullets') or []:
            para = self._para(after=40, line=264, numbering=self.bullet_num)
            self._run(para, b, size=20)

    def build(self, out):
        D = self.D
        s = self.doc.sections[0]
        s.page_width, s.page_height = Twips(11906), Twips(16838)
        s.top_margin = s.bottom_margin = Twips(1000)
        s.left_margin = s.right_margin = Twips(1080)
        self.p([(D['name'], {'size': 44, 'font': HF})], after=40, line=None)
        if has(D.get('headline')):
            self.p([(D['headline'], {'size': 22, 'color': NAVY2, 'bold': True})], after=60, line=None)
        if has(D.get('contact')):
            self.p([('  |  '.join(D['contact']), {'size': 18, 'color': SLATE})], after=120, line=None)
        if has(D.get('profile')):
            self.heading('Profile')
            for para in (D['profile'] if isinstance(D['profile'], list) else [D['profile']]):
                self.p([(para, {'size': 20})], after=80, line=270)
        if has(D.get('key_skills')):
            self.heading('Key skills')
            self.p([('  ·  '.join(D['key_skills']), {'size': 20})], after=60, line=270)
        if has(D.get('experience')):
            self.heading('Professional experience')
            for r in D['experience']:
                self.role(r)
        if has(D.get('earlier_career')):
            self.heading('Earlier career')
            for r in D['earlier_career']:
                self.role(r, compact=not has(r.get('bullets')))
        for key, title in (('education', 'Education'), ('certifications', 'Professional qualifications')):
            if has(D.get(key)):
                self.heading(title)
                for x in D[key]:
                    self.p([(x, {'size': 20})], after=40, line=264)
        for sec in D.get('other_sections') or []:
            if has(sec.get('items')):
                self.heading(sec['heading'])
                for x in sec['items']:
                    para = self._para(after=40, line=264, numbering=self.bullet_num)
                    self._run(para, x, size=20)
        # footer page number only, no branding
        for pp in list(s.footer.paragraphs):
            pp._p.getparent().remove(pp._p)
        fpar = self._para(s.footer, after=None, line=None, align='center')
        fld = self._el('w:fldSimple', **{'w:instr': 'PAGE'})
        r = self._el('w:r')
        rpr = self._el('w:rPr')
        rpr.append(self._el('w:color', **{'w:val': SLATE}))
        rpr.append(self._el('w:sz', **{'w:val': 16}))
        r.append(rpr)
        tt = self._el('w:t')
        tt.text = '1'
        r.append(tt)
        fld.append(r)
        fpar._p.append(fld)
        fix_zoom(self.doc)
        cp = self.doc.core_properties
        cp.author = D['name'] if not D.get('name_is_heading') else ''
        cp.title = f'{D["name"]} CV'
        cp.comments = ''
        cp.last_modified_by = ''
        self.doc.save(out)


# --------------------------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------------------------
def all_text(x):
    if isinstance(x, dict):
        return ' '.join(all_text(v) for v in x.values())
    if isinstance(x, list):
        return ' '.join(all_text(v) for v in x)
    return str(x) if isinstance(x, str) else ''


def validate_report(D):
    errs = []
    for k in ('date', 'summary', 'hiring_manager_read', 'ratings', 'changes', 'hygiene', 'skills_teaser'):
        if not has(D.get(k)):
            errs.append(f'missing {k}')
    if errs:
        return errs
    areas = [r.get('area') for r in D['ratings']]
    if sorted(areas) != sorted(AREAS):
        errs.append(f'ratings must cover exactly these 7 areas: {AREAS}')
    for r in D['ratings']:
        if r.get('rating') not in (1, 2, 3, 'unassessed'):
            errs.append(f'bad rating for {r.get("area")}: use 1, 2, 3 or "unassessed"')
    for k in ('strong', 'changed', 'needs_evidence'):
        if not has(D['summary'].get(k)):
            errs.append(f'summary.{k} missing')
    for k in ('first_impression', 'hesitations', 'shortlist_case'):
        if not has(D['hiring_manager_read'].get(k)):
            errs.append(f'hiring_manager_read.{k} missing')
    for r in D.get('requirements') or []:
        if r.get('status') not in STATUSES:
            errs.append(f'bad status "{r.get("status")}"; use one of {list(STATUSES)}')
    if not 1 <= len(D['changes']) <= 5:
        errs.append('changes: 1 to 5 priorities')
    for c in D['changes']:
        if c.get('label') not in LABELS:
            errs.append(f'change label must be one of {LABELS}')
    if len(D.get('before_after') or []) > 3:
        errs.append('before_after: at most 3')
    if not 3 <= len(D['skills_teaser']) <= 4:
        errs.append('skills_teaser: 3 or 4 skills only (the full set is CARLY™’s job)')
    for h in D['hygiene']:
        if h.get('result') not in HYGIENE:
            errs.append(f'hygiene result must be one of {list(HYGIENE)}')
    if sum(1 for c in D['changes'] if c.get('label') == LABELS[1]) > 3:
        errs.append('changes: at most 3 "Additional evidence needed" items; keep the decisive ones')
    cn = D.get('carly_next') or {}
    if cn.get('module') not in MODULES or not has(cn.get('why')):
        errs.append(f'carly_next needs a "module" (one of {list(MODULES)}) and a one-sentence "why" tied to the biggest gap')
    reqs = D.get('requirements') or []
    if len(reqs) > 8:
        errs.append('requirements: at most 8; merge minor ones and keep what decides the hire')
    if reqs:
        for r in reqs:
            if r.get('priority', 'Stated') not in ('Essential', 'Desirable', 'Stated'):
                errs.append('requirement priority must be Essential, Desirable or Stated')
        if not any(r.get('core') or r.get('priority') == 'Essential' for r in reqs):
            errs.append('mark the role\'s core requirements with "core": true (what the job is fundamentally hiring for)')
        lc = D.get('level_check') or {}
        if lc.get('result') not in LEVEL or not all(has(lc.get(k)) for k in ('brief', 'cv', 'note')):
            errs.append(f'level_check needs brief, cv, note and result (one of {list(LEVEL)}) when a target is supplied')
        if not errs and role_fit(reqs)[0] == 'Weak' and 'weak match for this role' not in D['hiring_manager_read']['first_impression']:
            errs.append('role fit is Weak: first_impression must start "Well written, but a weak match for this role: '
                        'X of Y requirements are not shown in your CV." (adjust "Well written" if the writing verdict is not good)')
    m = PLACEHOLDER.search(all_text(D))
    if m:
        errs.append(f'placeholder text found: "{m.group(0)}"')
    return errs


def _norm(t):
    t = t.lower().replace('\u2019', "'").replace('\u2018', "'").replace('\u201c', '"').replace('\u201d', '"')
    t = re.sub(r'[\u2010-\u2015-]', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()


def check_quotes(D, source_text):
    """Every before_after 'before' marked as a quote must appear word for word in the original CV."""
    src = _norm(source_text)
    errs = []
    for x in D.get('before_after') or []:
        if x.get('quote', True) is False:
            continue
        for frag in re.split(r'\.\.\.|\u2026', x['before']):
            f = _norm(frag).strip(' .,;:')
            if len(f) >= 12 and f not in src:
                errs.append(f'before_after quote not found in the original CV: "{frag.strip()[:70]}". Quote it exactly, '
                            'or set "quote": false for a structural change')
    return errs


def validate_cv(D):
    errs = []
    if not has(D.get('name')):
        errs.append('name missing: use the candidate’s supplied name, or a source-supported professional '
                    'heading with "name_is_heading": true. Never invent a name.')
    if not has(D.get('experience')):
        errs.append('experience missing')
    text = all_text(D)
    m = PLACEHOLDER.search(text)
    if m:
        errs.append(f'placeholder text found in CV: "{m.group(0)}"')
    if re.search(r'career agility|carly|evaluate my cv|review my cv', text, re.I):
        errs.append('the CV must not mention Career Agility International, CARLY™ or this tool')
    for r in (D.get('experience') or []) + (D.get('earlier_career') or []):
        if not has(r.get('title')):
            errs.append('every role needs its official title')
    return errs


def cv_words(D):
    return len(all_text(D).split())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--kind', choices=['report', 'cv', 'fit'], required=True,
                    help='fit: print the role fit computed from report.json requirements, then stop')
    ap.add_argument('--input', required=True)
    ap.add_argument('--output')
    ap.add_argument('--source', help='plain text of the original CV; checks before_after quotes word for word')
    a = ap.parse_args()
    with open(a.input, encoding='utf-8') as f:
        D = json.load(f)
    if a.kind == 'fit':
        reqs = D.get('requirements') or []
        if not reqs:
            print('No requirements: role fit not assessed.')
        else:
            name, note = role_fit(reqs)
            miss = sum(1 for r in reqs if r['status'] in ('Not demonstrated in supplied material', 'Confirmed gap'))
            print(f'Role fit: {name} ({miss} of {len(reqs)} requirements not shown). {note}')
        return
    if not a.output:
        ap.error('--output is required for report and cv')
    errs = validate_report(D) if a.kind == 'report' else validate_cv(D)
    if a.kind == 'report' and a.source:
        with open(a.source, encoding='utf-8') as f:
            errs += check_quotes(D, f.read())
    if errs:
        print('NOT BUILT. Fix these and rerun:\n- ' + '\n- '.join(errs), file=sys.stderr)
        sys.exit(2)
    os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
    if a.kind == 'report':
        logo = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'cai-logo.png')
        Report(D, logo).build(a.output)
    else:
        CV(D).build(a.output)
        n = cv_words(D)
        if n > 1150:
            print(f'WARNING: about {n} words, likely over 3 pages. Compress older roles and repetition, then rebuild.')
        elif n > 850:
            print(f'Note: about {n} words, likely 2 to 3 pages.')
    print(f'Saved {a.output}')


if __name__ == '__main__':
    main()
