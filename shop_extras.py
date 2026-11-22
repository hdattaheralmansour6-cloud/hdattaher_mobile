"""
HDATTAHER MOBILE - Zones de livraison, variantes (stockage / couleur) et avis clients.

Toutes les fonctions de lecture sont « tolérantes » : si les nouvelles tables
n'existent pas encore dans Supabase, elles renvoient simplement une liste vide
et le site continue de fonctionner comme avant.
"""
from database import db


# ============================================================
#  ZONES DE LIVRAISON
# ============================================================

def get_zones(active_only=True):
    try:
        filters = {'is_active': True} if active_only else None
        return db.fetch_all('delivery_zones', '*', filters=filters, order=('sort_order', True)) or []
    except Exception:
        return []


def get_zone(zone_id):
    if not zone_id:
        return None
    try:
        return db.fetch_one('delivery_zones', '*', {'id': zone_id})
    except Exception:
        return None


# ============================================================
#  VARIANTES
# ============================================================

def variant_label(v):
    """« 256 Go · Noir » (ou seulement l'un des deux)."""
    if not v:
        return ''
    return ' · '.join(x for x in ((v.get('storage') or '').strip(), (v.get('color') or '').strip()) if x)


def variant_price(product, v):
    """Prix de la variante, ou le prix du produit si la variante n'a pas de prix à elle."""
    try:
        p = float(v.get('price')) if v and v.get('price') not in (None, '') else 0
    except (TypeError, ValueError):
        p = 0
    return p if p > 0 else float(product.get('price') or 0)


def get_variants(product_id):
    try:
        return db.fetch_all('product_variants', '*', filters={'product_id': product_id},
                            order=('sort_order', True)) or []
    except Exception:
        return []


def get_variants_by_ids(ids):
    ids = [i for i in ids if i]
    if not ids:
        return {}
    try:
        from database import get_supabase
        rows = get_supabase().table('product_variants').select('*').in_('id', ids).execute().data or []
        return {str(r['id']): r for r in rows}
    except Exception:
        return {}


def sync_product_stock(product_id):
    """Le stock du produit = la somme des stocks de ses variantes."""
    variants = get_variants(product_id)
    total = sum(int(v.get('stock') or 0) for v in variants)
    try:
        db.update('products', {'stock': total, 'has_variants': bool(variants)}, {'id': product_id})
    except Exception:
        db.update('products', {'stock': total}, {'id': product_id})
    return total


def save_variants(product_id, rows):
    """
    Enregistre les variantes saisies dans l'admin.
    rows : liste de dicts {storage, color, price, stock}.
    Les variantes déjà existantes (même stockage + couleur) sont mises à jour
    (les anciennes commandes gardent leur lien), les autres créées ou retirées.
    Retourne le stock total.
    """
    def key(v):
        return ((v.get('storage') or '').strip().lower(), (v.get('color') or '').strip().lower())

    existing = {key(v): v for v in get_variants(product_id)}
    seen = set()
    for i, r in enumerate(rows):
        k = key(r)
        if k == ('', '') or k in seen:
            continue
        seen.add(k)
        data = {
            'storage': (r.get('storage') or '').strip()[:40] or None,
            'color': (r.get('color') or '').strip()[:40] or None,
            'price': r.get('price') if (r.get('price') or 0) > 0 else None,
            'stock': max(0, min(int(r.get('stock') or 0), 100000)),
            'sort_order': i,
        }
        if k in existing:
            db.update('product_variants', data, {'id': existing[k]['id']})
        else:
            db.insert('product_variants', dict(data, product_id=product_id))
    for k, v in existing.items():
        if k not in seen:
            db.delete('product_variants', {'id': v['id']})
    return sync_product_stock(product_id)


def remove_variants(product_id):
    for v in get_variants(product_id):
        db.delete('product_variants', {'id': v['id']})
    try:
        db.update('products', {'has_variants': False}, {'id': product_id})
    except Exception:
        pass


def change_variant_stock(variant_id, delta):
    """Ajoute / retire du stock à une variante puis met à jour le produit. Retourne False si introuvable."""
    try:
        v = db.fetch_one('product_variants', 'id, product_id, stock', {'id': variant_id})
    except Exception:
        v = None
    if not v:
        return False
    new_stock = max(0, int(v.get('stock') or 0) + int(delta))
    db.update('product_variants', {'stock': new_stock}, {'id': variant_id})
    sync_product_stock(v['product_id'])
    return True


# ============================================================
#  AVIS CLIENTS
# ============================================================

def get_reviews(product_id, limit=30):
    try:
        return db.fetch_all('reviews', '*', filters={'product_id': product_id, 'is_approved': True},
                            order=('created_at', False), limit=limit) or []
    except Exception:
        return []


