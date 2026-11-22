"""
HDATTAHER MOBILE - Catalogue PDF (style noir & or, comme le site et les factures)

generate_catalogue_pdf(sections, settings, site_url, subtitle='')
  sections : liste de (nom_catégorie, [produits])
  produit  : dict name, brand, price, old_price, discount, etat, stock, from_price (bool),
             url (lien vers la fiche), photo (bytes JPEG/PNG ou None)
"""
import io
import os
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Flowable, Spacer, Table,
                                TableStyle, NextPageTemplate, PageBreak, CondPageBreak)

from invoice_generator import _fonts, _money, IMG_DIR, INK, INK_2, GOLD, GOLD_LIGHT, GOLD_DARK, TEXT, MUTED, LINE

PAGE_W, PAGE_H = A4
MARGIN = 14 * mm
CONTENT_W = PAGE_W - 2 * MARGIN
TOP_BAND = 22 * mm
GAP = 6 * mm
CARD_W = (CONTENT_W - GAP) / 2
CARD_H = 74 * mm
PAPER = colors.HexColor('#FBF8F1')
GREEN = colors.HexColor('#1F9D55')
RED = colors.HexColor('#C53030')

MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août',
        'septembre', 'octobre', 'novembre', 'décembre']


def _today_fr():
    d = date.today()
    return f"{d.day} {MOIS[d.month - 1]} {d.year}"


def _fit(canv, text, font, size, max_w, min_size=6):
    """Réduit la taille du texte pour qu'il tienne dans max_w ; coupe avec « … » si besoin."""
    s = size
    while s > min_size and canv.stringWidth(text, font, s) > max_w:
        s -= 0.5
    if canv.stringWidth(text, font, s) > max_w:
        while text and canv.stringWidth(text + '…', font, s) > max_w:
            text = text[:-1]
        text = text.rstrip() + '…'
    return text, s


def _wrap2(canv, text, font, size, max_w):
    """Coupe un texte en 2 lignes maximum."""
    words, lines, cur = (text or '').split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if canv.stringWidth(t, font, size) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
            if len(lines) == 2:
                break
    if cur and len(lines) < 2:
        lines.append(cur)
    used = ' '.join(lines).split()
    if len(used) < len(words) and lines:
        last = lines[-1]
        while last and canv.stringWidth(last + '…', font, size) > max_w:
            last = last[:-1]
        lines[-1] = last.rstrip() + '…'
    return lines[:2]


def _qr(canv, url, x, y, size):
    w = QrCodeWidget(url, barLevel='M')
    b = w.getBounds()
    bw, bh = b[2] - b[0], b[3] - b[1]
    d = Drawing(size, size, transform=[size / bw, 0, 0, size / bh, 0, 0])
    d.add(w)
    renderPDF.draw(d, canv, x, y)


