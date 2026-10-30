"""
HDATTAHER MOBILE - Images d'aperçu pour WhatsApp / Facebook (1200 x 630, JPEG)
Quand un lien du site est partagé, WhatsApp affiche cette image avec la photo,
le nom et le prix du produit, aux couleurs noir et or de la boutique.
"""
import io
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

W, H = 1200, 630
BG = (11, 11, 13)
CARD = (22, 22, 26)
GOLD = (212, 175, 55)
GOLD_LIGHT = (243, 222, 154)
GOLD_DARK = (169, 129, 47)
WHITE = (245, 242, 235)
GREY = (160, 156, 148)
GREEN = (52, 211, 153)
RED = (248, 113, 113)
AMBER = (251, 191, 36)

_FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'fonts')
_IMG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'img')
_font_cache = {}


def _font(size, bold=False, italic=False):
    key = (size, bold, italic)
    if key not in _font_cache:
        path = os.path.join(_FONT_DIR, 'lora-italic.woff' if italic else 'lora.woff')
        try:
            f = ImageFont.truetype(path, size)
            try:
                f.set_variation_by_axes([700 if bold else 400])
            except Exception:
                pass
        except Exception:
            f = ImageFont.load_default()
        _font_cache[key] = f
    return _font_cache[key]


def fcfa(value):
    try:
        n = int(round(float(value or 0)))
    except (TypeError, ValueError):
        n = 0
    return f"{n:,}".replace(',', ' ') + ' FCFA'


def _gold_gradient(size):
    """Dégradé or (clair -> foncé) de la taille donnée."""
    w, h = size
    grad = Image.new('RGB', (w, h))
    px = grad.load()
    for y in range(h):
        for x in range(w):
            t = (x / max(w - 1, 1)) * 0.6 + (y / max(h - 1, 1)) * 0.4
            px[x, y] = tuple(int(GOLD_LIGHT[i] + (GOLD_DARK[i] - GOLD_LIGHT[i]) * t) for i in range(3))
    return grad


def _background():
    img = Image.new('RGB', (W, H), BG)
    glow = Image.new('L', (W, H), 0)
    ImageDraw.Draw(glow).ellipse((700, -260, 1500, 420), fill=70)
    ImageDraw.Draw(glow).ellipse((-300, 380, 500, 900), fill=35)
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    img.paste(Image.new('RGB', (W, H), GOLD), (0, 0), glow)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W - 1, H - 1), outline=(60, 50, 25), width=2)
    return img


def _wrap(draw, text, font, max_width, max_lines):
    words = (text or '').split()
    lines, cur = [], ''
    for w in words:
        test = (cur + ' ' + w).strip()
        if draw.textlength(test, font=font) <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
            while draw.textlength(cur, font=font) > max_width and len(cur) > 1:
                cur = cur[:-1]
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and draw.textlength(last + '…', font=font) > max_width:
            last = last[:-1]
        lines[-1] = last.rstrip() + '…'
    return lines


def _brand_badge(img, x, y, size=64):
    """Petit logo « HM » noir et or, comme dans l'en-tête du site."""
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((x, y, x + size, y + size), radius=int(size * .28), fill=BG, outline=GOLD, width=3)
    f = _font(int(size * .42), bold=True)
    tw = d.textlength('HM', font=f)
    d.text((x + (size - tw) / 2, y + size / 2), 'HM', font=f, fill=GOLD_LIGHT, anchor='lm')


