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


def create_order_from_cart(customer_id, cart_items, shipping_name, shipping_phone, shipping_address, notes='',
                           payment_method=None, payment_proof=None):
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
        'payment_method': payment_method,
        'payment_proof': payment_proof,
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


def _shift_stock(order_id, sign):
    """Remet (+1) ou reprend (-1) le stock des produits d'une commande."""
    try:
        items = db.fetch_all('order_items', 'product_id, quantity', {'order_id': order_id}) or []
    except Exception:
        return
    for it in items:
        pid, qty = it.get('product_id'), int(it.get('quantity') or 0)
        if not pid or qty <= 0:
            continue
        try:
            row = db.fetch_one('products', 'stock', {'id': pid})
            if row is None:
                continue
            new_stock = max(0, int(row.get('stock') or 0) + sign * qty)
            db.update('products', {'stock': new_stock}, {'id': pid})
        except Exception:
            continue


def update_order_status(order_id, new_status):
    """
    Change le statut d'une commande.
    - Passage en « Annulée »  : le stock des produits est remis automatiquement.
    - Sortie de « Annulée »   : le stock est repris (commande réactivée).
    """
    if new_status not in ORDER_STATUSES:
        return False
    current = db.fetch_one('orders', 'status', {'id': order_id})
    if not current:
        return False
    old_status = current.get('status')
    if old_status == new_status:
        return True
    db.update('orders', {
        'status': new_status,
        'updated_at': datetime.utcnow().isoformat(),
    }, {'id': order_id})
    if new_status == 'Annulée' and old_status != 'Annulée':
        _shift_stock(order_id, +1)
    elif old_status == 'Annulée' and new_status != 'Annulée':
        _shift_stock(order_id, -1)
    return True


# Étape suivante proposée en un clic dans l'admin
NEXT_STATUS = {
    'En attente': 'Confirmée',
    'Confirmée': 'Préparation',
    'Préparation': 'Expédiée',
    'Expédiée': 'Livrée',
}


def get_admin_overview():
    """Chiffres clés du tableau de bord (aujourd'hui, 7 jours, à traiter)."""
    from datetime import timedelta
    now = datetime.utcnow()
    today = now.strftime('%Y-%m-%d')
    d7 = (now - timedelta(days=7)).isoformat()
    d14 = (now - timedelta(days=14)).isoformat()
    try:
        orders = db.fetch_all('orders', 'id, status, total, created_at',
                              filters=[('created_at', 'gte', d14)]) or []
    except Exception:
        orders = []

    def ventes(rows):
        return [o for o in rows if o.get('status') in STATUTS_VENTE]

    last7 = [o for o in orders if (o.get('created_at') or '') >= d7]
    prev7 = [o for o in orders if (o.get('created_at') or '') < d7]
    today_rows = [o for o in orders if (o.get('created_at') or '')[:10] == today]

    ca7 = sum(float(o.get('total') or 0) for o in ventes(last7))
    ca_prev = sum(float(o.get('total') or 0) for o in ventes(prev7))
    evolution = None
    if ca_prev > 0:
        evolution = round((ca7 - ca_prev) / ca_prev * 100)

    try:
        pending = db.count('orders', {'status': 'En attente'})
    except Exception:
        pending = 0
    try:
        stock_alerts = db.fetch_all('products', 'id, name, stock, image',
                                    filters=[('stock', 'lte', 5), ('is_active', 'eq', True)],
                                    order=('stock', True)) or []
    except Exception:
        stock_alerts = []

    nb7 = len(ventes(last7))
    return {
        'ca_today': sum(float(o.get('total') or 0) for o in ventes(today_rows)),
        'orders_today': len(today_rows),
        'ca_7': ca7,
        'evolution_7': evolution,
        'nb_7': nb7,
        'panier_moyen': (ca7 / nb7) if nb7 else 0,
        'pending': pending,
        'stock_alerts': stock_alerts,
        'out_of_stock': sum(1 for p in stock_alerts if (p.get('stock') or 0) == 0),
    }


def get_all_orders(status_filter=None):
    sb = get_supabase()

    def _run(cols):
        query = sb.table('orders').select(f'*, customers({cols})').order('created_at', desc=True)
        if status_filter:
            query = query.eq('status', status_filter)
        return query.execute().data or []

    try:
        orders = _run('full_name, email, phone, avatar_url')
    except Exception:
        # Colonne avatar_url pas encore créée dans Supabase
        orders = _run('full_name, email, phone')
    for o in orders:
        customer = o.pop('customers', None)
        o['customer_name'] = customer['full_name'] if customer else 'Client supprimé'
        o['customer_email'] = customer['email'] if customer else ''
        o['customer_avatar'] = (customer or {}).get('avatar_url') or ''
    return orders


# ============================================================
#  STATISTIQUES POUR LE DASHBOARD ADMIN (Phase 3)
# ============================================================

# Statuts comptabilisés comme des ventes effectives (pour le CA)
STATUTS_VENTE = ('Confirmée', 'Préparation', 'Expédiée', 'Livrée')


def get_dashboard_stats(days=30):
    """
    Agrège les données nécessaires aux graphiques du dashboard admin :
    - CA + nombre de commandes par jour (période demandée)
    - Répartition des commandes par statut
    - Top 5 produits les plus vendus (quantité)
    - Produits en stock bas (<= 5)
    """
    from collections import defaultdict
    from datetime import datetime, timedelta

    sb = get_supabase()
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()

    orders = db.fetch_all(
        'orders', 'id, status, total, created_at',
        filters=[('created_at', 'gte', since)],
    )

    # --- CA + nb commandes par jour ---
    par_jour = defaultdict(lambda: {'total': 0, 'nb': 0})
    par_statut = defaultdict(int)
    order_ids_vente = set()

    for o in orders:
        jour = (o['created_at'] or '')[:10]
        par_statut[o['status']] += 1
        if o['status'] in STATUTS_VENTE:
            par_jour[jour]['total'] += o['total'] or 0
            par_jour[jour]['nb'] += 1
            order_ids_vente.add(o['id'])

    jours_tries = sorted(par_jour.keys())

    # --- Top produits vendus (jointure order_items -> orders pour ne garder que les ventes) ---
    top_produits = defaultdict(int)
    items_result = sb.table('order_items').select('product_name, quantity, orders(status)').execute()
    for it in (items_result.data or []):
        order_info = it.get('orders')
        if order_info and order_info.get('status') in STATUTS_VENTE:
            top_produits[it['product_name']] += it['quantity']

    top_5 = sorted(top_produits.items(), key=lambda x: x[1], reverse=True)[:5]

    # --- Stock bas ---
    stock_bas = db.fetch_all(
        'products', 'name, stock',
        filters=[('stock', 'lte', 5)],
        order=('stock', True),
    )

    return {
        'ca_labels': jours_tries,
        'ca_values': [round(par_jour[j]['total']) for j in jours_tries],
        'statuts_labels': list(par_statut.keys()),
        'statuts_values': list(par_statut.values()),
        'top_produits_labels': [t[0] for t in top_5],
        'top_produits_values': [t[1] for t in top_5],
        'stock_bas': stock_bas,
        'ca_total_periode': sum(par_jour[j]['total'] for j in jours_tries),
        'nb_commandes_periode': sum(par_jour[j]['nb'] for j in jours_tries),
    }
