"""
HDATTAHER MOBILE - Gestion des commandes (création, stock automatique, statuts)
"""
import secrets
from datetime import datetime

from database import db, get_supabase

ORDER_STATUSES = ['En attente', 'Confirmée', 'Préparation', 'Expédiée', 'Livrée', 'Annulée']


def generate_order_number():
    date_part = datetime.utcnow().strftime('%y%m%d')
    random_part = secrets.token_hex(3).upper()
    return f"CMD{date_part}{random_part}"


def create_order_from_cart(customer_id, cart_items, shipping_name, shipping_phone, shipping_address, notes=''):
    """
    Crée une commande à partir des articles du panier (déjà validés/enrichis
    par cart.get_cart_details). Diminue le stock de chaque produit commandé.
    Retourne (order, error).
    """
    if not cart_items:
        return None, "Votre panier est vide."

    sb = get_supabase()

    # Vérification finale du stock (au cas où il aurait changé depuis l'affichage du panier)
    for item in cart_items:
        product_id = item['product']['id']
        fresh = sb.table('products').select('stock').eq('id', product_id).execute()
        current_stock = fresh.data[0]['stock'] if fresh.data else 0
        if current_stock < item['quantity']:
            return None, f"Stock insuffisant pour \"{item['product']['name']}\" (disponible : {current_stock})."

    total = sum(item['subtotal'] for item in cart_items)

    order = db.insert('orders', {
        'order_number': generate_order_number(),
        'customer_id': customer_id,
        'status': 'En attente',
        'total': total,
        'shipping_name': shipping_name,
        'shipping_phone': shipping_phone,
        'shipping_address': shipping_address,
        'notes': notes,
    })

    if not order:
        return None, "Erreur lors de la création de la commande."

    for item in cart_items:
        product = item['product']
        db.insert('order_items', {
            'order_id': order['id'],
            'product_id': product['id'],
            'product_name': product['name'],
            'quantity': item['quantity'],
            'unit_price': product['price'],
            'subtotal': item['subtotal'],
        })

        # Baisse automatique du stock (le produit passe en "Rupture"
        # tout seul dès que le stock atteint 0, l'affichage est dynamique)
        new_stock = max(0, product.get('stock', 0) - item['quantity'])
        db.update('products', {'stock': new_stock}, {'id': product['id']})

    return order, None


def get_customer_orders(customer_id):
    orders = db.fetch_all('orders', filters={'customer_id': customer_id}, order='created_at')
    return orders or []


def get_order_with_items(order_id):
    rows = db.fetch_all('orders', filters={'id': order_id}, limit=1)
    if not rows:
        return None, []
    order = rows[0]
    items = db.fetch_all('order_items', filters={'order_id': order_id})
    return order, (items or [])


def update_order_status(order_id, new_status):
    if new_status not in ORDER_STATUSES:
        return False
    db.update('orders', {
        'status': new_status,
        'updated_at': datetime.utcnow().isoformat(),
    }, {'id': order_id})
    return True


def get_all_orders(status_filter=None):
    sb = get_supabase()
    query = sb.table('orders').select('*, customers(full_name, email, phone)').order('created_at', desc=True)
    if status_filter:
        query = query.eq('status', status_filter)
    result = query.execute()
    orders = result.data or []
    for o in orders:
        customer = o.pop('customers', None)
        o['customer_name'] = customer['full_name'] if customer else 'Client supprimé'
        o['customer_email'] = customer['email'] if customer else ''
    return orders
