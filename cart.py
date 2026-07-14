"""
HDATTAHER MOBILE - Panier d'achat (stocké en session Flask)
"""
from flask import session
from database import db, get_supabase


CART_SESSION_KEY = 'cart'


def _get_raw_cart():
    return session.get(CART_SESSION_KEY, {})


def _save_cart(cart):
    session[CART_SESSION_KEY] = cart
    session.modified = True


def add_to_cart(product_id, quantity=1):
    cart = _get_raw_cart()
    product_id = str(product_id)
    cart[product_id] = cart.get(product_id, 0) + max(1, quantity)
    _save_cart(cart)


def update_quantity(product_id, quantity):
    cart = _get_raw_cart()
    product_id = str(product_id)
    if quantity <= 0:
        cart.pop(product_id, None)
    else:
        cart[product_id] = quantity
    _save_cart(cart)


def remove_from_cart(product_id):
    cart = _get_raw_cart()
    cart.pop(str(product_id), None)
    _save_cart(cart)


def clear_cart():
    session.pop(CART_SESSION_KEY, None)
    session.modified = True


def cart_item_count():
    return sum(_get_raw_cart().values())


def get_cart_details():
    """Retourne (items, total) avec les infos produits à jour depuis la base."""
    cart = _get_raw_cart()
    if not cart:
        return [], 0

    sb = get_supabase()
    ids = list(cart.keys())
    result = sb.table('products').select('*').in_('id', ids).execute()
    products_by_id = {p['id']: p for p in (result.data or [])}

    items = []
    total = 0
    changed = False

    for product_id, qty in list(cart.items()):
        product = products_by_id.get(product_id)
        if not product or not product.get('is_active', True):
            # Produit supprimé ou désactivé entre-temps : on le retire du panier
            cart.pop(product_id, None)
            changed = True
            continue

        # On ne laisse jamais la quantité dépasser le stock disponible
        available = product.get('stock', 0)
        if available <= 0:
            cart.pop(product_id, None)
            changed = True
            continue
        if qty > available:
            qty = available
            cart[product_id] = qty
            changed = True

        if product.get('image') and not str(product['image']).startswith('http'):
            try:
                product['image'] = sb.storage.from_('product-images').get_public_url(product['image'])
            except Exception:
                pass

        subtotal = float(product['price']) * qty
        total += subtotal
        items.append({
            'product': product,
            'quantity': qty,
            'subtotal': subtotal,
        })

    if changed:
        _save_cart(cart)

    return items, total
