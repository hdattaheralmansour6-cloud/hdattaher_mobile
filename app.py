"""
HDATTAHER MOBILE - Application Flask (Supabase / PostgreSQL)
Site e-commerce de vente de téléphones et accessoires
Propriétaire : Hdattaher | Localisation : Niger
"""
import os
import io
import re
import time
import secrets
from urllib.parse import quote, urlparse
from datetime import datetime, timedelta
from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for,
                   flash, session, jsonify, send_from_directory, abort, Response)
from flask_caching import Cache
from flask_compress import Compress
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_login import (login_user, logout_user, login_required as customer_login_required,
                          current_user)
from config import Config
from database import db, verify_admin_password, get_settings_dict, get_supabase, init_supabase
from deep_translator import GoogleTranslator
from customer_auth import (login_manager, create_customer, verify_customer_password,
                            update_customer_last_login, update_customer_profile,
                            change_customer_password, generate_reset_code,
                            verify_reset_code, consume_reset_code, get_customer_by_email,
                            get_pending_reset_requests, count_pending_reset_requests)
from werkzeug.security import check_password_hash
import cart as cart_module
from order_manager import (create_order_from_cart, get_customer_orders, get_order_with_items,
                            update_order_status, get_all_orders, ORDER_STATUSES,
                            get_dashboard_stats, get_admin_overview, NEXT_STATUS)
from invoice_generator import generate_invoice_pdf
# test redeploiement storage 2
app = Flask(__name__)
app.config.from_object(Config)

# Render place un relais devant le serveur : on lit la vraie adresse IP du visiteur
# (en-tête X-Forwarded-For, un seul relais de confiance)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# --- Performance : cache mémoire + compression des réponses (Phase 6) ---
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 120  # 2 minutes
cache = Cache(app)
Compress(app)
login_manager.init_app(app)

def auto_translate(text, target):
    if not text:
        return ""

    try:
        return GoogleTranslator(source="fr", target=target).translate(text)
    except Exception:
        return text

# ===========================
# PROTECTION CSRF GLOBALE
# ============================================================
#  PROTECTION CSRF GLOBALE
# ============================================================
csrf = CSRFProtect(app)


# ============================================================
#  RATE LIMITING
# ============================================================
_login_attempts = {}


def _check_rate_limit(ip):
    if ip not in _login_attempts:
        return False, 0
    data = _login_attempts[ip]
    if data.get('locked_until') and datetime.now() < data['locked_until']:
        remaining = (data['locked_until'] - datetime.now()).seconds
        return True, remaining
    if data.get('locked_until') and datetime.now() >= data['locked_until']:
        del _login_attempts[ip]
        return False, 0
    return False, 0


def _record_failed_login(ip):
    if ip not in _login_attempts:
        _login_attempts[ip] = {'count': 0, 'locked_until': None}
    _login_attempts[ip]['count'] += 1
    if _login_attempts[ip]['count'] >= Config.LOGIN_MAX_ATTEMPTS:
        _login_attempts[ip]['locked_until'] = datetime.now() + timedelta(
            seconds=Config.LOGIN_LOCKOUT_SECONDS
        )
        return True
    return False


def _reset_login_attempts(ip):
    if ip in _login_attempts:
        del _login_attempts[ip]


# ============================================================
#  UTILITAIRES
# ============================================================

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def safe_float(value, default=0.0):
    try:
        return float(value) if value not in (None, '') else default
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    try:
        return int(float(value)) if value not in (None, '') else default
    except (ValueError, TypeError):
        return default


