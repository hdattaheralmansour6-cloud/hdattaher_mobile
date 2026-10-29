"""
HDATTAHER MOBILE - Génération de factures PDF (design moderne)
"""
import io
import os
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    KeepTogether, Image,
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
IMG_DIR = os.path.join(BASE_DIR, 'static', 'img')
UPLOAD_DIR = os.path.join(BASE_DIR, 'static', 'uploads')

PRIMARY = colors.HexColor('#6C63FF')
PRIMARY_DARK = colors.HexColor('#4B44CC')
PRIMARY_SOFT = colors.HexColor('#EFEDFF')
TEXT = colors.HexColor('#1A1A2E')
MUTED = colors.HexColor('#6B7280')
BORDER = colors.HexColor('#E5E7EB')
ZEBRA = colors.HexColor('#F8F8FC')

PAGE_W, PAGE_H = A4
MARGIN = 16 * mm
CONTENT_W = PAGE_W - 2 * MARGIN

STATUS_LABELS = {
    'en attente': ('En attente', '#B45309', '#FEF3C7'),
    'confirmée': ('Confirmée', '#1D4ED8', '#DBEAFE'),
    'préparation': ('Préparation', '#1D4ED8', '#DBEAFE'),
    'expédiée': ('Expédiée', '#6D28D9', '#EDE9FE'),
    'livrée': ('Livrée', '#047857', '#D1FAE5'),
    'annulée': ('Annulée', '#B91C1C', '#FEE2E2'),
    'pending': ('En attente', '#B45309', '#FEF3C7'),
    'confirmed': ('Confirmée', '#1D4ED8', '#DBEAFE'),
    'processing': ('En préparation', '#1D4ED8', '#DBEAFE'),
    'shipped': ('Expédiée', '#6D28D9', '#EDE9FE'),
    'delivered': ('Livrée', '#047857', '#D1FAE5'),
    'cancelled': ('Annulée', '#B91C1C', '#FEE2E2'),
    'canceled': ('Annulée', '#B91C1C', '#FEE2E2'),
}


def _money(v):
    try:
        return f"{float(v or 0):,.0f}".replace(',', ' ') + ' FCFA'
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