def _photo_panel(img, box, photo_bytes, radius=34):
    """Panneau clair arrondi avec la photo du produit centrée."""
    x0, y0, x1, y1 = box
    pw, ph = x1 - x0, y1 - y0
    panel = Image.new('RGB', (pw, ph), (250, 248, 243))
    photo = None
    if photo_bytes:
        try:
            photo = Image.open(io.BytesIO(photo_bytes))
            photo = ImageOps.exif_transpose(photo).convert('RGBA')
        except Exception:
            photo = None
    if photo is not None:
        pad = int(min(pw, ph) * .07)
        photo.thumbnail((pw - 2 * pad, ph - 2 * pad), Image.LANCZOS)
        panel.paste(photo, ((pw - photo.width) // 2, (ph - photo.height) // 2), photo)
    else:
        d = ImageDraw.Draw(panel)
        cx, cy = pw // 2, ph // 2
        d.rounded_rectangle((cx - 70, cy - 120, cx + 70, cy + 120), radius=26, outline=GOLD_DARK, width=8)
        d.ellipse((cx - 9, cy + 88, cx + 9, cy + 106), fill=GOLD_DARK)
    mask = Image.new('L', (pw, ph), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, pw - 1, ph - 1), radius=radius, fill=255)
    # ombre douce
    shadow = Image.new('L', (W, H), 0)
    ImageDraw.Draw(shadow).rounded_rectangle((x0 + 6, y0 + 14, x1 + 6, y1 + 14), radius=radius, fill=150)
    img.paste(Image.new('RGB', (W, H), (0, 0, 0)), (0, 0), shadow.filter(ImageFilter.GaussianBlur(18)))
    img.paste(panel, (x0, y0), mask)
    ImageDraw.Draw(img).rounded_rectangle(box, radius=radius, outline=GOLD, width=3)


def _pay_logos(img, x, y, h=52, label=True):
    """Logos Amanata et Nita sur des petites cartes blanches. Retourne la largeur utilisée."""
    d = ImageDraw.Draw(img)
    cx = x
    if label:
        lf = _font(24, italic=True)
        d.text((cx, y + h / 2), 'Paiement', font=lf, fill=GREY, anchor='lm')
        cx += int(d.textlength('Paiement', font=lf)) + 14
    for name in ('amanata', 'nita'):
        try:
            logo = Image.open(os.path.join(_IMG_DIR, name + '.png')).convert('RGB')
        except Exception:
            continue
        pad = 6
        logo.thumbnail((200, h - 2 * pad), Image.LANCZOS)
        cw = logo.width + 2 * pad + 8
        d.rounded_rectangle((cx, y, cx + cw, y + h), radius=12, fill=(255, 255, 255))
        img.paste(logo, (cx + (cw - logo.width) // 2, y + (h - logo.height) // 2))
        cx += cw + 10
    return cx - x


def _to_jpeg(img):
    out = io.BytesIO()
    img.save(out, 'JPEG', quality=86, optimize=True, progressive=True)
    return out.getvalue()


def render_product(product, photo_bytes=None):
    """Image d'aperçu d'un produit : photo + marque + nom + prix + disponibilité."""
    img = _background()
    _photo_panel(img, (40, 40, 590, 590), photo_bytes)
    d = ImageDraw.Draw(img)

    x, right = 640, 1160
    maxw = right - x
    # En-tête boutique
    _brand_badge(img, x, 46, 58)
    d.text((x + 74, 75), 'HDATTAHER MOBILE', font=_font(26, bold=True), fill=GOLD_LIGHT, anchor='lm')

    y = 150
    brand = ' '.join((product.get('brand') or '').split()).upper()
    if brand:
        d.text((x, y), brand, font=_font(26, bold=True), fill=GOLD)
        y += 44

    # Nom (3 lignes max, taille adaptée à la longueur)
    name = ' '.join((product.get('name') or '').split()) or 'Produit'
    size = 58 if len(name) <= 22 else 50 if len(name) <= 40 else 44
    nf = _font(size, bold=True)
    for line in _wrap(d, name, nf, maxw, 3):
        d.text((x, y), line, font=nf, fill=WHITE)
        y += int(size * 1.18)

    # Prix
    y += 18
    price = product.get('price') or 0
    old = product.get('old_price') or 0
    disc = int(product.get('discount') or 0)
    pf = _font(64, bold=True)
    price_txt = fcfa(price)
    grad = _gold_gradient((int(d.textlength(price_txt, font=pf)) + 4, 80))
    mask = Image.new('L', grad.size, 0)
    ImageDraw.Draw(mask).text((0, 0), price_txt, font=pf, fill=255)
    img.paste(grad, (x, y), mask)
    y += 92

    if (old and old > price) or disc > 0:
        of = _font(30)
        if old and old > price:
            old_txt = fcfa(old)
            d.text((x, y), old_txt, font=of, fill=GREY)
            ow = d.textlength(old_txt, font=of)
            d.line((x, y + 20, x + ow, y + 20), fill=GREY, width=3)
            bx = x + ow + 18
        else:
            bx = x
        if disc <= 0 and old and old > price:
            disc = int(round((old - price) / old * 100))
        if disc > 0:
            badge = f'-{disc} %'
            bf = _font(28, bold=True)
            bw = d.textlength(badge, font=bf)
            d.rounded_rectangle((bx, y - 2, bx + bw + 30, y + 42), radius=21, fill=(185, 28, 28))
            d.text((bx + 15, y + 20), badge, font=bf, fill=WHITE, anchor='lm')
        y += 60

    # Disponibilité
    in_stock = (product.get('stock') or 0) > 0
    col = GREEN if in_stock else AMBER
    d.ellipse((x, y + 8, x + 18, y + 26), fill=col)
    d.text((x + 30, y + 17), 'En stock' if in_stock else 'Bientôt de retour', font=_font(28, bold=True), fill=col, anchor='lm')

    # Pied
    d.line((x, 548, right, 548), fill=(70, 60, 30), width=2)
    d.text((x, 586), 'Livraison au Niger', font=_font(24, italic=True), fill=GREY, anchor='lm')
    lw = _pay_logos(Image.new('RGB', (W, 80)), 0, 0, 52, label=False)  # largeur des logos
    _pay_logos(img, right - lw + 10, 560, 52, label=False)
    return _to_jpeg(img)


def render_home(photos=()):
    """Image d'aperçu de la boutique : logo, slogan et jusqu'à 3 produits."""
    img = _background()
    d = ImageDraw.Draw(img)
    photos = [p for p in photos if p][:3]

    _brand_badge(img, 60, 56, 76)
    d.text((156, 94), 'HDATTAHER MOBILE', font=_font(40, bold=True), fill=GOLD_LIGHT, anchor='lm')

    if photos:
        tf = _font(54, bold=True)
        d.text((60, 190), 'Le smartphone de vos rêves,', font=tf, fill=WHITE)
        d.text((60, 254), 'livré au Niger.', font=_font(54, bold=True, italic=True), fill=GOLD_LIGHT)
        n = len(photos)
        tile, gap = 190, 26
        total = n * tile + (n - 1) * gap
        x0 = 60
        for i, data in enumerate(photos):
            x = x0 + i * (tile + gap)
            _photo_panel(img, (x, 360, x + tile, 360 + tile), data, radius=26)
        d = ImageDraw.Draw(img)
        rx = max(x0 + total + 50, 760)
        lines = ['iPhone · Samsung', 'Xiaomi · Tecno', 'Accessoires']
        for i, t in enumerate(lines):
            d.text((rx, 395 + i * 48), t, font=_font(32, bold=True), fill=GREY)
        _pay_logos(img, rx, 395 + 3 * 48 + 4, 56, label=False)
    else:
        tf = _font(72, bold=True)
        d.text((60, 230), 'Le smartphone de vos rêves,', font=tf, fill=WHITE)
        d.text((60, 320), 'livré au Niger.', font=_font(72, bold=True, italic=True), fill=GOLD_LIGHT)
        d.text((60, 470), 'Smartphones neufs · Accessoires · Livraison au Niger', font=_font(32), fill=GREY)
        _pay_logos(img, 60, 520, 60)
    return _to_jpeg(img)
