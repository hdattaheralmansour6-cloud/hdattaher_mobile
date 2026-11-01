"""
HDATTAHER MOBILE - Panier d'achat (stocké en session Flask)

Chaque ligne du panier a une « clé » :
  - « id_produit »                 pour un produit simple
  - « id_produit:id_variante »     pour une version précise (ex. 256 Go · Noir)
"""
from flask import session
from database import db, get_supabase
from shop_extras import get_variants_by_ids, variant_label, variant_price


CART_SESSION_KEY = 'cart'


def make_key(product_id, variant_id=None):
    return f"{product_id}:{variant_id}" if variant_id else str(product_id)


def split_key(key):
    product_id, _, variant_id = str(key).partition(':')
    return product_id, (variant_id or None)


def _get_raw_cart():
    return session.get(CART_SESSION_KEY, {})


def _save_cart(cart):
    session[CART_SESSION_KEY] = cart
    session.modified = True


def add_to_cart(product_id, quantity=1, variant_id=None):
    cart = _get_raw_cart()
    key = make_key(product_id, variant_id)
    cart[key] = cart.get(key, 0) + max(1, quantity)
    _save_cart(cart)


def update_quantity(key, quantity):
    cart = _get_raw_cart()
    key = str(key)
    if quantity <= 0:
        cart.pop(key, None)
    else:
        cart[key] = quantity
    _save_cart(cart)


def remove_from_cart(key):
    cart = _get_raw_cart()
    cart.pop(str(key), None)
    _save_cart(cart)


def clear_cart():
    session.pop(CART_SESSION_KEY, None)
    session.modified = True


def cart_item_count():
    return sum(_get_raw_cart().values())


def get_cart_details():
    """Retourne (items, total) avec les infos produits (et variantes) à jour depuis la base."""
    cart = _get_raw_cart()
    if not cart:
        return [], 0

    sb = get_supabase()
    parsed = {key: split_key(key) for key in cart}
    product_ids = list({pid for pid, _ in parsed.values()})
    result = sb.table('products').select('*').in_('id', product_ids).execute()
    products_by_id = {str(p['id']): p for p in (result.data or [])}
    variants_by_id = get_variants_by_ids([vid for _, vid in parsed.values()])

    items = []
    total = 0
    changed = False

    for key, qty in list(cart.items()):
        product_id, variant_id = parsed[key]
        product = products_by_id.get(product_id)
        if not product or not product.get('is_active', True):
            # Produit supprimé ou désactivé entre-temps : on le retire du panier
            cart.pop(key, None)
            changed = True
            continue

        variant = None
        if variant_id:
            variant = variants_by_id.get(variant_id)
            if not variant or str(variant.get('product_id')) != product_id:
                cart.pop(key, None)
                changed = True
                continue
            available = int(variant.get('stock') or 0)
            unit_price = variant_price(product, variant)
        else:
            if product.get('has_variants'):
                # Le produit a maintenant plusieurs versions : il faut en choisir une
                cart.pop(key, None)
                changed = True
                continue
            available = int(product.get('stock') or 0)
            unit_price = float(product.get('price') or 0)

        # On ne laisse jamais la quantité dépasser le stock disponible
        if available <= 0:
            cart.pop(key, None)
            changed = True
            continue
        if qty > available:
            qty = available
            cart[key] = qty
            changed = True

        if product.get('image') and not str(product['image']).startswith('http'):
            try:
                product['image'] = sb.storage.from_('product-images').get_public_url(product['image'])
            except Exception:
                pass

        subtotal = unit_price * qty
        total += subtotal
        items.append({
            'key': key,
            'product': product,
            'variant': variant,
            'variant_id': variant_id,
            'label': variant_label(variant),
            'unit_price': unit_price,
            'available': available,
            'quantity': qty,
            'subtotal': subtotal,
        })

    if changed:
        _save_cart(cart)

    return items, total