class ProductCard(Flowable):
    def __init__(self, p, F):
        super().__init__()
        self.p, self.F = p, F

    def wrap(self, *a):
        return CARD_W, CARD_H

    def draw(self):
        c, p, F = self.canv, self.p, self.F
        w, h = CARD_W, CARD_H
        r = 3.2 * mm
        # carte
        c.setFillColor(colors.white)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.7)
        c.roundRect(0, 0, w, h, r, stroke=1, fill=1)
        # zone photo
        ph = 38 * mm
        pad = 3.5 * mm
        c.saveState()
        clip = c.beginPath()
        clip.roundRect(pad, h - pad - ph, w - 2 * pad, ph, 2.4 * mm)
        c.clipPath(clip, stroke=0, fill=0)
        c.setFillColor(colors.HexColor('#F4F1EA'))
        c.rect(pad, h - pad - ph, w - 2 * pad, ph, stroke=0, fill=1)
        if p.get('photo'):
            try:
                img = ImageReader(io.BytesIO(p['photo']))
                iw, ih = img.getSize()
                box_w, box_h = w - 2 * pad - 4 * mm, ph - 4 * mm
                k = min(box_w / iw, box_h / ih)
                dw, dh = iw * k, ih * k
                c.drawImage(img, pad + (w - 2 * pad - dw) / 2, h - pad - ph + (ph - dh) / 2, dw, dh, mask='auto')
            except Exception:
                p['photo'] = None
        if not p.get('photo'):
            c.setFillColor(GOLD)
            c.setFont(F['Serif-Bold'], 22)
            c.drawCentredString(w / 2, h - pad - ph / 2 - 7, 'HM')
        c.restoreState()

        # badges sur la photo
        bx = pad + 2.4 * mm
        by = h - pad - 2.4 * mm - 5 * mm
        disc = int(float(p.get('discount') or 0))
        if disc > 0:
            txt = f"-{disc}%"
            bw = c.stringWidth(txt, F['Sans-Bold'], 7.5) + 4.5 * mm
            c.setFillColor(INK)
            c.roundRect(bx, by, bw, 5 * mm, 2.5 * mm, stroke=0, fill=1)
            c.setFillColor(GOLD_LIGHT)
            c.setFont(F['Sans-Bold'], 7.5)
            c.drawCentredString(bx + bw / 2, by + 1.55 * mm, txt)
            bx += bw + 1.6 * mm
        if (p.get('etat') or 'neuf') != 'neuf':
            txt = 'Occasion'
            bw = c.stringWidth(txt, F['Sans-Bold'], 7) + 4.5 * mm
            c.setFillColor(colors.HexColor('#2563EB'))
            c.roundRect(bx, by, bw, 5 * mm, 2.5 * mm, stroke=0, fill=1)
            c.setFillColor(colors.white)
            c.setFont(F['Sans-Bold'], 7)
            c.drawCentredString(bx + bw / 2, by + 1.6 * mm, txt)
        if int(p.get('stock') or 0) <= 0:
            txt = 'Épuisé'
            bw = c.stringWidth(txt, F['Sans-Bold'], 7) + 4.5 * mm
            ex = w - pad - 2.4 * mm - bw
            c.setFillColor(colors.HexColor('#FDE8E8'))
            c.roundRect(ex, by, bw, 5 * mm, 2.5 * mm, stroke=0, fill=1)
            c.setFillColor(RED)
            c.setFont(F['Sans-Bold'], 7)
            c.drawCentredString(ex + bw / 2, by + 1.6 * mm, txt)

        # textes
        tx = pad + 0.6 * mm
        qr_s = 17 * mm
        text_w = w - 2 * pad - qr_s - 3 * mm
        y = h - pad - ph - 5.2 * mm
        brand = (p.get('brand') or '').upper()
        if brand:
            t, s = _fit(c, brand, F['Sans-Bold'], 6.8, text_w)
            c.setFillColor(GOLD_DARK)
            c.setFont(F['Sans-Bold'], s)
            c.drawString(tx, y, t)
            y -= 4.6 * mm
        c.setFillColor(TEXT)
        lines = _wrap2(c, p.get('name') or '', F['Serif-Bold'], 10.5, text_w)
        c.setFont(F['Serif-Bold'], 10.5)
        for ln in lines:
            c.drawString(tx, y, ln)
            y -= 4.6 * mm
        # prix (en bas)
        py = pad + 4.6 * mm
        old = float(p.get('old_price') or 0)
        price = float(p.get('price') or 0)
        if old > price > 0:
            c.setFillColor(MUTED)
            c.setFont(F['Sans'], 7.6)
            ot = _money(old)
            c.drawString(tx, py + 6.2 * mm, ot)
            ow = c.stringWidth(ot, F['Sans'], 7.6)
            c.setStrokeColor(MUTED)
            c.setLineWidth(0.6)
            c.line(tx, py + 6.2 * mm + 2.4, tx + ow, py + 6.2 * mm + 2.4)
        if p.get('from_price'):
            c.setFillColor(MUTED)
            c.setFont(F['Sans'], 6.8)
            c.drawString(tx, py + (9.6 * mm if old > price > 0 else 6.2 * mm), 'À partir de')
        t, s = _fit(c, _money(price), F['Serif-Bold'], 13.5, text_w)
        c.setFillColor(GOLD_DARK)
        c.setFont(F['Serif-Bold'], s)
        c.drawString(tx, py, t)
        c.setFillColor(MUTED)
        c.setFont(F['Sans'], 6.2)
        c.drawString(tx, pad + 0.6 * mm, 'Scannez ou touchez pour commander')
        # QR code vers la fiche produit
        if p.get('url'):
            qx, qy = w - pad - qr_s, pad
            _qr(c, p['url'], qx, qy, qr_s)
            c.linkURL(p['url'], (0, 0, w, h), relative=1)


