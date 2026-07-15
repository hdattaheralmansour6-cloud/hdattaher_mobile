"""
HDATTAHER MOBILE - Génération de factures PDF (Phase 4)
"""
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

PRIMARY_COLOR = colors.HexColor('#6C63FF')
TEXT_COLOR = colors.HexColor('#1A1A2E')
MUTED_COLOR = colors.HexColor('#6B7280')
BORDER_COLOR = colors.HexColor('#E5E7EB')


def generate_invoice_pdf(order, items, settings=None):
    """
    Génère la facture PDF d'une commande.
    - order : dict (order_number, status, total, shipping_*, notes, created_at, customer_name, customer_email)
    - items : liste de dicts (product_name, unit_price, quantity, subtotal)
    - settings : dict des paramètres du site (site_name, owner_name, whatsapp, location)
    Retourne les octets du PDF (bytes).
    """
    settings = settings or {}
    site_name = settings.get('site_name') or 'HDATTAHER MOBILE'
    owner_name = settings.get('owner_name') or ''
    whatsapp = settings.get('whatsapp') or ''
    location = settings.get('location') or ''

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=20 * mm, bottomMargin=20 * mm,
        leftMargin=18 * mm, rightMargin=18 * mm,
    )

    styles = getSampleStyleSheet()
    style_title = ParagraphStyle('InvoiceTitle', parent=styles['Title'],
                                  fontSize=20, textColor=PRIMARY_COLOR, spaceAfter=2)
    style_muted = ParagraphStyle('Muted', parent=styles['Normal'],
                                  fontSize=9, textColor=MUTED_COLOR)
    style_normal = ParagraphStyle('NormalDark', parent=styles['Normal'],
                                   fontSize=10, textColor=TEXT_COLOR, leading=14)
    style_right = ParagraphStyle('Right', parent=style_normal, alignment=TA_RIGHT)
    style_section = ParagraphStyle('Section', parent=styles['Heading3'],
                                    fontSize=11, textColor=PRIMARY_COLOR, spaceBefore=6, spaceAfter=4)

    story = []

    # ── En-tête ──
    header_data = [[
        Paragraph(f"<b>{site_name}</b>", style_title),
        Paragraph(f"<b>FACTURE</b><br/>N° {order.get('order_number', '')}", style_right),
    ]]
    header_table = Table(header_data, colWidths=[95 * mm, 75 * mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(header_table)

    coords = []
    if owner_name:
        coords.append(owner_name)
    if location:
        coords.append(location)
    if whatsapp:
        coords.append(f"WhatsApp : {whatsapp}")
    if coords:
        story.append(Paragraph(' • '.join(coords), style_muted))

    story.append(Spacer(1, 4 * mm))
    story.append(HRFlowable(width='100%', thickness=1, color=BORDER_COLOR))
    story.append(Spacer(1, 4 * mm))

    # ── Infos commande / client ──
    date_str = (order.get('created_at') or '')[:10]
    info_data = [[
        Paragraph(
            f"<b>Facturé à</b><br/>{order.get('shipping_name', '')}<br/>"
            f"{order.get('shipping_phone', '')}<br/>{order.get('shipping_address', '')}",
            style_normal
        ),
        Paragraph(
            f"<b>Détails</b><br/>Date : {date_str}<br/>"
            f"Statut : {order.get('status', '')}<br/>"
            f"Client : {order.get('customer_name', '')}",
            style_right
        ),
    ]]
    info_table = Table(info_data, colWidths=[95 * mm, 75 * mm])
    info_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    story.append(info_table)
    story.append(Spacer(1, 8 * mm))

    # ── Tableau des articles ──
    table_data = [['Produit', 'Prix unitaire', 'Quantité', 'Sous-total']]
    for item in items:
        table_data.append([
            item.get('product_name', ''),
            f"{item.get('unit_price', 0):,.0f} FCFA".replace(',', ' '),
            str(item.get('quantity', 0)),
            f"{item.get('subtotal', 0):,.0f} FCFA".replace(',', ' '),
        ])

    items_table = Table(table_data, colWidths=[70 * mm, 35 * mm, 25 * mm, 40 * mm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9.5),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 4 * mm))

    # ── Total ──
    total_data = [['', 'Total', f"{order.get('total', 0):,.0f} FCFA".replace(',', ' ')]]
    total_table = Table(total_data, colWidths=[100 * mm, 35 * mm, 35 * mm])
    total_table.setStyle(TableStyle([
        ('FONTNAME', (1, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 0), (-1, 0), 12),
        ('ALIGN', (1, 0), (-1, 0), 'RIGHT'),
        ('TEXTCOLOR', (1, 0), (-1, 0), PRIMARY_COLOR),
        ('LINEABOVE', (1, 0), (-1, 0), 1, PRIMARY_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(total_table)

    if order.get('notes'):
        story.append(Spacer(1, 8 * mm))
        story.append(Paragraph(f"<b>Notes :</b> {order['notes']}", style_normal))

    story.append(Spacer(1, 14 * mm))
    footer_style = ParagraphStyle('Footer', parent=style_muted, alignment=TA_CENTER)
    story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER_COLOR))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(f"Merci pour votre confiance — {site_name}", footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
