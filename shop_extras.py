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