class SectionTitle(Flowable):
    def __init__(self, title, count, F):
        super().__init__()
        self.title, self.count, self.F = title, count, F

    def wrap(self, *a):
        return CONTENT_W, 14 * mm

    def draw(self):
        c, F = self.canv, self.F
        c.setFillColor(TEXT)
        c.setFont(F['Serif-Bold'], 17)
        c.drawString(0, 5 * mm, self.title)
        tw = c.stringWidth(self.title, F['Serif-Bold'], 17)
        c.setFillColor(MUTED)
        c.setFont(F['Sans'], 8)
        n = f"{self.count} produit{'s' if self.count > 1 else ''}"
        c.drawString(tw + 4 * mm, 5.6 * mm, n)
        c.setFillColor(GOLD)
        c.rect(0, 1.6 * mm, 18 * mm, 1.1 * mm, stroke=0, fill=1)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.line(19.5 * mm, 2.15 * mm, CONTENT_W, 2.15 * mm)


def generate_catalogue_pdf(sections, settings=None, site_url='https://hdattahermobile.com', subtitle=''):
    F = _fonts()
    settings = settings or {}
    site_name = (settings.get('site_name') or 'HDATTAHER MOBILE').strip()
    whatsapp = (settings.get('whatsapp') or '').strip().lstrip('+')
    location = (settings.get('location') or 'Niger').strip()
    domain = site_url.split('://', 1)[-1].rstrip('/')
    today = _today_fr()
    total = sum(len(ps) for _, ps in sections)
    logo_png = os.path.join(os.path.dirname(IMG_DIR), 'favicon', 'logo-512.png')
    if not os.path.isfile(logo_png):
        logo_png = os.path.join(IMG_DIR, 'logo-hm.png')

    def cover(canv, doc):
        canv.saveState()
        canv.setFillColor(INK)
        canv.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
        canv.setFillColor(colors.Color(0.83, 0.69, 0.22, alpha=0.08))
        canv.circle(PAGE_W * 0.85, PAGE_H * 0.86, 95 * mm, stroke=0, fill=1)
        canv.setFillColor(colors.Color(0.83, 0.69, 0.22, alpha=0.05))
        canv.circle(PAGE_W * 0.1, PAGE_H * 0.12, 70 * mm, stroke=0, fill=1)
        canv.setFillAlpha(1)
        canv.setStrokeAlpha(1)
        # cadre doré
        canv.setStrokeColor(colors.Color(0.83, 0.69, 0.22, alpha=0.55))
        canv.setLineWidth(0.8)
        canv.roundRect(9 * mm, 9 * mm, PAGE_W - 18 * mm, PAGE_H - 18 * mm, 5 * mm, stroke=1, fill=0)
        canv.setStrokeAlpha(1)
        cx = PAGE_W / 2
        ls = 46 * mm
        if os.path.isfile(logo_png):
            canv.saveState()
            clip = canv.beginPath(); clip.roundRect(cx - ls / 2, PAGE_H * 0.60, ls, ls, 9 * mm)
            canv.clipPath(clip, stroke=0, fill=0)
            canv.drawImage(logo_png, cx - ls / 2, PAGE_H * 0.60, ls, ls, mask='auto')
            canv.restoreState()
        words = site_name.upper().split()
        canv.setFillColor(GOLD_LIGHT)
        canv.setFont(F['Serif-Bold'], 34)
        canv.drawCentredString(cx, PAGE_H * 0.60 - 16 * mm, words[0] if words else site_name.upper())
        if len(words) > 1:
            canv.setFillColor(colors.HexColor('#B9B2A0'))
            canv.setFont(F['Sans-Medium'], 11)
            canv.drawCentredString(cx, PAGE_H * 0.60 - 25 * mm, '   '.join(' '.join(words[1:])))
        canv.setFillColor(GOLD)
        canv.rect(cx - 15 * mm, PAGE_H * 0.60 - 33 * mm, 30 * mm, 0.9 * mm, stroke=0, fill=1)
        canv.setFillColor(colors.white)
        canv.setFont(F['Serif-Bold'], 40)
        canv.drawCentredString(cx, PAGE_H * 0.36, 'Catalogue')
        canv.setFillColor(GOLD)
        canv.setFont(F['Serif-Italic'], 14)
        canv.drawCentredString(cx, PAGE_H * 0.36 - 11 * mm, subtitle or 'Smartphones & accessoires')
        canv.setFillColor(colors.HexColor('#A9A39A'))
        canv.setFont(F['Sans'], 10)
        canv.drawCentredString(cx, PAGE_H * 0.36 - 20 * mm, f"Prix du {today}  ·  {total} produit{'s' if total > 1 else ''}")
        # bas de couverture
        qs = 26 * mm
        _qr_white(canv, site_url, cx - qs / 2, 36 * mm, qs)
        canv.setFillColor(colors.HexColor('#D9D3C3'))
        canv.setFont(F['Sans-Medium'], 9.5)
        line = domain + (f"   ·   WhatsApp +{whatsapp}" if whatsapp else '')
        canv.drawCentredString(cx, 26 * mm, line)
        canv.setFillColor(colors.HexColor('#8D877B'))
        canv.setFont(F['Sans'], 8)
        canv.drawCentredString(cx, 20 * mm, f"Livraison partout au Niger  ·  {location}")
        canv.linkURL(site_url, (cx - qs / 2, 36 * mm, cx + qs / 2, 36 * mm + qs), relative=0)
        canv.restoreState()

    def page(canv, doc):
        canv.saveState()
        canv.setFillColor(PAPER)
        canv.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
        top = PAGE_H - TOP_BAND
        canv.setFillColor(INK)
        canv.rect(0, top, PAGE_W, TOP_BAND, stroke=0, fill=1)
        canv.setFillColor(GOLD)
        canv.rect(0, top - 0.9 * mm, PAGE_W, 0.9 * mm, stroke=0, fill=1)
        ls = 11 * mm
        if os.path.isfile(logo_png):
            canv.saveState()
            clip = canv.beginPath(); clip.roundRect(MARGIN, top + (TOP_BAND - ls) / 2, ls, ls, 2.4 * mm)
            canv.clipPath(clip, stroke=0, fill=0)
            canv.drawImage(logo_png, MARGIN, top + (TOP_BAND - ls) / 2, ls, ls, mask='auto')
            canv.restoreState()
        canv.setFillColor(GOLD_LIGHT)
        canv.setFont(F['Serif-Bold'], 13)
        canv.drawString(MARGIN + ls + 3.5 * mm, top + TOP_BAND / 2 - 1.2 * mm, site_name.upper())
        canv.setFillColor(colors.HexColor('#A9A39A'))
        canv.setFont(F['Sans'], 8)
        canv.drawRightString(PAGE_W - MARGIN, top + TOP_BAND / 2 + 1 * mm, 'Catalogue')
        canv.setFillColor(GOLD)
        canv.setFont(F['Sans-Medium'], 7.5)
        canv.drawRightString(PAGE_W - MARGIN, top + TOP_BAND / 2 - 3.2 * mm, f"Prix du {today}")
        # pied
        canv.setStrokeColor(LINE)
        canv.setLineWidth(0.6)
        canv.line(MARGIN, 13 * mm, PAGE_W - MARGIN, 13 * mm)
        canv.setFillColor(MUTED)
        canv.setFont(F['Sans'], 7.4)
        foot = domain + (f"   ·   Commandes WhatsApp : +{whatsapp}" if whatsapp else '')
        canv.drawString(MARGIN, 8.5 * mm, foot)
        canv.drawRightString(PAGE_W - MARGIN, 8.5 * mm, f"Page {doc.page - 1}")
        canv.linkURL(site_url, (MARGIN, 7 * mm, MARGIN + 60 * mm, 12 * mm), relative=0)
        canv.restoreState()

    buf = io.BytesIO()
    doc = BaseDocTemplate(buf, pagesize=A4, title=f"Catalogue {site_name}", author=site_name,
                          subject='Catalogue des produits', leftMargin=MARGIN, rightMargin=MARGIN)
    cover_frame = Frame(0, 0, PAGE_W, PAGE_H, id='cover', leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    body_frame = Frame(MARGIN, 17 * mm, CONTENT_W, PAGE_H - TOP_BAND - 17 * mm - 6 * mm, id='body',
                       leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate('cover', [cover_frame], onPage=cover),
                          PageTemplate('page', [body_frame], onPage=page)])

    story = [NextPageTemplate('page'), PageBreak()]
    if not total:
        story.append(Spacer(1, 30 * mm))
        story.append(SectionTitle('Aucun produit pour le moment', 0, F))
    for si, (title, prods) in enumerate(sections):
        if not prods:
            continue
        story.append(CondPageBreak(14 * mm + CARD_H + 4 * mm))
        story.append(SectionTitle(title, len(prods), F))
        story.append(Spacer(1, 2 * mm))
        for i in range(0, len(prods), 2):
            row = [ProductCard(prods[i], F), '', ProductCard(prods[i + 1], F) if i + 1 < len(prods) else '']
            t = Table([row], colWidths=[CARD_W, GAP, CARD_W], rowHeights=[CARD_H], spaceAfter=GAP)
            t.setStyle(TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                                   ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0)]))
            story.append(t)
        story.append(Spacer(1, 4 * mm))
    story.append(CondPageBreak(70 * mm))
    story.append(ContactCard(F, domain, site_url, whatsapp, location))
    doc.build(story)
    return buf.getvalue()