def generate_invoice_pdf(order, items, settings=None):
    """
    Génère la facture PDF d'une commande (bytes).
    - order : dict (order_number, status, total, shipping_*, notes, created_at,
              customer_name, payment_method, ...)
    - items : liste de dicts (product_name, unit_price, quantity, subtotal)
    - settings : dict (site_name, owner_name, whatsapp, location, logo_path)
    """
    settings = settings or {}
    site_name = settings.get('site_name') or 'HDATTAHER MOBILE'
    owner_name = settings.get('owner_name') or ''
    whatsapp = settings.get('whatsapp') or ''
    location = settings.get('location') or ''
    order_number = order.get('order_number', '')
    date_str = str(order.get('created_at') or '')[:10]
    status_key = str(order.get('status') or '').lower()
    st_label, st_fg, st_bg = STATUS_LABELS.get(
        status_key, (order.get('status') or '—', '#374151', '#E5E7EB'))
    method = order.get('payment_method') or ''

    def style(name, **kw):
        base = dict(fontName='Helvetica', fontSize=9.5, leading=13, textColor=TEXT)
        base.update(kw)
        return ParagraphStyle(name, **base)

    s_norm = style('n')
    s_muted = style('m', fontSize=8.5, textColor=MUTED, leading=11)
    s_label = style('l', fontName='Helvetica-Bold', fontSize=7.5, textColor=PRIMARY, leading=10)
    s_right = style('r', alignment=TA_RIGHT)
    s_bold = style('b', fontName='Helvetica-Bold', fontSize=10.5, leading=14)
    s_head = style('h', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.white)
    s_head_r = style('hr', parent=s_head, alignment=TA_RIGHT) if False else style(
        'hr', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.white, alignment=TA_RIGHT)
    s_cell_r = style('cr', alignment=TA_RIGHT)
    s_center = style('c', alignment=TA_CENTER, fontSize=8.5, textColor=MUTED)

    # ── Décor de page (bandeau haut + pied) ──
    def decorate(canv, doc):
        canv.saveState()
        band_h = 44 * mm
        canv.setFillColor(PRIMARY)
        canv.rect(0, PAGE_H - band_h, PAGE_W, band_h, stroke=0, fill=1)
        canv.setFillColor(PRIMARY_DARK)
        canv.circle(PAGE_W - 8 * mm, PAGE_H - 6 * mm, 34 * mm, stroke=0, fill=1)
        canv.setFillColor(PRIMARY)
        canv.rect(0, PAGE_H - band_h, PAGE_W * 0.62, band_h, stroke=0, fill=1)
        canv.setFillColor(colors.HexColor('#8A83FF'))
        canv.rect(0, PAGE_H - band_h - 1.6 * mm, PAGE_W, 1.6 * mm, stroke=0, fill=1)

        # Nom du site + coordonnées
        canv.setFillColor(colors.white)
        canv.setFont('Helvetica-Bold', 19)
        canv.drawString(MARGIN, PAGE_H - 19 * mm, site_name.upper())
        canv.setFont('Helvetica', 8.5)
        coords = [c for c in (location, f"WhatsApp : {whatsapp}" if whatsapp else '') if c]
        y = PAGE_H - 26 * mm
        for line in coords:
            canv.drawString(MARGIN, y, line)
            y -= 4.4 * mm

        # Titre FACTURE à droite
        canv.setFont('Helvetica-Bold', 26)
        canv.drawRightString(PAGE_W - MARGIN, PAGE_H - 19 * mm, 'FACTURE')
        canv.setFont('Helvetica', 10)
        canv.drawRightString(PAGE_W - MARGIN, PAGE_H - 26 * mm, f"N° {order_number}")
        canv.setFont('Helvetica', 8.5)
        canv.drawRightString(PAGE_W - MARGIN, PAGE_H - 31 * mm, f"Date : {date_str}")

        # Pied de page
        canv.setStrokeColor(BORDER)
        canv.setLineWidth(0.6)
        canv.line(MARGIN, 18 * mm, PAGE_W - MARGIN, 18 * mm)
        canv.setFillColor(MUTED)
        canv.setFont('Helvetica', 8)
        canv.drawCentredString(PAGE_W / 2, 12.5 * mm, f"Merci pour votre confiance — {site_name}")
        canv.drawRightString(PAGE_W - MARGIN, 8 * mm, f"Page {doc.page}")
        canv.setFillColor(PRIMARY)
        canv.rect(0, 0, PAGE_W, 3 * mm, stroke=0, fill=1)
        canv.restoreState()

    buffer = io.BytesIO()
    doc = BaseDocTemplate(buffer, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                          topMargin=56 * mm, bottomMargin=24 * mm,
                          title=f"Facture {order_number}", author=site_name)
    frame = Frame(MARGIN, 24 * mm, CONTENT_W, PAGE_H - 56 * mm - 24 * mm,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id='main', frames=[frame], onPage=decorate)])

    story = []

    # ── Cartes : Facturé à / Détails ──
    bill_to = (
        [Paragraph('FACTURÉ À', s_label), Spacer(1, 1.5 * mm),
         Paragraph(f"<b>{_e(order.get('shipping_name'))}</b>", s_bold),
         Paragraph(_e(order.get('shipping_phone')), s_norm),
         Paragraph(_e(order.get('shipping_address')), s_norm)]
    )
    pill = Table([[Paragraph(f"<font color='{st_fg}'><b>{_e(st_label)}</b></font>",
                             style('pill', fontSize=8.5, alignment=TA_CENTER))]],
                 colWidths=[32 * mm], rowHeights=[6.5 * mm])
    pill.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(st_bg)),
        ('ROUNDEDCORNERS', [3.2 * mm] * 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    details = [
        Paragraph('DÉTAILS', style('l2', fontName='Helvetica-Bold', fontSize=7.5,
                                   textColor=PRIMARY, leading=10, alignment=TA_RIGHT)),
        Spacer(1, 1.5 * mm),
        Paragraph(f"Client : <b>{_e(order.get('customer_name'))}</b>", s_right),
        Paragraph(f"Date : {_e(date_str)}", s_right),
        Spacer(1, 1.5 * mm),
    ]
    wrap = Table([['', pill]], colWidths=[(CONTENT_W - 6 * mm) / 2 - 8 * mm - 32 * mm, 32 * mm])
    wrap.setStyle(TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                              ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0)]))
    details.append(wrap)

    gap = 6 * mm
    half = (CONTENT_W - gap) / 2
    cards = Table([[bill_to, '', details]], colWidths=[half, gap, half])
    cards.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), ZEBRA), ('BACKGROUND', (2, 0), (2, 0), ZEBRA),
        ('ROUNDEDCORNERS', [3 * mm] * 4),
        ('BOX', (0, 0), (0, 0), 0.6, BORDER), ('BOX', (2, 0), (2, 0), 0.6, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4 * mm), ('RIGHTPADDING', (0, 0), (-1, -1), 4 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5 * mm), ('BOTTOMPADDING', (0, 0), (-1, -1), 4 * mm),
        ('LEFTPADDING', (1, 0), (1, 0), 0), ('RIGHTPADDING', (1, 0), (1, 0), 0),
    ]))
    story += [cards, Spacer(1, 8 * mm)]

    # ── Articles ──
    data = [[Paragraph('PRODUIT', s_head), Paragraph('PRIX UNIT.', s_head_r),
             Paragraph('QTÉ', s_head_r), Paragraph('SOUS-TOTAL', s_head_r)]]
    for it in items:
        data.append([Paragraph(_e(it.get('product_name')), s_norm),
                     Paragraph(_money(it.get('unit_price')), s_cell_r),
                     Paragraph(_e(it.get('quantity', 0)), s_cell_r),
                     Paragraph(f"<b>{_money(it.get('subtotal'))}</b>", s_cell_r)])
    tbl = Table(data, colWidths=[CONTENT_W - 100 * mm, 34 * mm, 16 * mm, 50 * mm], repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TEXT),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ZEBRA]),
        ('LINEBELOW', (0, 1), (-1, -1), 0.4, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story += [tbl, Spacer(1, 5 * mm)]

    # ── Paiement (gauche) + Total (droite) ──
    pay_cell = []
    if method:
        logo = _logo(os.path.join(IMG_DIR, f"{method.lower()}.png"), 24 * mm, 17 * mm)
        txt = [Paragraph('MODE DE PAIEMENT', s_label), Spacer(1, 1 * mm),
               Paragraph(f"<b>{_e(method)}</b>", s_bold),
               Paragraph('Reçu de transfert fourni', s_muted)]
        if logo:
            pay_box = Table([[logo, txt]], colWidths=[28 * mm, 50 * mm])
            pay_box.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            pay_cell = pay_box
        else:
            pay_cell = txt
    left_w = CONTENT_W - 78 * mm - 6 * mm
    left = Table([[pay_cell]], colWidths=[left_w]) if pay_cell else ''
    if pay_cell:
        left.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.6, BORDER), ('ROUNDEDCORNERS', [3 * mm] * 4),
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('LEFTPADDING', (0, 0), (-1, -1), 4 * mm), ('RIGHTPADDING', (0, 0), (-1, -1), 3 * mm),
            ('TOPPADDING', (0, 0), (-1, -1), 3 * mm), ('BOTTOMPADDING', (0, 0), (-1, -1), 3 * mm),
        ]))

    total = Table([[Paragraph('TOTAL À PAYER', style('tl', fontName='Helvetica-Bold', fontSize=8,
                                                     textColor=colors.HexColor('#DAD7FF'))),
                    ],
                   [Paragraph(_money(order.get('total')), style('tv', fontName='Helvetica-Bold',
                                                                fontSize=16, leading=20,
                                                                textColor=colors.white,
                                                                alignment=TA_RIGHT))]],
                  colWidths=[78 * mm])
    total.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PRIMARY), ('ROUNDEDCORNERS', [3 * mm] * 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5 * mm), ('RIGHTPADDING', (0, 0), (-1, -1), 5 * mm),
        ('TOPPADDING', (0, 0), (0, 0), 3.5 * mm), ('BOTTOMPADDING', (0, 0), (0, 0), 0),
        ('TOPPADDING', (0, 1), (0, 1), 1), ('BOTTOMPADDING', (0, 1), (0, 1), 3.5 * mm),
    ]))
    bottom = Table([[left, '', total]], colWidths=[left_w, 6 * mm, 78 * mm])
    bottom.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(KeepTogether([bottom]))

    if order.get('notes'):
        story += [Spacer(1, 7 * mm),
                  KeepTogether([Paragraph('NOTES', s_label), Spacer(1, 1 * mm),
                                Paragraph(_e(order['notes']), s_norm)])]

    if owner_name:
        story += [Spacer(1, 10 * mm), Paragraph(f"{_e(site_name)} — {_e(owner_name)}", s_center)]

    doc.build(story)
    return buffer.getvalue()
