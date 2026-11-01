"""
HDATTAHER MOBILE - Factures PDF (style noir & or, comme le site)
"""
import io
import os
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    KeepTogether, Image, Flowable,
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
IMG_DIR = os.path.join(BASE_DIR, 'static', 'img')
FONT_DIR = os.path.join(BASE_DIR, 'static', 'fonts', 'pdf')

# ── Couleurs du site ──
INK = colors.HexColor('#0B0B0D')        # noir du site
INK_2 = colors.HexColor('#16161A')
GOLD = colors.HexColor('#D4AF37')
GOLD_LIGHT = colors.HexColor('#F1D88A')
GOLD_DARK = colors.HexColor('#A67C2E')
CREAM = colors.HexColor('#FBF7EC')
TEXT = colors.HexColor('#1C1C21')
MUTED = colors.HexColor('#6E6A60')
LINE = colors.HexColor('#E9E2CF')

PAGE_W, PAGE_H = A4
MARGIN = 16 * mm
CONTENT_W = PAGE_W - 2 * MARGIN
HEADER_H = 48 * mm

STATUS_LABELS = {
    'en attente': ('En attente', '#B45309', '#FEF3C7'),
    'confirmée': ('Confirmée', '#1D4ED8', '#DBEAFE'),
    'préparation': ('En préparation', '#1D4ED8', '#DBEAFE'),
    'expédiée': ('Expédiée', '#6D28D9', '#EDE9FE'),
    'livrée': ('Livrée', '#047857', '#D1FAE5'),
    'annulée': ('Annulée', '#B91C1C', '#FEE2E2'),
}
PAID = ('confirmée', 'préparation', 'expédiée', 'livrée')


# ── Polices (Lora pour les titres, Poppins pour le texte) ──
def _fonts():
    files = {
        'Serif-Bold': 'Lora-Bold.ttf', 'Serif': 'Lora-Medium.ttf', 'Serif-Italic': 'Lora-MediumItalic.ttf',
        'Sans': 'Poppins-Regular.ttf', 'Sans-Medium': 'Poppins-Medium.ttf', 'Sans-Bold': 'Poppins-Bold.ttf',
    }
    fallback = {
        'Serif-Bold': 'Times-Bold', 'Serif': 'Times-Roman', 'Serif-Italic': 'Times-Italic',
        'Sans': 'Helvetica', 'Sans-Medium': 'Helvetica', 'Sans-Bold': 'Helvetica-Bold',
    }
    names = {}
    for key, fname in files.items():
        reg = 'HM-' + key
        try:
            if reg not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(reg, os.path.join(FONT_DIR, fname)))
            names[key] = reg
        except Exception:
            names[key] = fallback[key]
    return names


def _money(v):
    try:
        return f"{float(v or 0):,.0f}".replace(',', ' ') + ' FCFA'
    except (TypeError, ValueError):
        return f"{v} FCFA"


def _e(v):
    return escape(str(v if v is not None else ''))


def _logo(path, max_w, max_h):
    """Image proportionnelle, ou None si le fichier est absent/illisible."""
    try:
        if not path or not os.path.isfile(path):
            return None
        from reportlab.lib.utils import ImageReader
        iw, ih = ImageReader(path).getSize()
        ratio = min(max_w / iw, max_h / ih)
        return Image(path, width=iw * ratio, height=ih * ratio)
    except Exception:
        return None


def _date_fr(raw):
    raw = str(raw or '')[:10]
    mois = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août',
            'septembre', 'octobre', 'novembre', 'décembre']
    try:
        y, m, d = raw.split('-')
        return f"{int(d)} {mois[int(m) - 1]} {y}"
    except Exception:
        return raw


class _Rule(Flowable):
    """Fine ligne dorée."""
    def __init__(self, width, color=GOLD, thickness=0.8):
        super().__init__()
        self.width, self.color, self.thickness = width, color, thickness

    def wrap(self, *a):
        return self.width, self.thickness

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)