def _qr_white(canv, url, x, y, size):
    canv.setFillColor(colors.white)
    canv.roundRect(x - 2 * mm, y - 2 * mm, size + 4 * mm, size + 4 * mm, 2.5 * mm, stroke=0, fill=1)
    _qr(canv, url, x, y, size)


class ContactCard(Flowable):
    def __init__(self, F, domain, site_url, whatsapp, location):
        super().__init__()
        self.F, self.domain, self.site_url, self.wa, self.loc = F, domain, site_url, whatsapp, location

    def wrap(self, *a):
        return CONTENT_W, 62 * mm

    def draw(self):
        c, F = self.canv, self.F
        w, h = CONTENT_W, 58 * mm
        c.setFillColor(INK)
        c.roundRect(0, 0, w, h, 4 * mm, stroke=0, fill=1)
        c.saveState()
        clip = c.beginPath(); clip.roundRect(0, 0, w, h, 4 * mm)
        c.clipPath(clip, stroke=0, fill=0)
        c.setFillColor(colors.Color(0.83, 0.69, 0.22, alpha=0.08))
        c.circle(w - 20 * mm, h - 6 * mm, 40 * mm, stroke=0, fill=1)
        c.restoreState()
        c.setFillColor(GOLD_LIGHT)
        c.setFont(F['Serif-Bold'], 18)
        c.drawString(8 * mm, h - 14 * mm, 'Commander, c\'est simple')
        c.setFillColor(colors.HexColor('#D9D3C3'))
        c.setFont(F['Sans'], 9.5)
        lines = ['1.  Scannez ou touchez le produit qui vous plaît.',
                 '2.  Commandez sur le site (sans compte) ou écrivez-nous sur WhatsApp.',
                 '3.  Payez par Amana ou Nita, et recevez votre commande partout au Niger.']
        y = h - 24 * mm
        for ln in lines:
            c.drawString(8 * mm, y, ln)
            y -= 6.2 * mm
        c.setFillColor(GOLD)
        c.setFont(F['Sans-Bold'], 11)
        info = self.domain + (f"   ·   WhatsApp +{self.wa}" if self.wa else '')
        c.drawString(8 * mm, 8 * mm, info)
        qs = 30 * mm
        qx = w - qs - 8 * mm
        target = f"https://wa.me/{self.wa}" if self.wa else self.site_url
        _qr_white(c, target, qx, (h - qs) / 2, qs)
        c.setFillColor(colors.HexColor('#A9A39A'))
        c.setFont(F['Sans'], 6.8)
        c.drawCentredString(qx + qs / 2, (h - qs) / 2 - 5.5 * mm, 'WhatsApp' if self.wa else 'Le site')
        c.linkURL(target, (qx, (h - qs) / 2, qx + qs, (h - qs) / 2 + qs), relative=1)