def login_required(f):
    """Décorateur pour protéger les routes admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Veuillez vous connecter.', 'warning')
            return redirect(url_for('admin_login'))
        login_time = session.get('login_time')
        if login_time:
            elapsed = time.time() - login_time
            if elapsed > Config.PERMANENT_SESSION_LIFETIME:
                session.clear()
                flash('Votre session a expiré. Veuillez vous reconnecter.', 'warning')
                return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


@cache.memoize(timeout=120)
def get_settings():
    return get_settings_dict()


def log_action(action, details=''):
    try:
        admin_id = session.get('user_id', None)
        ip = request.remote_addr if request else None
        db.insert('admin_logs', {
            'action': action,
            'details': details,
            'admin_id': admin_id,
            'ip_address': ip
        })
    except Exception:
        pass


@cache.memoize(timeout=120)
def get_categories_list():
    return db.fetch_all('categories', '*',
                        filters={'is_active': True},
                        order=('sort_order', True))


@app.context_processor
def inject_globals():
    settings = get_settings()
    categories = get_categories_list()
    dynamic_css = ':root {\n'
    dynamic_css += f'  --primary: {settings.get("primary_color", "#6C63FF")};\n'
    dynamic_css += f'  --secondary: {settings.get("secondary_color", "#FF6584")};\n'
    dynamic_css += f'  --accent: {settings.get("accent_color", "#00D9FF")};\n'
    dynamic_css += '}\n'
    cart_count = cart_module.cart_item_count()
    pending_reset_count = 0
    pending_orders_count = 0
    if session.get('logged_in'):
        pending_reset_count = count_pending_reset_requests()
        try:
            pending_orders_count = db.count('orders', {'status': 'En attente'})
        except Exception:
            pending_orders_count = 0
    return dict(settings=settings, categories=categories, dynamic_css=dynamic_css,
                cart_count=cart_count, pending_reset_count=pending_reset_count,
                pending_orders_count=pending_orders_count)


# ============================================================
#  SÉCURITÉ - En-têtes
# ============================================================

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    """
    Formulaire périmé (ex. ancienne page de connexion restée ouverte dans un autre onglet
    alors qu'une connexion a déjà réussi) : on revient proprement au lieu d'afficher
    une page blanche "Bad Request".
    """
    if request.endpoint == 'admin_login':
        if 'logged_in' in session:
            return redirect(url_for('admin_dashboard'))
        flash('Votre session a expiré. Veuillez réessayer.', 'warning')
        return redirect(url_for('admin_login'))

    flash('Votre session a expiré. Veuillez réessayer.', 'warning')
    ref = request.referrer
    if ref and urlparse(ref).netloc == request.host:
        return redirect(ref)
    return redirect(url_for('index'))


@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response


@app.before_request
def make_session_permanent():
    session.permanent = True


# ============================================================
#  ROUTES PUBLIQUES
# ============================================================

@app.route('/robots.txt')
def robots_txt():
    lines = [
        'User-agent: *',
        'Allow: /',
        'Disallow: /azawad/',
        'Disallow: /compte/',
        'Disallow: /panier/',
        f'Sitemap: {Config.SITE_URL}/sitemap.xml',
    ]
    return Response('\n'.join(lines), mimetype='text/plain')


@app.route('/sitemap.xml')
def sitemap_xml():
    base = Config.SITE_URL
    urls = [
        {'loc': f'{base}/', 'changefreq': 'daily', 'priority': '1.0'},
        {'loc': f'{base}/products', 'changefreq': 'daily', 'priority': '0.9'},
    ]

    products = db.fetch_all('products', 'id, updated_at', {'is_active': True})
    for p in products:
        urls.append({
            'loc': f'{base}/product/{p["id"]}',
            'lastmod': (p.get('updated_at') or '')[:10],
            'changefreq': 'weekly',
            'priority': '0.8',
        })

    xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        xml_parts.append('  <url>')
        xml_parts.append(f'    <loc>{u["loc"]}</loc>')
        if u.get('lastmod'):
            xml_parts.append(f'    <lastmod>{u["lastmod"]}</lastmod>')
        xml_parts.append(f'    <changefreq>{u["changefreq"]}</changefreq>')
        xml_parts.append(f'    <priority>{u["priority"]}</priority>')
        xml_parts.append('  </url>')
    xml_parts.append('</urlset>')

    return Response('\n'.join(xml_parts), mimetype='application/xml')


@app.route('/')
def index():
    """Page d'accueil"""
    sb = get_supabase()

    # Derniers produits
    r = sb.table('products').select('*, categories(name)') \
        .eq('is_active', True) \
        .order('created_at', desc=True).limit(8).execute()
    latest = r.data or []

    # Promotions
    r = sb.table('products').select('*, categories(name)') \
        .eq('is_active', True).gt('discount', 0) \
        .order('discount', desc=True).limit(4).execute()
    promos = r.data or []

    # Adapter le format category_name pour les templates
    for lst in [latest, promos]:
        for p in lst:
            cat = p.pop('categories', None)
            p['category_name'] = cat['name'] if cat else None

    # Stats
    total_products = db.count('products', {'is_active': True})
    all_prods = db.fetch_all('products', 'brand', {'is_active': True})
    _seen = {}
    for p in all_prods:
        b = ' '.join((p.get('brand') or '').split())
        if b and b.lower() not in _seen:
            _seen[b.lower()] = b if any(ch.isupper() for ch in b) else b.title()
    brand_names = sorted(_seen.values(), key=str.lower)
    unique_brands = len(brand_names)

    stats = {
        'total_products': total_products,
        'total_brands': unique_brands,
        'happy_clients': 1000,
    }

    banners = db.fetch_all('banners', '*', {'is_active': True}, order=('sort_order', True))

    return render_template('public/index.html', latest=latest,
                           promos=promos, stats=stats, banners=banners, brands=brand_names)


def _clean_search(text, limit=60):
    """Garde un texte de recherche sûr pour les filtres Supabase (.or_/ilike)."""
    text = re.sub(r'[,()%*\\:"\']', ' ', text or '')
    return ' '.join(text.split())[:limit]


@app.route('/products')
def products():
    """Page de tous les produits avec filtres"""
    sb = get_supabase()

    category_id = request.args.get('category', default=None, type=str)
    search = _clean_search(request.args.get('search', default='', type=str))
    min_price = request.args.get('min_price', default=None, type=float)
    max_price = request.args.get('max_price', default=None, type=float)
    brand = request.args.get('brand', default='', type=str).strip()
    sort = request.args.get('sort', default='newest', type=str)

    allowed_sorts = {'newest', 'price_asc', 'price_desc', 'popular'}
    if sort not in allowed_sorts:
        sort = 'newest'

    # Promotions cat
    promo_cat = db.fetch_one('categories', 'id', {'name': 'Promotions'})
    promo_category_id = promo_cat['id'] if promo_cat else None

    query = sb.table('products').select('*, categories(name)').eq('is_active', True)

    if category_id:
        if category_id == promo_category_id:
            query = query.gt('discount', 0)
        else:
            query = query.eq('category_id', category_id)

    if search:
        query = query.or_(
            f'name.ilike.%{search}%,brand.ilike.%{search}%,description.ilike.%{search}%'
        )

    promo_only = request.args.get('promo') == '1'
    if promo_only:
        query = query.gt('discount', 0)

    if min_price is not None:
        query = query.gte('price', min_price)
    if max_price is not None:
        query = query.lte('price', max_price)
    if brand:
        query = query.ilike('brand', re.sub(r'[%_\\]', '', brand))

    sort_map = {
        'price_asc': ('price', False),
        'price_desc': ('price', True),
        'popular': ('views', True),
        'newest': ('created_at', True),
    }
    col, desc = sort_map[sort]
    query = query.order(col, desc=desc)

    result = query.execute()
    products_list = result.data or []

    for p in products_list:
        cat = p.pop('categories', None)
        p['category_name'] = cat['name'] if cat else None
        
        if p.get('image') and not p['image'].startswith('http'):
            p['image'] = sb.storage.from_('product-images').get_public_url(p['image'])
    all_categories = db.fetch_all('categories', '*', {'is_active': True}, order=('sort_order', True))
    all_brands_rows = db.fetch_all('products', 'brand', {'is_active': True})
    _seen = {}
    for row in all_brands_rows:
        b = ' '.join((row.get('brand') or '').split())
        if b and b.lower() not in _seen:
            _seen[b.lower()] = b if any(ch.isupper() for ch in b) else b.title()
    all_brands = sorted(_seen.values(), key=str.lower)

    return render_template('public/products.html',
                           products=products_list,
                           all_categories=all_categories,
                           all_brands=all_brands,
                           current_category=category_id,
                           current_brand=brand,
                           search=search, sort=sort, promo_only=promo_only,
                           min_price=min_price, max_price=max_price)


@app.route('/product/<product_id>')
def product_detail(product_id):
    """Page détail d'un produit"""
    sb = get_supabase()
    r = sb.table('products').select('*, categories(name)').eq('id', product_id).execute()
    product = r.data[0] if r.data else None

    if not product:
        flash('Produit introuvable.', 'error')
        return redirect(url_for('products'))

    cat = product.pop('categories', None)
    product['category_name'] = cat['name'] if cat else None
    if product.get('image') and not product['image'].startswith('http'):
        product['image'] = sb.storage.from_('product-images').get_public_url(product['image'])
    # Enregistrer la vue (le trigger Postgres incrémente automatiquement views)
    ip = request.remote_addr
    ua = request.headers.get('User-Agent', '')[:200]
    try:
        db.insert('product_views', {
            'product_id': product_id,
            'ip_address': ip,
            'user_agent': ua
        })
    except Exception:
        pass

    # Produits similaires
    r2 = sb.table('products').select('*, categories(name)') \
        .eq('category_id', product['category_id']) \
        .neq('id', product_id) \
        .eq('is_active', True).limit(4).execute()
    related = r2.data or []
    for p in related:
        c = p.pop('categories', None)
        p['category_name'] = c['name'] if c else None
        if p.get('image') and not p['image'].startswith('http'):
            p['image'] = sb.storage.from_('product-images').get_public_url(p['image'])
    return render_template('public/product_detail.html', product=product, related=related)


@app.route('/about')
def about():
    return render_template('public/about.html')


@app.route('/favoris')
def favorites_page():
    """Page Favoris - rendu 100% côté client depuis localStorage (aucune donnée serveur)."""
    return render_template('public/favorites.html')


@app.route('/featured')
def featured_products():
    """Ancienne page « En vedette » (supprimée) : on renvoie vers la boutique."""
    return redirect(url_for('products'), code=301)


@app.route('/new-arrivals')
def new_arrivals():
    """Nouvelles arrivages"""
    sb = get_supabase()
    r = sb.table('products').select('*, categories(name)') \
        .eq('is_active', True).eq('is_new', True) \
        .order('created_at', desc=True).execute()
    products_list = r.data or []
    for p in products_list:
        cat = p.pop('categories', None)
        p['category_name'] = cat['name'] if cat else None
    return render_template('public/products.html',
                           products=products_list,
                           all_categories=db.fetch_all('categories', '*', {'is_active': True}, order=('sort_order', True)),
                           page_title='Nouvelles Arrivages 🆕',
                           current_category=None, search='', sort='newest',
                           min_price=None, max_price=None)


def _digits(text):
    return re.sub(r'\D', '', text or '')[-8:]


@app.route('/suivi-commande', methods=['GET', 'POST'])
def order_tracking():
    """Le client suit sa commande avec son numéro de commande + son téléphone."""
    order, items, error = None, [], None
    number = request.values.get('numero', '').strip().upper().lstrip('#')
    phone = request.values.get('telephone', '').strip()
    if request.method == 'POST':
        if not number or len(_digits(phone)) < 8:
            error = 'missing'
        else:
            try:
                rows = db.fetch_all('orders', filters={'order_number': number}, limit=1)
            except Exception:
                rows = []
            found = rows[0] if rows else None
            if found and _digits(found.get('shipping_phone')) == _digits(phone):
                order = found
                try:
                    items = db.fetch_all('order_items', filters={'order_id': found['id']}) or []
                except Exception:
                    items = []
            else:
                error = 'not_found'
    return render_template('public/order_tracking.html', order=order, items=items,
                           error=error, numero=number, telephone=phone)


@app.route('/contact')
def contact():
    """Page contact"""
    return render_template('public/contact.html')

@app.route('/api/products')
def api_products():
    search = _clean_search(request.args.get('q', ''))
    if len(search) < 2:
        return jsonify([])
    sb = get_supabase()
    try:
        r = sb.table('products').select('id, name, name_en, name_ar, brand, price, old_price, image, discount, stock') \
            .eq('is_active', True) \
            .or_(f'name.ilike.%{search}%,brand.ilike.%{search}%') \
            .order('views', desc=True).limit(12).execute()
        rows = r.data or []
    except Exception:
        rows = []
    for p in rows:
        img = p.get('image')
        if not img or img == 'default.png':
            p['image'] = ''
        elif not img.startswith('http'):
            p['image'] = sb.storage.from_('product-images').get_public_url(img)
    return jsonify(rows)


# ============================================================
#  ROUTES ADMIN
# ============================================================

@app.route('/azawad', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'GET' and 'logged_in' in session:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        ip = request.remote_addr

        is_blocked, remaining = _check_rate_limit(ip)
        if is_blocked:
            minutes = remaining // 60
            seconds = remaining % 60
            flash(f'Trop de tentatives. Réessayez dans {minutes}m {seconds}s.', 'error')
            log_action('Tentative login bloquée', f'IP: {ip}')
            return render_template('admin/login.html')

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Veuillez remplir tous les champs.', 'error')
            return render_template('admin/login.html')

        # Vérifier via RPC Supabase (bcrypt côté serveur)
        admin = verify_admin_password(username, password)

        if admin:
            _reset_login_attempts(ip)
            db.update('admins', {'last_login': datetime.utcnow().isoformat()},
                      {'id': admin['id']})

            session.clear()
            session['logged_in'] = True
            session['user_id'] = admin['id']
            session['username'] = admin['username']
            session['login_time'] = time.time()
            session.permanent = True

            log_action('Connexion réussie', f'IP: {ip}')
            flash('Connexion réussie!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            blocked = _record_failed_login(ip)
            attempts_left = Config.LOGIN_MAX_ATTEMPTS - _login_attempts.get(ip, {}).get('count', 0)

            if blocked:
                flash(f'Compte bloqué pour {Config.LOGIN_LOCKOUT_SECONDS // 60} minutes.', 'error')
                log_action('Compte bloqué', f'IP: {ip}, Utilisateur: {username}')
            else:
                flash(f'Identifiants incorrects. {max(0, attempts_left)} tentative(s) restante(s).', 'error')
                log_action('Tentative échouée', f'IP: {ip}, Utilisateur: {username}')

    return render_template('admin/login.html')


@app.route('/azawad/logout')
def admin_logout():
    username = session.get('username', 'inconnu')
    log_action('Déconnexion', f'Utilisateur: {username}')
    session.clear()
    flash('Déconnexion réussie.', 'info')
    return redirect(url_for('admin_login'))


@app.route('/admin')
@login_required
def admin_dashboard():
    sb = get_supabase()
    stats = {
        'total_products': db.count('products'),
        'active_products': db.count('products', {'is_active': True}),
        'total_views': sum((p.get('views') or 0) for p in db.fetch_all('products', 'views')),
        'out_of_stock': db.count('products', {'stock': 0}),
        'total_categories': db.count('categories'),
        'promo_products': len(db.fetch_all('products', 'id', [('discount', 'gt', 0)])),
    }
    # Low stock
    low = sb.table('products').select('id', count='exact').gt('stock', 0).lte('stock', 5).execute()
    stats['low_stock'] = low.count if low.count else 0

    recent = db.fetch_all('products', '*, categories(name)', order=('created_at', False), limit=5)
    for p in recent:
        c = p.pop('categories', None)
        p['category_name'] = c['name'] if c else None

    top_viewed = db.fetch_all('products', '*', order=('views', False), limit=5)

    periode = request.args.get('periode', 30, type=int)
    if periode not in (7, 30, 90):
        periode = 30
    order_stats = get_dashboard_stats(days=periode)
    overview = get_admin_overview()
    try:
        recent_orders = get_all_orders()[:6]
    except Exception:
        recent_orders = []

    return render_template('admin/dashboard.html', stats=stats, recent=recent, top_viewed=top_viewed,
                            order_stats=order_stats, periode=periode, overview=overview,
                            recent_orders=recent_orders, next_status=NEXT_STATUS)


@app.route('/azawad/profile', methods=['GET', 'POST'])
@login_required
def admin_profile():
    """Page Mon Profil — modifier username / mot de passe"""
    admin_id = session.get('user_id')
    admin = db.fetch_one('admins', 'id, username, email, created_at', {'id': admin_id})

    if not admin:
        flash('Erreur: admin introuvable.', 'error')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        action = request.form.get('action', '')
        sb = get_supabase()

        # ── Changer le nom d'utilisateur ──
        if action == 'change_username':
            new_username = request.form.get('new_username', '').strip()
            confirm_password = request.form.get('confirm_password', '')

            if not new_username:
                flash('Le nom d\'utilisateur ne peut pas être vide.', 'error')
                return render_template('admin/profile.html', admin=admin)

            if len(new_username) < 3:
                flash('Le nom d\'utilisateur doit contenir au moins 3 caractères.', 'error')
                return render_template('admin/profile.html', admin=admin)

            # Vérifier le mot de passe via RPC
            verified = verify_admin_password(admin['username'], confirm_password)
            if not verified:
                flash('Mot de passe incorrect.', 'error')
                return render_template('admin/profile.html', admin=admin)

            # Vérifier que le nouveau username n'est pas déjà pris
            existing = db.fetch_one('admins', 'id', {'username': new_username})
            if existing and str(existing['id']) != str(admin_id):
                flash('Ce nom d\'utilisateur est déjà utilisé.', 'error')
                return render_template('admin/profile.html', admin=admin)

            # Mettre à jour le username
            db.update('admins', {'username': new_username}, {'id': admin_id})
            session['username'] = new_username
            log_action('Modification username', f'Ancien: {admin["username"]} → Nouveau: {new_username}')
            flash('Nom d\'utilisateur modifié avec succès!', 'success')

            # Rafraîchir les données admin
            admin = db.fetch_one('admins', 'id, username, email, created_at', {'id': admin_id})

        # ── Changer le mot de passe ──
        elif action == 'change_password':
            old_password = request.form.get('old_password', '')
            new_password = request.form.get('new_password', '')
            confirm_new = request.form.get('confirm_new_password', '')

            if not old_password or not new_password or not confirm_new:
                flash('Tous les champs sont obligatoires.', 'error')
                return render_template('admin/profile.html', admin=admin)

            if len(new_password) < 6:
                flash('Le nouveau mot de passe doit contenir au moins 6 caractères.', 'error')
                return render_template('admin/profile.html', admin=admin)

            if new_password != confirm_new:
                flash('Les nouveaux mots de passe ne correspondent pas.', 'error')
                return render_template('admin/profile.html', admin=admin)

            # Utiliser la RPC change_admin_password (bcrypt côté serveur)
            try:
                result = sb.rpc('change_admin_password', {
                    'p_admin_id': admin_id,
                    'p_old_password': old_password,
                    'p_new_password': new_password
                }).execute()

                if result.data is True or result.data == True:
                    log_action('Changement mot de passe', f'Utilisateur: {admin["username"]}')
                    session.clear()
                    flash('Mot de passe modifié avec succès! Veuillez vous reconnecter.', 'success')
                    return redirect(url_for('admin_login'))
                else:
                    flash('Ancien mot de passe incorrect.', 'error')
            except Exception as e:
                flash('Erreur lors du changement de mot de passe.', 'error')

    return render_template('admin/profile.html', admin=admin)


@app.route('/azawad/products')
@login_required
def admin_products():
    products_list = db.fetch_all('products', '*, categories(name)', order=('created_at', False))
    for p in products_list:
        c = p.pop('categories', None)
        p['category_name'] = c['name'] if c else None
    counts = {
        'all': len(products_list),
        'active': sum(1 for p in products_list if p.get('is_active')),
        'hidden': sum(1 for p in products_list if not p.get('is_active')),
        'out': sum(1 for p in products_list if (p.get('stock') or 0) == 0),
        'low': sum(1 for p in products_list if 0 < (p.get('stock') or 0) <= 5),
        'promo': sum(1 for p in products_list if (p.get('discount') or 0) > 0),
    }
    return render_template('admin/products.html', products=products_list, counts=counts,
                           filtre=request.args.get('filtre', 'all'))


def _wants_json():
    return request.headers.get('X-Requested-With') == 'fetch'


@app.route('/azawad/product/stock/<product_id>', methods=['POST'])
@login_required
def admin_product_stock(product_id):
    """Change le stock en un clic (+1 / -1) ou à une valeur précise."""
    product = db.fetch_one('products', 'id, name, stock', {'id': product_id})
    if not product:
        return (jsonify(ok=False, error='introuvable'), 404) if _wants_json() else redirect(url_for('admin_products'))
    if request.form.get('value', '') != '':
        new_stock = safe_int(request.form.get('value'), product.get('stock') or 0)
    else:
        new_stock = (product.get('stock') or 0) + safe_int(request.form.get('delta'), 0)
    new_stock = max(0, min(new_stock, 100000))
    db.update('products', {'stock': new_stock}, {'id': product_id})
    log_action('Stock modifié', f"{product['name']} : {product.get('stock') or 0} -> {new_stock}")
    if _wants_json():
        return jsonify(ok=True, stock=new_stock)
    return redirect(request.referrer or url_for('admin_products'))


@app.route('/azawad/product/visible/<product_id>', methods=['POST'])
@login_required
def admin_product_toggle(product_id):
    """Affiche / masque un produit sur le site en un clic."""
    product = db.fetch_one('products', 'id, name, is_active', {'id': product_id})
    if not product:
        return (jsonify(ok=False, error='introuvable'), 404) if _wants_json() else redirect(url_for('admin_products'))
    new_state = not bool(product.get('is_active'))
    db.update('products', {'is_active': new_state}, {'id': product_id})
    log_action('Produit ' + ('affiché' if new_state else 'masqué'), product['name'])
    if _wants_json():
        return jsonify(ok=True, active=new_state)
    flash(('Produit visible sur le site.' if new_state else 'Produit masqué du site.'), 'success')
    return redirect(request.referrer or url_for('admin_products'))


@app.route('/azawad/product/dupliquer/<product_id>', methods=['POST'])
@login_required
def admin_product_duplicate(product_id):
    """Crée une copie (masquée) d'un produit puis ouvre sa fiche pour la modifier."""
    product = db.fetch_one('products', '*', {'id': product_id})
    if not product:
        flash('Produit introuvable.', 'error')
        return redirect(url_for('admin_products'))
    copy = {k: v for k, v in product.items()
            if k not in ('id', 'created_at', 'updated_at', 'views', 'categories')}
    copy['name'] = (product.get('name') or 'Produit') + ' (copie)'
    copy['is_active'] = False
    copy['views'] = 0
    rows = db.insert('products', copy)
    new = rows[0] if isinstance(rows, list) and rows else rows
    log_action('Produit dupliqué', product.get('name') or '')
    flash('Copie créée (masquée du site). Modifiez-la puis rendez-la visible.', 'success')
    if new and new.get('id'):
        return redirect(url_for('admin_edit_product', product_id=new['id']))
    return redirect(url_for('admin_products'))


# ============================================================
#  MARQUES (liste à choisir dans l'admin, même orthographe partout)
# ============================================================
KNOWN_BRANDS = ['Apple', 'Samsung', 'Tecno', 'Infinix', 'Itel', 'Xiaomi', 'Redmi', 'Huawei',
                'Honor', 'Oppo', 'Realme', 'Vivo', 'Google', 'Nokia', 'OnePlus', 'Motorola', 'Oraimo', 'Anker']


def _brand_choices():
    """Marques connues + marques déjà utilisées sur les produits (sans doublon majuscule/minuscule)."""
    choices = {b.lower(): b for b in KNOWN_BRANDS}
    try:
        for row in db.fetch_all('products', 'brand') or []:
            b = ' '.join((row.get('brand') or '').split())
            if b and b.lower() not in choices:
                choices[b.lower()] = b
    except Exception:
        pass
    return sorted(choices.values(), key=str.lower)


def _brand_from_form():
    """Lit la marque choisie (ou « Autre ») et l'écrit toujours de la même façon."""
    raw = request.form.get('brand', '')
    if raw == '__other__':
        raw = request.form.get('brand_other', '')
    raw = ' '.join((raw or '').split())[:40]
    if not raw:
        return ''
    for b in _brand_choices():
        if b.lower() == raw.lower():
            return b
    return raw if any(c.isupper() for c in raw) else raw.title()


def _upload_product_image(file):
    """
    Envoie la photo d'un produit sur Supabase Storage et retourne son URL publique (ou None).
    La photo est redressée (iPhone), réduite à 1400 px maximum et allégée en WEBP.
    """
    if not file or not file.filename or not allowed_file(file.filename):
        return None
    data = file.read()
    if not data:
        return None
    content_type, ext = (file.content_type or 'image/jpeg'), None
    try:
        from PIL import Image, ImageOps
        img = Image.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img)
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGBA' if 'A' in img.getbands() else 'RGB')
        img.thumbnail((1400, 1400), Image.LANCZOS)
        out = io.BytesIO()
        img.save(out, 'WEBP', quality=86, method=4)
        data, content_type, ext = out.getvalue(), 'image/webp', 'webp'
    except Exception:
        ext = (file.filename.rsplit('.', 1)[-1] or 'jpg').lower()
    storage_filename = f"{int(time.time())}_{secrets.token_hex(5)}.{ext}"
    sb = get_supabase()
    sb.storage.from_('product-images').upload(
        storage_filename, data, {'content-type': content_type, 'upsert': 'true'})
    return sb.storage.from_('product-images').get_public_url(storage_filename)


def _prices_from_form():
    """Prix, ancien prix et réduction cohérents (réduction calculée depuis l'ancien prix)."""
    price = max(0, safe_float(request.form.get('price'), 0))
    old_price = max(0, safe_float(request.form.get('old_price'), 0))
    discount = max(0, min(99, safe_int(request.form.get('discount'), 0)))
    if old_price > price > 0:
        discount = int(round((old_price - price) / old_price * 100))
    elif old_price and old_price <= price:
        old_price, discount = 0, 0
    return price, old_price, discount


@app.route('/azawad/product/add', methods=['GET', 'POST'])
@login_required
def admin_add_product():
    cats = db.fetch_all('categories', '*', order=('sort_order', True))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        
        name_en = auto_translate(name, "en")
        name_ar = auto_translate(name, "ar")

        description = request.form.get("description", "").strip()
        description_en = auto_translate(description, "en")
        description_ar = auto_translate(description, "ar")

        if not name:
            flash('Le nom du produit est obligatoire.', 'error')
            return render_template('admin/product_form.html', product=None, categories=cats, action='add', brands=_brand_choices())

        image_filename = _upload_product_image(request.files.get('image')) or 'default.png'
        price, old_price, discount = _prices_from_form()

        db.insert('products', {
            'name': name,
            'name_en': name_en,
            'name_ar': name_ar,
            'description': description,
            'description_en': description_en,
            'description_ar': description_ar,
            'price': price,
            'old_price': old_price,
            'discount': discount,
            'stock': safe_int(request.form.get('stock'), 0),
            'category_id': request.form.get('category_id'),
            'image': image_filename,
            'brand': _brand_from_form(),
            'is_new': bool(request.form.get('is_new')),
        })
        log_action('Ajout produit', f'Produit: {name}')
        flash('Produit ajouté avec succès!', 'success')
        return redirect(url_for('admin_products'))

    return render_template('admin/product_form.html', product=None, categories=cats, action='add', brands=_brand_choices())


@app.route('/azawad/product/edit/<product_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_product(product_id):
    product = db.fetch_one('products', '*', {'id': product_id})
    cats = db.fetch_all('categories', '*', order=('sort_order', True))

    if not product:
        flash('Produit introuvable.', 'error')
        return redirect(url_for('admin_products'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        
        description = request.form.get("description", "").strip()

        name_en = auto_translate(name, "en")
        name_ar = auto_translate(name, "ar")

        description_en = auto_translate(description, "en")
        description_ar = auto_translate(description, "ar")
        
        if not name:
            flash('Le nom est obligatoire.', 'error')
            return render_template('admin/product_form.html', product=product, categories=cats, action='edit', brands=_brand_choices())

        image_filename = _upload_product_image(request.files.get('image')) or product['image']
        price, old_price, discount = _prices_from_form()

        db.update('products', {
            'name': name,
            'name_en': name_en,
            'name_ar': name_ar,
            'description': description,
            'description_en': description_en,
            'description_ar': description_ar,
            'price': price,
            'old_price': old_price,
            'discount': discount,
            'stock': safe_int(request.form.get('stock'), 0),
            'category_id': request.form.get('category_id'),
            'image': image_filename,
            'brand': _brand_from_form(),
            'is_new': bool(request.form.get('is_new')),
            'is_active': bool(request.form.get('is_active')),
        }, {'id': product_id})
        log_action('Modification produit', f'Produit: {name}')
        flash('Produit modifié avec succès!', 'success')
        return redirect(url_for('admin_products'))

    return render_template('admin/product_form.html', product=product, categories=cats, action='edit', brands=_brand_choices())


@app.route('/azawad/product/delete/<product_id>', methods=['POST'])
@login_required
def admin_delete_product(product_id):
    confirmed = request.form.get('confirmed', '')
    if confirmed != 'yes':
        flash('Confirmation requise.', 'error')
        return redirect(url_for('admin_products'))

    product = db.fetch_one('products', 'name', {'id': product_id})
    if not product:
        flash('Produit introuvable.', 'error')
        return redirect(url_for('admin_products'))

    product_name = product['name']
    db.delete('products', {'id': product_id})
    log_action('Suppression produit', f'Produit: {product_name}')
    flash('Produit supprimé.', 'success')
    return redirect(url_for('admin_products'))


# ============================================================
#  BANNIÈRES DU CARROUSEL (page d'accueil)
# ============================================================

@app.route('/azawad/banners')
@login_required
def admin_banners():
    banners = db.fetch_all('banners', '*', order=('sort_order', True))
    return render_template('admin/banners.html', banners=banners)


@app.route('/azawad/banner/add', methods=['GET', 'POST'])
@login_required
def admin_add_banner():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        subtitle = request.form.get('subtitle', '').strip()
        # Traduction automatique FR -> EN/AR (comme pour les produits)
        title_en = auto_translate(title, 'en')
        title_ar = auto_translate(title, 'ar')
        subtitle_en = auto_translate(subtitle, 'en')
        subtitle_ar = auto_translate(subtitle, 'ar')
        sort_order = safe_int(request.form.get('sort_order'), 0)
        is_active = bool(request.form.get('is_active'))

        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                if filename:
                    timestamp = str(int(time.time()))
                    storage_filename = f"{timestamp}_{filename}"
                    file_bytes = file.read()
                    sb = get_supabase()
                    sb.storage.from_('product-images').upload(
                        storage_filename, file_bytes,
                        {'content-type': file.content_type, 'upsert': 'true'}
                    )
                    image_filename = sb.storage.from_('product-images').get_public_url(storage_filename)

        if not image_filename:
            flash("Une image est obligatoire pour une bannière.", 'error')
            return render_template('admin/banner_form.html', banner=None, action='add')

        db.insert('banners', {
            'title': title,
            'subtitle': subtitle,
            'title_en': title_en or None,
            'title_ar': title_ar or None,
            'subtitle_en': subtitle_en or None,
            'subtitle_ar': subtitle_ar or None,
            'link_url': None,
            'image': image_filename,
            'sort_order': sort_order,
            'is_active': is_active,
        })
        log_action('Ajout bannière', f'Titre: {title or "(sans titre)"}')
        flash('Bannière ajoutée avec succès !', 'success')
        return redirect(url_for('admin_banners'))

    return render_template('admin/banner_form.html', banner=None, action='add')


@app.route('/azawad/banner/edit/<banner_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_banner(banner_id):
    banner = db.fetch_one('banners', '*', {'id': banner_id})
    if not banner:
        flash('Bannière introuvable.', 'error')
        return redirect(url_for('admin_banners'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        subtitle = request.form.get('subtitle', '').strip()
        # Traduction automatique FR -> EN/AR (comme pour les produits)
        title_en = auto_translate(title, 'en')
        title_ar = auto_translate(title, 'ar')
        subtitle_en = auto_translate(subtitle, 'en')
        subtitle_ar = auto_translate(subtitle, 'ar')
        sort_order = safe_int(request.form.get('sort_order'), 0)
        is_active = bool(request.form.get('is_active'))

        image_filename = banner['image']
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                if filename:
                    timestamp = str(int(time.time()))
                    storage_filename = f"{timestamp}_{filename}"
                    file_bytes = file.read()
                    sb = get_supabase()
                    sb.storage.from_('product-images').upload(
                        storage_filename, file_bytes,
                        {'content-type': file.content_type, 'upsert': 'true'}
                    )
                    image_filename = sb.storage.from_('product-images').get_public_url(storage_filename)

        db.update('banners', {
            'title': title,
            'subtitle': subtitle,
            'title_en': title_en or None,
            'title_ar': title_ar or None,
            'subtitle_en': subtitle_en or None,
            'subtitle_ar': subtitle_ar or None,
            'link_url': None,
            'image': image_filename,
            'sort_order': sort_order,
            'is_active': is_active,
        }, {'id': banner_id})
        log_action('Modification bannière', f'Titre: {title or "(sans titre)"}')
        flash('Bannière modifiée avec succès !', 'success')
        return redirect(url_for('admin_banners'))

    return render_template('admin/banner_form.html', banner=banner, action='edit')


@app.route('/azawad/banner/delete/<banner_id>', methods=['POST'])
@login_required
def admin_delete_banner(banner_id):
    banner = db.fetch_one('banners', '*', {'id': banner_id})
    if not banner:
        flash('Bannière introuvable.', 'error')
        return redirect(url_for('admin_banners'))

    db.delete('banners', {'id': banner_id})
    log_action('Suppression bannière', f'Titre: {banner.get("title") or "(sans titre)"}')
    flash('Bannière supprimée.', 'success')
    return redirect(url_for('admin_banners'))


@app.route('/azawad/categories')
@login_required
def admin_categories():
    cats = db.fetch_all('categories', '*', order=('sort_order', True))
    return render_template('admin/categories.html', cats=cats)


@app.route('/azawad/category/add', methods=['POST'])
@login_required
def admin_add_category():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Nom obligatoire.', 'error')
        return redirect(url_for('admin_categories'))

    try:
        db.insert('categories', {
            'name': name,
            'name_en': auto_translate(name, 'en'),
            'name_ar': auto_translate(name, 'ar'),
            'icon': request.form.get('icon', 'fas fa-box'),
        })
        log_action('Ajout catégorie', f'Catégorie: {name}')
        cache.delete_memoized(get_categories_list)
        flash('Catégorie ajoutée!', 'success')
    except Exception:
        flash('Erreur: catégorie existe déjà.', 'error')
    return redirect(url_for('admin_categories'))


@app.route('/azawad/category/delete/<cat_id>', methods=['POST'])
@login_required
def admin_delete_category(cat_id):
    cat = db.fetch_one('categories', 'name', {'id': cat_id})
    cat_name = cat['name'] if cat else 'Inconnue'
    db.delete('categories', {'id': cat_id})
    log_action('Suppression catégorie', f'Catégorie: {cat_name}')
    cache.delete_memoized(get_categories_list)
    flash('Catégorie supprimée.', 'success')
    return redirect(url_for('admin_categories'))


@app.route('/azawad/reinitialisations')
@login_required
def admin_reset_requests():
    requests_list = get_pending_reset_requests()
    return render_template('admin/reset_requests.html', requests=requests_list)


# ============================================================
#  ADMINISTRATION DES CLIENTS
# ============================================================

@app.route('/azawad/clients')
@login_required
def admin_customers():
    customers = db.fetch_all('customers', order=('created_at', False)) or []
    # Nombre de commandes par client
    order_counts = {}
    try:
        for o in (db.fetch_all('orders', columns='customer_id') or []):
            cid = o.get('customer_id')
            if cid:
                order_counts[str(cid)] = order_counts.get(str(cid), 0) + 1
    except Exception:
        pass
    return render_template('admin/customers.html', customers=customers, order_counts=order_counts)


@app.route('/azawad/client/bloquer/<customer_id>', methods=['POST'])
@login_required
def admin_toggle_customer_block(customer_id):
    customer = db.fetch_one('customers', 'full_name, email, is_blocked', {'id': customer_id})
    if not customer:
        flash('Client introuvable.', 'error')
        return redirect(url_for('admin_customers'))

    new_state = not customer.get('is_blocked')
    db.update('customers', {'is_blocked': new_state}, {'id': customer_id})

    if new_state:
        log_action('Blocage client', f"{customer.get('full_name')} ({customer.get('email')})")
        flash(f"Compte de {customer.get('full_name')} bloqué. Il ne peut plus se connecter.", 'success')
    else:
        log_action('Déblocage client', f"{customer.get('full_name')} ({customer.get('email')})")
        flash(f"Compte de {customer.get('full_name')} débloqué. Le message pour le client est copié — collez-le dans WhatsApp.", 'success')
    return redirect(url_for('admin_customers'))


@app.route('/azawad/reinitialisations/traiter/<request_id>', methods=['POST'])
@login_required
def admin_resolve_reset_request(request_id):
    db.update('password_resets', {'dismissed': True}, {'id': request_id})
    log_action('Code de réinitialisation marqué traité', f'ID: {request_id}')
    if _wants_json():
        return jsonify(ok=True)
    flash('Demande marquée comme traitée.', 'success')
    return redirect(url_for('admin_reset_requests'))


@app.route('/azawad/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if request.method == 'POST':
        fields = ['owner_name', 'whatsapp', 'location',
                  'primary_color', 'secondary_color', 'accent_color',
                  'about_title', 'about_text',
                  'facebook', 'instagram', 'tiktok']

        for field in fields:
            value = request.form.get(field, '')
            db.upsert('settings', {'key': field, 'value': value}, on_conflict='key')

        # Traduction automatique FR -> EN/AR du titre et du texte À propos
        for field in ['about_title', 'about_text']:
            value = request.form.get(field, '').strip()
            db.upsert('settings', {'key': f'{field}_en', 'value': auto_translate(value, 'en')}, on_conflict='key')
            db.upsert('settings', {'key': f'{field}_ar', 'value': auto_translate(value, 'ar')}, on_conflict='key')

        dark_mode = '1' if request.form.get('dark_mode') else '0'
        db.upsert('settings', {'key': 'dark_mode', 'value': dark_mode}, on_conflict='key')

        # Upload image de la page À propos (stockée sur Supabase Storage)
        if 'about_image' in request.files:
            about_file = request.files['about_image']
            if about_file and about_file.filename and allowed_file(about_file.filename):
                filename = secure_filename(about_file.filename)
                if filename:
                    storage_filename = f"about_{int(time.time())}_{filename}"
                    file_bytes = about_file.read()
                    sb = get_supabase()
                    sb.storage.from_('product-images').upload(
                        storage_filename, file_bytes,
                        {'content-type': about_file.content_type, 'upsert': 'true'}
                    )
                    about_url = sb.storage.from_('product-images').get_public_url(storage_filename)
                    db.upsert('settings', {'key': 'about_image', 'value': about_url}, on_conflict='key')

        log_action('Modification paramètres', 'Paramètres mis à jour')
        cache.delete_memoized(get_settings)
        flash('Paramètres sauvegardés!', 'success')
        return redirect(url_for('admin_settings'))

    return render_template('admin/settings.html')


@app.route('/azawad/logs')
@login_required
def admin_logs():
    sb = get_supabase()
    result = sb.table('admin_logs').select('*, admins(username)') \
        .order('created_at', desc=True).limit(100).execute()
    logs = result.data or []

    for log in logs:
        admin = log.pop('admins', None)
        log['username'] = admin['username'] if admin else None

    return render_template('admin/logs.html', logs=logs)


# ============================================================
#  FICHIERS STATIQUES UPLOADS
# ============================================================

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    filename = secure_filename(filename)
    if not filename:
        abort(404)
    return send_from_directory(Config.UPLOAD_FOLDER, filename)


# ============================================================
#  PANIER
# ============================================================

@app.route('/panier')
def cart_view():
    items, total = cart_module.get_cart_details()
    return render_template('public/cart.html', items=items, total=total)


@app.route('/panier/ajouter/<product_id>', methods=['POST'])
def cart_add(product_id):
    quantity = request.form.get('quantity', 1, type=int) or 1
    quantity = max(1, min(quantity, 20))
    cart_module.add_to_cart(product_id, quantity)
    if request.headers.get('X-Requested-With') == 'fetch':
        return jsonify(ok=True, count=cart_module.cart_item_count())
    flash('Produit ajouté au panier.', 'success')
    ref = request.referrer or ''
    if not ref or urlparse(ref).netloc not in ('', request.host):
        ref = url_for('products')
    return redirect(ref)


@app.route('/panier/modifier/<product_id>', methods=['POST'])
def cart_update(product_id):
    quantity = request.form.get('quantity', 1, type=int) or 0
    cart_module.update_quantity(product_id, quantity)
    return redirect(url_for('cart_view'))


@app.route('/panier/supprimer/<product_id>', methods=['POST'])
def cart_remove(product_id):
    cart_module.remove_from_cart(product_id)
    flash('Produit retiré du panier.', 'info')
    return redirect(url_for('cart_view'))


# ============================================================
#  VALIDATION DE COMMANDE
# ============================================================

def _save_payment_proof(file, customer_id):
    """
    Vérifie que le fichier est bien une image puis la range sur Supabase Storage.
    Retourne (url, erreur).
    """
    if not file or not file.filename:
        return None, "Veuillez joindre la capture d'écran du reçu de paiement."
    if not allowed_file(file.filename):
        return None, "Le reçu doit être une image (png, jpg, jpeg, webp)."
    data = file.read()
    if not data:
        return None, "Le fichier du reçu est vide."
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(data))
        fmt = (img.format or '').lower()
        img.verify()
    except Exception:
        return None, "Le fichier du reçu n'est pas une image valide."
    ext = {'jpeg': 'jpg', 'png': 'png', 'webp': 'webp', 'gif': 'gif'}.get(fmt)
    if not ext:
        return None, "Format d'image non accepté (png, jpg, jpeg, webp)."
    storage_filename = f"receipts/{int(time.time())}_{secrets.token_hex(8)}.{ext}"
    try:
        sb = get_supabase()
        sb.storage.from_('product-images').upload(
            storage_filename, data,
            {'content-type': f'image/{"jpeg" if ext == "jpg" else ext}'}
        )
        return sb.storage.from_('product-images').get_public_url(storage_filename), None
    except Exception:
        return None, "Impossible d'envoyer le reçu pour le moment. Veuillez réessayer."


@app.route('/commande/valider', methods=['GET', 'POST'])
@customer_login_required
def checkout():
    items, total = cart_module.get_cart_details()
    if not items:
        flash('Votre panier est vide.', 'error')
        return redirect(url_for('cart_view'))

    rows = db.fetch_all('customers', filters={'id': current_user.id}, limit=1)
    customer = rows[0] if rows else {}

    def _render(**extra):
        return render_template('public/checkout.html', items=items, total=total, customer=customer,
                               payment_number=Config.PAYMENT_NUMBER,
                               payment_methods=Config.PAYMENT_METHODS, **extra)

    if request.method == 'POST':
        shipping_name = request.form.get('shipping_name', '').strip()
        shipping_phone = request.form.get('shipping_phone', '').strip()
        shipping_address = request.form.get('shipping_address', '').strip()
        notes = request.form.get('notes', '').strip()
        payment_method = request.form.get('payment_method', '').strip()

        # On garde ce que le client a saisi si une erreur survient
        customer = dict(customer or {})
        customer.update({'full_name': shipping_name, 'phone': shipping_phone, 'address': shipping_address})

        if not shipping_name or not shipping_phone or not shipping_address:
            flash('Veuillez remplir toutes les informations de livraison.', 'error')
            return _render(selected_method=payment_method, notes=notes)

        if payment_method not in Config.PAYMENT_METHODS:
            flash('Veuillez choisir un moyen de paiement (Amanata ou Nita).', 'error')
            return _render(notes=notes)

        proof_url, proof_error = _save_payment_proof(request.files.get('payment_proof'), current_user.id)
        if proof_error:
            flash(proof_error, 'error')
            return _render(selected_method=payment_method, notes=notes)

        order, error = create_order_from_cart(
            current_user.id, items, shipping_name, shipping_phone, shipping_address, notes,
            payment_method=payment_method, payment_proof=proof_url
        )

        if error:
            flash(error, 'error')
            return _render(selected_method=payment_method, notes=notes)

        cart_module.clear_cart()
        log_action('Nouvelle commande', f'N° {order["order_number"]} - Client: {current_user.email} - Paiement {payment_method}')
        flash(f'Commande {order["order_number"]} enregistrée avec succès !', 'success')
        return redirect(url_for('order_confirmation', order_id=order['id']))

    return _render()


@app.route('/commande/confirmation/<order_id>')
@customer_login_required
def order_confirmation(order_id):
    order, items = get_order_with_items(order_id)
    if not order or str(order.get('customer_id')) != str(current_user.id):
        flash('Commande introuvable.', 'error')
        return redirect(url_for('index'))
    return render_template('public/order_confirmation.html', order=order, items=items)


# ============================================================
#  ADMINISTRATION DES COMMANDES
# ============================================================

@app.route('/azawad/commandes')
def admin_orders():
    if 'logged_in' not in session:
        return redirect(url_for('admin_login'))
    status_filter = request.args.get('status', '')
    if status_filter not in ORDER_STATUSES:
        status_filter = ''
    all_orders = get_all_orders()
    counts = {s: 0 for s in ORDER_STATUSES}
    for o in all_orders:
        counts[o.get('status')] = counts.get(o.get('status'), 0) + 1
    orders = [o for o in all_orders if not status_filter or o.get('status') == status_filter]
    return render_template('admin/orders.html', orders=orders, statuses=ORDER_STATUSES,
                            status_filter=status_filter, counts=counts, total_count=len(all_orders),
                            next_status=NEXT_STATUS)


@app.route('/azawad/commande/<order_id>')
def admin_order_detail(order_id):
    if 'logged_in' not in session:
        return redirect(url_for('admin_login'))
    order, items = get_order_with_items(order_id)
    if not order:
        flash('Commande introuvable.', 'error')
        return redirect(url_for('admin_orders'))
    customer = None
    if order.get('customer_id'):
        rows = db.fetch_all('customers', filters={'id': order['customer_id']}, limit=1)
        customer = rows[0] if rows else None
    return render_template('admin/order_detail.html', order=order, items=items,
                           statuses=ORDER_STATUSES, customer=customer, next_status=NEXT_STATUS)


@app.route('/azawad/commande/statut/<order_id>', methods=['POST'])
def admin_update_order_status(order_id):
    if 'logged_in' not in session:
        return redirect(url_for('admin_login'))
    new_status = request.form.get('status', '')
    if update_order_status(order_id, new_status):
        log_action('Statut commande modifié', f'Commande: {order_id} -> {new_status}')
        if new_status == 'Annulée':
            flash('Commande annulée. Le stock des produits a été remis automatiquement.', 'success')
        else:
            flash(f'Commande passée en « {new_status} ».', 'success')
    else:
        flash('Statut invalide.', 'error')
    return redirect(request.referrer or url_for('admin_orders'))


@app.route('/azawad/commande/facture/<order_id>')
def admin_order_invoice(order_id):
    if 'logged_in' not in session:
        return redirect(url_for('admin_login'))
    order, items = get_order_with_items(order_id)
    if not order:
        flash('Commande introuvable.', 'error')
        return redirect(url_for('admin_orders'))

    # Récupérer le nom du client pour l'affichage sur la facture
    customer = db.fetch_one('customers', 'full_name, email', {'id': order.get('customer_id')})
    order['customer_name'] = customer['full_name'] if customer else 'Client supprimé'

    pdf_bytes = generate_invoice_pdf(order, items, get_settings())
    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename=facture-{order["order_number"]}.pdf'}
    )


# ============================================================
#  COMPTES CLIENTS (Flask-Login)
# ============================================================

@app.route('/compte/inscription', methods=['GET', 'POST'])
def customer_register():
    if current_user.is_authenticated:
        return redirect(url_for('customer_profile'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not full_name or not email or not password:
            flash('Veuillez remplir tous les champs obligatoires.', 'error')
            return render_template('public/account/register.html')

        if password != confirm:
            flash('Les mots de passe ne correspondent pas.', 'error')
            return render_template('public/account/register.html')

        if len(password) < 6:
            flash('Le mot de passe doit contenir au moins 6 caractères.', 'error')
            return render_template('public/account/register.html')

        customer, error = create_customer(full_name, email, phone, password)
        if error:
            flash(error, 'error')
            return render_template('public/account/register.html')

        login_user(customer)
        update_customer_last_login(customer.id)
        flash('Bienvenue ! Votre compte a été créé.', 'success')
        return redirect(url_for('customer_profile'))

    return render_template('public/account/register.html')


@app.route('/compte/connexion', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'GET' and current_user.is_authenticated:
        return redirect(url_for('customer_profile'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        row = verify_customer_password(email, password)
        if row:
            if row.get('is_blocked'):
                # Compte bloqué par l'admin : pas de connexion, on propose
                # de demander de l'aide sur WhatsApp avec un message pré-rempli.
                settings = get_settings()
                whatsapp_number = settings.get('whatsapp', '22791720755')
                message = quote(
                    f"Bonjour, je n'arrive pas à me connecter à mon compte HDATTAHER MOBILE. "
                    f"Nom : {row.get('full_name', '')}, Email : {email}. Pouvez-vous m'aider ?"
                )
                wa_help_link = f"https://wa.me/{whatsapp_number}?text={message}"
                return render_template('public/account/login.html', blocked=True,
                                       wa_help_link=wa_help_link)
            from customer_auth import Customer
            login_user(Customer(row), remember=True)
            update_customer_last_login(row['id'])
            flash('Connexion réussie !', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('customer_profile'))
        else:
            flash('Email ou mot de passe incorrect.', 'error')

    return render_template('public/account/login.html')


@app.route('/compte/deconnexion')
@customer_login_required
def customer_logout():
    logout_user()
    flash('Vous êtes déconnecté.', 'info')
    return redirect(url_for('index'))


@app.route('/compte/profil', methods=['GET', 'POST'])
@customer_login_required
def customer_profile():
    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'profile':
            full_name = request.form.get('full_name', '').strip()
            phone = request.form.get('phone', '').strip()
            address = request.form.get('address', '').strip()
            if not full_name:
                flash('Le nom est obligatoire.', 'error')
            else:
                update_customer_profile(current_user.id, full_name, phone, address)
                flash('Profil mis à jour.', 'success')
            return redirect(url_for('customer_profile'))

        elif form_type == 'password':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_new_password', '')

            row = db.fetch_all('customers', filters={'id': current_user.id}, limit=1)
            row = row[0] if row else None

            if not row or not check_password_hash(row['password_hash'], current_password):
                flash('Mot de passe actuel incorrect.', 'error')
            elif len(new_password) < 6:
                flash('Le nouveau mot de passe doit contenir au moins 6 caractères.', 'error')
            elif new_password != confirm_password:
                flash('Les nouveaux mots de passe ne correspondent pas.', 'error')
            else:
                change_customer_password(current_user.id, new_password)
                flash('Mot de passe modifié.', 'success')
            return redirect(url_for('customer_profile'))

    rows = db.fetch_all('customers', filters={'id': current_user.id}, limit=1)
    customer = rows[0] if rows else None
    orders = get_customer_orders(current_user.id)
    stats = {
        'total': len(orders),
        'in_progress': sum(1 for o in orders if o.get('status') in ('En attente', 'Confirmée', 'Préparation', 'Expédiée')),
        'delivered': sum(1 for o in orders if o.get('status') == 'Livrée'),
    }
    return render_template('public/account/profile.html', customer=customer, stats=stats)


AVATAR_SIZE = 400


def _process_avatar(file):
    """Vérifie l'image, la redresse, la recadre en carré et la compresse en JPEG. Retourne (bytes, erreur)."""
    if not file or not file.filename:
        return None, "Veuillez choisir une photo."
    data = file.read()
    if not data:
        return None, "Le fichier est vide."
    try:
        from PIL import Image, ImageOps
        img = Image.open(io.BytesIO(data))
        img.verify()
        img = Image.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img)
        img = ImageOps.fit(img.convert('RGB'), (AVATAR_SIZE, AVATAR_SIZE), Image.LANCZOS)
        out = io.BytesIO()
        img.save(out, 'JPEG', quality=86, optimize=True)
        return out.getvalue(), None
    except Exception:
        return None, "Ce fichier n'est pas une image valide (jpg, png, webp)."


def _storage_path_from_url(url):
    marker = '/product-images/'
    if url and marker in url and '/avatars/' in url:
        return url.split(marker, 1)[1].split('?', 1)[0]
    return None


@app.route('/compte/photo', methods=['POST'])
@customer_login_required
def customer_avatar():
    sb = get_supabase()
    old_path = _storage_path_from_url(getattr(current_user, 'avatar_url', ''))

    if request.form.get('action') == 'remove':
        new_url = None
    else:
        data, error = _process_avatar(request.files.get('avatar'))
        if error:
            flash(error, 'error')
            return redirect(url_for('customer_profile'))
        path = f"avatars/{current_user.id}_{secrets.token_hex(6)}.jpg"
        try:
            sb.storage.from_('product-images').upload(path, data, {'content-type': 'image/jpeg'})
            new_url = sb.storage.from_('product-images').get_public_url(path)
        except Exception:
            flash("Impossible d'envoyer la photo pour le moment. Réessayez.", 'error')
            return redirect(url_for('customer_profile'))

    try:
        db.update('customers', {'avatar_url': new_url}, {'id': current_user.id})
    except Exception:
        app.logger.exception("Mise à jour avatar_url impossible (colonne manquante ?)")
        flash("La photo n'a pas pu être enregistrée. Réessayez plus tard.", 'error')
        return redirect(url_for('customer_profile'))

    if old_path:
        try:
            sb.storage.from_('product-images').remove([old_path])
        except Exception:
            pass
    flash('Photo de profil supprimée.' if new_url is None else 'Photo de profil mise à jour.', 'success')
    return redirect(url_for('customer_profile'))


@app.template_filter('nombre')
def nombre_filter(value):
    try:
        return f"{float(value or 0):,.0f}".replace(',', '\xa0')
    except (TypeError, ValueError):
        return value


@app.template_filter('wa')
def wa_filter(phone):
    """Numéro pour les liens wa.me (ajoute 227 aux numéros nigériens à 8 chiffres)."""
    digits = re.sub(r'\D', '', phone or '')
    if len(digits) == 8:
        digits = '227' + digits
    return digits


@app.template_filter('fcfa')
def fcfa_filter(value):
    try:
        return f"{float(value or 0):,.0f}".replace(',', '\xa0') + ' FCFA'
    except (TypeError, ValueError):
        return f"{value} FCFA"


@app.route('/compte/commandes')
@customer_login_required
def customer_orders():
    orders = sorted(get_customer_orders(current_user.id),
                    key=lambda o: o.get('created_at') or '', reverse=True)
    return render_template('public/account/orders.html', orders=orders)


@app.route('/compte/commande/<order_id>')
@customer_login_required
def customer_order_detail(order_id):
    order, items = get_order_with_items(order_id)
    if not order or str(order.get('customer_id')) != str(current_user.id):
        flash('Commande introuvable.', 'error')
        return redirect(url_for('customer_orders'))
    return render_template('public/account/order_detail.html', order=order, items=items)


INVOICE_STATUSES = ('Confirmée', 'Préparation', 'Expédiée', 'Livrée')


@app.route('/compte/commande/<order_id>/facture')
@customer_login_required
def customer_order_invoice(order_id):
    order, items = get_order_with_items(order_id)
    if not order or str(order.get('customer_id')) != str(current_user.id):
        flash('Commande introuvable.', 'error')
        return redirect(url_for('customer_orders'))

    # Facture seulement pour les commandes confirmées (pas en attente ni annulées)
    if order.get('status') not in INVOICE_STATUSES:
        flash('La facture n\'est pas disponible pour cette commande.', 'error')
        return redirect(url_for('customer_order_detail', order_id=order_id))

    order['customer_name'] = current_user.full_name

    pdf_bytes = generate_invoice_pdf(order, items, get_settings())
    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename=facture-{order["order_number"]}.pdf'}
    )


@app.route('/compte/mot-de-passe-oublie', methods=['GET', 'POST'])
def customer_forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()

        account_exists = False
        try:
            account_exists = generate_reset_code(email)
            if account_exists:
                log_action('Demande de code de réinitialisation', f'Email: {email}')
        except Exception:
            pass

        if not account_exists:
            flash("Cet email n'a pas de compte. Vérifiez l'adresse ou créez un compte.", 'error')
            return redirect(url_for('customer_forgot_password', email=email))

        # L'application WhatsApp est ouverte par le JS du formulaire (lien natif,
        # sans nouvel onglet) ; ici on amène ce même onglet sur la page de saisie du code.
        flash("Envoyez le message WhatsApp pré-rempli, puis collez ici le code reçu.", 'success')
        return redirect(url_for('customer_reset_password', email=email))

    return render_template('public/account/forgot_password.html',
                           email=request.args.get('email', '').strip())


@app.route('/compte/verifier-email', methods=['POST'])
def customer_check_email():
    """Vérifie si un email a un compte (utilisé par le JS du formulaire
    mot de passe oublié, avant d'ouvrir WhatsApp)."""
    email = request.form.get('email', '').strip()
    exists = bool(get_customer_by_email(email)) if email else False
    return {'exists': exists}


@app.route('/compte/reinitialiser', methods=['GET', 'POST'])
def customer_reset_password():
    if request.method == 'GET':
        email = request.args.get('email', '').strip()
        return render_template('public/account/reset_password.html', email=email)

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        code = request.form.get('code', '').strip()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        customer_id = verify_reset_code(email, code)
        if not customer_id:
            flash("Code invalide ou expiré. Vérifiez le code reçu sur WhatsApp.", 'error')
        elif len(new_password) < 6:
            flash('Le mot de passe doit contenir au moins 6 caractères.', 'error')
        elif new_password != confirm_password:
            flash('Les mots de passe ne correspondent pas.', 'error')
        else:
            change_customer_password(customer_id, new_password)
            consume_reset_code(email, code)
            log_action('Mot de passe réinitialisé via code', f'Email: {email}')
            flash('Mot de passe réinitialisé. Vous pouvez vous connecter.', 'success')
            return redirect(url_for('customer_login'))

        return render_template('public/account/reset_password.html', email=email)


# ============================================================
#  GESTION DES ERREURS
# ============================================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('public/about.html'), 404


@app.errorhandler(403)
def forbidden(e):
    flash('Accès non autorisé.', 'error')
    return redirect(url_for('admin_login'))


# ============================================================
#  DÉMARRAGE
# ============================================================

if __name__ == '__main__':
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

    if init_supabase():
        # Mode debug uniquement en développement local
        is_debug = os.environ.get('FLASK_ENV', 'production') == 'development'
        port = int(os.environ.get('PORT', 5000))

        print("\n" + "=" * 60)
        print("  HDATTAHER MOBILE - Serveur Supabase demarre!")
        print(f"  Site public : http://127.0.0.1:{port}")
        print(f"  Admin : http://127.0.0.1:{port}/admin/login")
        print(f"  Mode : {'DEVELOPPEMENT' if is_debug else 'PRODUCTION'}")
        print("  Base de donnees : Supabase (PostgreSQL)")
        print("=" * 60 + "\n")
        app.run(debug=is_debug, host='0.0.0.0', port=port)
    else:
        print("\n[ERREUR] Verifiez votre connexion Supabase dans .env")