class _Stamp(Flowable):
    """Tampon « PAYÉE » / « ANNULÉE » légèrement incliné."""
    def __init__(self, text, color, font):
        super().__init__()
        self.text, self.color, self.font = text, color, font

    def wrap(self, *a):
        return 46 * mm, 20 * mm

    def draw(self):
        c, col = self.canv, self.color
        c.saveState()
        c.translate(23 * mm, 10 * mm)
        c.rotate(-10)
        c.setStrokeColor(col)
        c.setFillColor(colors.Color(col.red, col.green, col.blue, alpha=0.06))
        c.setLineWidth(1.6)
        c.roundRect(-21 * mm, -6.5 * mm, 42 * mm, 13 * mm, 2.5 * mm, stroke=1, fill=1)
        c.setLineWidth(0.5)
        c.roundRect(-19.8 * mm, -5.3 * mm, 39.6 * mm, 10.6 * mm, 1.8 * mm, stroke=1, fill=0)
        c.setFillColor(col)
        c.setFont(self.font, 13)
        c.drawCentredString(0, -2.2 * mm, self.text)
        c.restoreState()


def generate_invoice_pdf(order, items, settings=None):
    """
    Génère la facture PDF d'une commande (bytes).
    - order : dict (order_number, status, total, shipping_*, notes, created_at,
              customer_name, payment_method, delivery_zone, delivery_fee ...)
    - items : liste de dicts (product_name, unit_price, quantity, subtotal)
    - settings : dict (site_name, owner_name, whatsapp, location)
    """
    F = _fonts()
    settings = settings or {}
    site_name = (settings.get('site_name') or 'HDATTAHER MOBILE').strip()
    owner_name = settings.get('owner_name') or ''
    whatsapp = (settings.get('whatsapp') or '').strip()
    location = (settings.get('location') or '').strip()
    site_url = 'hdattahermobile.com'
    order_number = order.get('order_number', '')
    date_str = _date_fr(order.get('created_at'))
    status_key = str(order.get('status') or '').lower()
    st_label, st_fg, st_bg = STATUS_LABELS.get(status_key, (order.get('status') or '—', '#374151', '#E5E7EB'))
    method = (order.get('payment_method') or '').replace('Amanata', 'Amana')
    fee = float(order.get('delivery_fee') or 0) if order.get('delivery_zone') else 0
    items_total = sum(float(it.get('subtotal') or 0) for it in items)

    def st(name, **kw):
        base = dict(fontName=F['Sans'], fontSize=9, leading=13, textColor=TEXT)
        base.update(kw)
        return ParagraphStyle(name, **base)

    s_norm = st('n')
    s_small = st('s', fontSize=7.8, leading=10.5, textColor=MUTED)
    s_label = st('l', fontName=F['Sans-Bold'], fontSize=6.8, leading=9, textColor=GOLD_DARK)
    s_name = st('nm', fontName=F['Serif-Bold'], fontSize=11.5, leading=15)
    s_r = st('r', alignment=TA_RIGHT)
    s_rb = st('rb', alignment=TA_RIGHT, fontName=F['Sans-Medium'])
    s_head = st('h', fontName=F['Sans-Bold'], fontSize=7, leading=9, textColor=GOLD_DARK)
    s_head_r = st('hr', fontName=F['Sans-Bold'], fontSize=7, leading=9, textColor=GOLD_DARK, alignment=TA_RIGHT)
    s_head_c = st('hc', fontName=F['Sans-Bold'], fontSize=7, leading=9, textColor=GOLD_DARK, alignment=TA_CENTER)
    s_c = st('c', alignment=TA_CENTER)
    s_prod = st('p', fontName=F['Sans-Medium'], fontSize=9.2, leading=12.5)

    # ── Décor de chaque page : bandeau noir, filet doré, pied de page ──
    def decorate(canv, doc):
        canv.saveState()
        top = PAGE_H - HEADER_H
        canv.setFillColor(INK)
        canv.rect(0, top, PAGE_W, HEADER_H, stroke=0, fill=1)
        # léger halo doré (limité au bandeau)
        canv.saveState()
        clip = canv.beginPath(); clip.rect(0, top, PAGE_W, HEADER_H)
        canv.clipPath(clip, stroke=0, fill=0)
        canv.setFillColor(colors.Color(0.83, 0.69, 0.22, alpha=0.07))
        canv.circle(PAGE_W - 30 * mm, PAGE_H - 6 * mm, 46 * mm, stroke=0, fill=1)
        canv.setFillColor(colors.Color(0.83, 0.69, 0.22, alpha=0.05))
        canv.circle(PAGE_W - 6 * mm, top + 4 * mm, 26 * mm, stroke=0, fill=1)
        canv.restoreState()
        # filet doré
        canv.setFillColor(GOLD)
        canv.rect(0, top - 1.2 * mm, PAGE_W, 1.2 * mm, stroke=0, fill=1)
        canv.setFillColor(GOLD_DARK)
        canv.rect(PAGE_W * 0.66, top - 1.2 * mm, PAGE_W * 0.34, 1.2 * mm, stroke=0, fill=1)

        # Monogramme HM
        bx, by, bs = MARGIN, PAGE_H - 13 * mm - 15 * mm, 15 * mm
        logo_png = os.path.join(IMG_DIR, 'logo-hm.png')
        if os.path.isfile(logo_png):
            canv.drawImage(logo_png, bx, by, bs, bs, mask='auto')
        else:
            canv.setStrokeColor(GOLD)
            canv.setLineWidth(1.1)
            canv.setFillColor(INK_2)
            canv.roundRect(bx, by, bs, bs, 3.6 * mm, stroke=1, fill=1)
            canv.setFillColor(GOLD)
            canv.setFont(F['Serif-Bold'], 15)
            canv.drawCentredString(bx + bs / 2, by + bs / 2 - 5.2, 'HM')

        # Nom de la boutique
        words = site_name.upper().split()
        tx = bx + bs + 5 * mm
        canv.setFillColor(GOLD_LIGHT)
        canv.setFont(F['Serif-Bold'], 17)
        canv.drawString(tx, by + bs - 6.6 * mm, words[0] if words else site_name.upper())
        if len(words) > 1:
            canv.setFillColor(colors.HexColor('#B9B2A0'))
            canv.setFont(F['Sans-Medium'], 7)
            canv.drawString(tx + 0.4 * mm, by + 2.2 * mm, '  '.join(' '.join(words[1:])))

        # Coordonnées
        coords = [c for c in (location, (f"WhatsApp  +{whatsapp.lstrip('+')}" if whatsapp else ''), site_url) if c]
        canv.setFillColor(colors.HexColor('#A9A39A'))
        canv.setFont(F['Sans'], 7.6)
        canv.drawString(MARGIN, top + 9 * mm, '   ·   '.join(coords))

        # FACTURE + numéro
        canv.setFillColor(colors.white)
        canv.setFont(F['Serif-Bold'], 26)
        canv.drawRightString(PAGE_W - MARGIN, PAGE_H - 22 * mm, 'Facture')
        canv.setFillColor(GOLD)
        canv.setFont(F['Sans-Medium'], 9)
        canv.drawRightString(PAGE_W - MARGIN, PAGE_H - 29 * mm, f"N° {order_number}")
        canv.setFillColor(colors.HexColor('#A9A39A'))
        canv.setFont(F['Sans'], 7.8)
        canv.drawRightString(PAGE_W - MARGIN, top + 9 * mm, date_str)

        # Pied de page
        canv.setStrokeColor(LINE)
        canv.setLineWidth(0.6)
        canv.line(MARGIN, 17 * mm, PAGE_W - MARGIN, 17 * mm)
        canv.setFillColor(GOLD_DARK)
        canv.setFont(F['Serif-Italic'], 9)
        canv.drawString(MARGIN, 11.5 * mm, 'Merci pour votre confiance.')
        canv.setFillColor(MUTED)
        canv.setFont(F['Sans'], 7.2)
        canv.drawRightString(PAGE_W - MARGIN, 11.5 * mm, f"{site_name}  ·  {site_url}  ·  page {doc.page}")
        canv.setFillColor(INK)
        canv.rect(0, 0, PAGE_W, 3.2 * mm, stroke=0, fill=1)
        canv.setFillColor(GOLD)
        canv.rect(0, 3.2 * mm, PAGE_W, 0.6 * mm, stroke=0, fill=1)

        canv.restoreState()

    buffer = io.BytesIO()
    top_margin = HEADER_H + 10 * mm
    doc = BaseDocTemplate(buffer, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                          topMargin=top_margin, bottomMargin=24 * mm,
                          title=f"Facture {order_number}", author=site_name)
    frame = Frame(MARGIN, 24 * mm, CONTENT_W, PAGE_H - top_margin - 24 * mm,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id='main', frames=[frame], onPage=decorate)])

    story = []

    # ── Facturé à / Livraison / Commande ──
    pill = Table([[Paragraph(f"<font color='{st_fg}'>{_e(st_label)}</font>",
                             st('pill', fontName=F['Sans-Bold'], fontSize=7.4, leading=9, alignment=TA_CENTER))]],
                 colWidths=[27 * mm], rowHeights=[5.6 * mm])
    pill.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(st_bg)), ('ROUNDEDCORNERS', [2.8 * mm] * 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    customer = order.get('shipping_name') or order.get('customer_name') or 'Client'
    col_a = [Paragraph('FACTURÉ À', s_label), Spacer(1, 2 * mm),
             Paragraph(_e(customer), s_name), Spacer(1, 0.8 * mm),
             Paragraph(_e(order.get('shipping_phone')), s_norm)]
    if order.get('customer_name') and order.get('customer_name') != customer:
        col_a.append(Paragraph(f"Compte : {_e(order.get('customer_name'))}", s_small))
    col_b = [Paragraph('LIVRAISON', s_label), Spacer(1, 2 * mm),
             Paragraph(_e(order.get('shipping_address') or '—'), s_norm)]
    if order.get('delivery_zone'):
        col_b += [Spacer(1, 0.8 * mm), Paragraph(f"Zone : <font name='{F['Sans-Medium']}'>{_e(order.get('delivery_zone'))}</font>", s_small)]
    col_c = [Paragraph('COMMANDE', s_label), Spacer(1, 2 * mm),
             Paragraph(f"<font name='{F['Sans-Medium']}'>N° {_e(order_number)}</font>", s_norm),
             Paragraph(_e(date_str), s_small), Spacer(1, 1.6 * mm), pill]
    w3 = (CONTENT_W - 2 * 6 * mm) / 3
    info = Table([[col_a, '', col_b, '', col_c]], colWidths=[w3, 6 * mm, w3, 6 * mm, w3])
    info.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEABOVE', (0, 0), (0, 0), 1.2, GOLD), ('LINEABOVE', (2, 0), (2, 0), 1.2, GOLD), ('LINEABOVE', (4, 0), (4, 0), 1.2, GOLD),
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 3 * mm), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story += [info, Spacer(1, 10 * mm)]

    # ── Articles ──
    data = [[Paragraph('ARTICLE', s_head), Paragraph('PRIX UNITAIRE', s_head_r),
             Paragraph('QTÉ', s_head_c), Paragraph('MONTANT', s_head_r)]]
    for it in items:
        name = str(it.get('product_name') or '')
        detail = ''
        if ' — ' in name:
            name, detail = name.split(' — ', 1)
        if name.endswith(' (occasion)'):
            name, detail = name[:-11], (detail + ' · occasion' if detail else 'Occasion')
        elif detail.endswith(' (occasion)'):
            detail = detail[:-11] + ' · occasion'
        cell = [Paragraph(_e(name), s_prod)]
        if detail:
            cell.append(Paragraph(_e(detail), s_small))
        data.append([cell, Paragraph(_money(it.get('unit_price')), s_r),
                     Paragraph(_e(it.get('quantity', 0)), s_c),
                     Paragraph(_money(it.get('subtotal')), s_rb)])
    widths = [CONTENT_W - 36 * mm - 16 * mm - 38 * mm, 36 * mm, 16 * mm, 38 * mm]
    tbl = Table(data, colWidths=widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), CREAM),
        ('LINEBELOW', (0, 0), (-1, 0), 0.9, GOLD),
        ('LINEBELOW', (0, 1), (-1, -1), 0.4, LINE),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, 0), 7), ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
        ('TOPPADDING', (0, 1), (-1, -1), 8), ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story += [tbl, Spacer(1, 7 * mm)]

    # ── Paiement (gauche) + Totaux (droite) ──
    left_w = CONTENT_W - 80 * mm - 8 * mm
    pay_parts = []
    if method:
        logo = _logo(os.path.join(IMG_DIR, f"{method.lower()}.png"), 20 * mm, 13 * mm)
        txt = [Paragraph('PAIEMENT', s_label), Spacer(1, 1.2 * mm),
               Paragraph(_e(method), st('pm', fontName=F['Serif-Bold'], fontSize=11.5, leading=14)),
               Paragraph('Transfert mobile · reçu fourni', s_small)]
        if logo:
            box = Table([[logo, txt]], colWidths=[24 * mm, left_w - 24 * mm - 8 * mm])
            box.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                     ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                                     ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0)]))
            pay_parts.append(box)
        else:
            pay_parts += txt
    if order.get('notes'):
        pay_parts += [Spacer(1, 4 * mm), Paragraph('NOTE DU CLIENT', s_label), Spacer(1, 1 * mm),
                      Paragraph(_e(order['notes']), s_small)]
    left = ''
    if pay_parts:
        left = Table([[pay_parts]], colWidths=[left_w])
        left.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.6, LINE), ('ROUNDEDCORNERS', [2.5 * mm] * 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 4 * mm), ('RIGHTPADDING', (0, 0), (-1, -1), 4 * mm),
            ('TOPPADDING', (0, 0), (-1, -1), 3.5 * mm), ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5 * mm),
        ]))

    rows = [[Paragraph('Sous-total', s_norm), Paragraph(_money(items_total), s_r)]]
    if order.get('delivery_zone'):
        rows.append([[Paragraph('Livraison', s_norm), Paragraph(_e(order.get('delivery_zone')), s_small)],
                     Paragraph(_money(fee) if fee else 'Gratuite', s_r)])
    sums = Table(rows, colWidths=[44 * mm, 36 * mm])
    sums.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 0.4, LINE), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4 * mm), ('RIGHTPADDING', (0, 0), (-1, -1), 4 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    total = Table([[Paragraph('TOTAL', st('tl', fontName=F['Sans-Bold'], fontSize=7.5, leading=10, textColor=GOLD_LIGHT)),
                    Paragraph(_money(order.get('total')), st('tv', fontName=F['Serif-Bold'], fontSize=16.5, leading=20,
                                                            textColor=GOLD, alignment=TA_RIGHT))]],
                  colWidths=[22 * mm, 58 * mm])
    total.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), INK), ('ROUNDEDCORNERS', [2.5 * mm] * 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4 * mm), ('RIGHTPADDING', (0, 0), (-1, -1), 4 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), 3.6 * mm), ('BOTTOMPADDING', (0, 0), (-1, -1), 3.8 * mm),
    ]))
    right = [sums, Spacer(1, 2.5 * mm), total]
    if status_key in PAID or status_key == 'annulée':
        stamp_col = colors.HexColor('#1F9D55') if status_key in PAID else colors.HexColor('#C53030')
        stamp = Table([[_Stamp('PAYÉE' if status_key in PAID else 'ANNULÉE', stamp_col, F['Sans-Bold'])]], colWidths=[80 * mm])
        stamp.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('TOPPADDING', (0, 0), (-1, -1), 4 * mm),
                                   ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0)]))
        right.append(stamp)
    bottom = Table([[left, '', right]], colWidths=[left_w, 8 * mm, 80 * mm])
    bottom.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(KeepTogether([bottom]))

    # ── Mentions ──
    story += [Spacer(1, 12 * mm), _Rule(CONTENT_W, LINE, 0.5), Spacer(1, 3 * mm)]
    sign = f"{_e(site_name)}" + (f" — {_e(owner_name)}" if owner_name else '')
    story.append(Paragraph(
        f"<font name='{F['Sans-Medium']}' color='#1C1C21'>{sign}</font><br/>"
        "Produits vérifiés avant envoi. Pour toute question sur cette facture, écrivez-nous sur WhatsApp "
        "en indiquant le numéro de commande.", st('foot', fontSize=7.6, leading=11, textColor=MUTED, alignment=TA_LEFT)))

    doc.build(story)
    return buffer.getvalue()