def refresh_rating(product_id):
    """Recalcule la note moyenne affichée sur le produit (avis publiés seulement)."""
    try:
        rows = db.fetch_all('reviews', 'rating', filters={'product_id': product_id, 'is_approved': True}) or []
        count = len(rows)
        avg = round(sum(int(r.get('rating') or 0) for r in rows) / count, 2) if count else 0
        db.update('products', {'rating_avg': avg, 'rating_count': count}, {'id': product_id})
    except Exception:
        pass


def count_pending_reviews():
    try:
        return db.count('reviews', {'is_approved': False})
    except Exception:
        return 0


# ============================================================
#  CODES PROMO
# ============================================================

def normalize_code(code):
    return ''.join(ch for ch in (code or '').upper() if ch.isalnum() or ch in '-_')[:24]


def get_coupons():
    try:
        return db.fetch_all('coupons', '*', order=('created_at', False)) or []
    except Exception:
        return None


def check_coupon(code, subtotal):
    """
    Vérifie un code promo pour un panier.
    Retourne (coupon, réduction en FCFA, message d'erreur).
    """
    from datetime import date
    code = normalize_code(code)
    if not code:
        return None, 0, None
    try:
        c = db.fetch_one('coupons', '*', {'code': code})
    except Exception:
        c = None
    if not c or c.get('is_active') is False:
        return None, 0, "Ce code promo n'existe pas."
    ends = str(c.get('ends_at') or '')[:10]
    if ends and ends < date.today().isoformat():
        return None, 0, 'Ce code promo a expiré.'
    if c.get('max_uses') and int(c.get('uses') or 0) >= int(c['max_uses']):
        return None, 0, "Ce code promo a déjà été utilisé le nombre de fois prévu."
    minimum = float(c.get('min_total') or 0)
    if subtotal < minimum:
        return None, 0, f"Ce code est valable à partir de {minimum:,.0f} FCFA d'achat.".replace(',', ' ')
    value = float(c.get('value') or 0)
    if c.get('kind') == 'percent':
        discount = round(subtotal * min(value, 90) / 100)
    else:
        discount = value
    discount = max(0, min(discount, subtotal))
    return c, discount, None


def use_coupon(coupon):
    try:
        db.update('coupons', {'uses': int(coupon.get('uses') or 0) + 1}, {'id': coupon['id']})
    except Exception:
        pass


# ============================================================
#  ALERTES « DE RETOUR EN STOCK »
# ============================================================

def _digits(phone):
    return ''.join(ch for ch in (phone or '') if ch.isdigit())


def add_stock_alert(product_id, phone, name=''):
    """Enregistre un numéro à prévenir. Renvoie 'ok', 'phone', 'dup', 'full' ou 'error'."""
    digits = _digits(phone)
    if len(digits) < 8 or len(digits) > 15:
        return 'phone'
    try:
        waiting = db.fetch_all('stock_alerts', 'id, phone', {'product_id': product_id, 'notified': False})
        if any(_digits(r.get('phone')) == digits for r in waiting):
            return 'dup'
        if len(waiting) >= 300:
            return 'full'
        db.insert('stock_alerts', {'product_id': product_id, 'phone': (phone or '').strip()[:30],
                                   'name': ' '.join((name or '').split())[:60], 'notified': False})
    except Exception:
        return 'error'
    return 'ok'


def get_stock_alerts():
    """Alertes en attente regroupées par produit (produits revenus en stock d'abord).
    Renvoie None si la table n'existe pas encore."""
    try:
        alerts = db.fetch_all('stock_alerts', '*', {'notified': False}, order=('created_at', True))
    except Exception:
        return None
    ids = list({a.get('product_id') for a in alerts if a.get('product_id')})
    products = {}
    if ids:
        try:
            from database import get_supabase
            rows = get_supabase().table('products').select('id, name, stock, image, price, is_active') \
                .in_('id', ids).execute().data or []
            products = {p['id']: p for p in rows}
        except Exception:
            products = {}
    groups = {}
    for a in alerts:
        p = products.get(a.get('product_id'))
        if not p:
            continue
        g = groups.setdefault(p['id'], {'product': p, 'alerts': [],
                                        'ready': int(p.get('stock') or 0) > 0 and p.get('is_active', True) is not False})
        g['alerts'].append(a)
    return sorted(groups.values(), key=lambda g: (not g['ready'], -len(g['alerts'])))


def count_ready_alerts():
    """Nombre de clients à prévenir (produit revenu en stock) — pour la pastille du menu admin."""
    groups = get_stock_alerts()
    return sum(len(g['alerts']) for g in groups if g['ready']) if groups else 0


def count_waiting_alerts(product_id):
    try:
        return db.count('stock_alerts', {'product_id': product_id, 'notified': False})
    except Exception:
        return 0
