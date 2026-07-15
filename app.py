"""
HDATTAHER MOBILE - Application Flask (Supabase / PostgreSQL)
Site e-commerce de vente de téléphones et accessoires
Propriétaire : Hdattaher | Localisation : Niger
"""
import os
import time
from urllib.parse import quote
from datetime import datetime, timedelta
from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for,
                   flash, session, jsonify, send_from_directory, abort, Response)
from flask_caching import Cache
from flask_compress import Compress
from werkzeug.utils import secure_filename
from flask_wtf.csrf import CSRFProtect
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
                            get_dashboard_stats)
from invoice_generator import generate_invoice_pdf
# test redeploiement storage 2
app = Flask(__name__)
app.config.from_object(Config)

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
    if session.get('logged_in'):
        pending_reset_count = count_pending_reset_requests()
    return dict(settings=settings, categories=categories, dynamic_css=dynamic_css,
                cart_count=cart_count, pending_reset_count=pending_reset_count)


# ============================================================
#  SÉCURITÉ - En-têtes
# ============================================================

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

    # Produits vedettes
    r = sb.table('products').select('*, categories(name)') \
        .eq('is_active', True).eq('is_featured', True) \
        .order('created_at', desc=True).limit(8).execute()
    featured = r.data or []

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
    for lst in [featured, latest, promos]:
        for p in lst:
            cat = p.pop('categories', None)
            p['category_name'] = cat['name'] if cat else None

    # Stats
    total_products = db.count('products', {'is_active': True})
    all_prods = db.fetch_all('products', 'brand', {'is_active': True})
    unique_brands = len(set(p['brand'] for p in all_prods if p.get('brand')))

    stats = {
        'total_products': total_products,
        'total_brands': unique_brands,
        'happy_clients': 1000,
    }

    banners = db.fetch_all('banners', '*', {'is_active': True}, order=('sort_order', True))

    return render_template('public/index.html', featured=featured, latest=latest,
                           promos=promos, stats=stats, banners=banners)


@app.route('/products')
def products():
    """Page de tous les produits avec filtres"""
    sb = get_supabase()

    category_id = request.args.get('category', default=None, type=str)
    search = request.args.get('search', default='', type=str).strip()
    min_price = request.args.get('min_price', default=None, type=float)
    max_price = request.args.get('max_price', default=None, type=float)
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

    if min_price is not None:
        query = query.gte('price', min_price)
    if max_price is not None:
        query = query.lte('price', max_price)

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

    return render_template('public/products.html',
                           products=products_list,
                           all_categories=all_categories,
                           current_category=category_id,
                           search=search, sort=sort,
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


@app.route('/featured')
def featured_products():
    """Produits en vedette"""
    sb = get_supabase()
    r = sb.table('products').select('*, categories(name)') \
        .eq('is_active', True).eq('is_featured', True) \
        .order('created_at', desc=True).execute()
    products_list = r.data or []
    for p in products_list:
        cat = p.pop('categories', None)
        p['category_name'] = cat['name'] if cat else None
    return render_template('public/products.html',
                           products=products_list,
                           all_categories=db.fetch_all('categories', '*', {'is_active': True}, order=('sort_order', True)),
                           page_title='Produits en Vedette ⭐',
                           current_category=None, search='', sort='newest',
                           min_price=None, max_price=None)


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


@app.route('/contact')
def contact():
    """Page contact"""
    return render_template('public/contact.html')

@app.route('/api/products')
def api_products():
    search = request.args.get('q', '')
    if search:
        sb = get_supabase()
        r = sb.table('products').select('id, name, price, image, discount') \
            .eq('is_active', True) \
            .or_(f'name.ilike.%{search}%,brand.ilike.%{search}%') \
            .limit(10).execute()
        return jsonify(r.data or [])
    return jsonify([])


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
        'total_views': sum(p['views'] for p in db.fetch_all('products', 'views')),
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
    order_stats = get_dashboard_stats(days=periode)

    return render_template('admin/dashboard.html', stats=stats, recent=recent, top_viewed=top_viewed,
                            order_stats=order_stats, periode=periode)


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
    return render_template('admin/products.html', products=products_list)


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
            return render_template('admin/product_form.html', product=None, categories=cats, action='add')

        image_filename = 'default.png'

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
                        storage_filename,
                        file_bytes,
                        {
                            'content-type': file.content_type,
                            'upsert': 'true'
                        }
                    )

                    image_filename = sb.storage.from_(
                        'product-images'
                    ).get_public_url(storage_filename)

        db.insert('products', {
            'name': name,
            'name_en': name_en,
            'name_ar': name_ar,
            'description': description,
            'description_en': description_en,
            'description_ar': description_ar,
            'price': safe_float(request.form.get('price'), 0),
            'old_price': safe_float(request.form.get('old_price'), 0),
            'discount': safe_int(request.form.get('discount'), 0),
            'stock': safe_int(request.form.get('stock'), 0),
            'category_id': request.form.get('category_id'),
            'image': image_filename,
            'brand': request.form.get('brand', ''),
            'is_featured': bool(request.form.get('is_featured')),
            'is_new': bool(request.form.get('is_new')),
        })
        log_action('Ajout produit', f'Produit: {name}')
        flash('Produit ajouté avec succès!', 'success')
        return redirect(url_for('admin_products'))

    return render_template('admin/product_form.html', product=None, categories=cats, action='add')


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
            return render_template('admin/product_form.html', product=product, categories=cats, action='edit')

        image_filename = product['image']
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
                    storage_filename,
                    file_bytes,
                    {
                        'content-type': file.content_type,
                        'upsert': 'true'
                    }
                )

                image_filename = sb.storage.from_(
                    'product-images'
                ).get_public_url(storage_filename)
                
                    
                    
                    
                    

        db.update('products', {
            'name': name,
            'name_en': name_en,
            'name_ar': name_ar,
            'description': description,
            'description_en': description_en,
            'description_ar': description_ar,
            'price': safe_float(request.form.get('price'), 0),
            'old_price': safe_float(request.form.get('old_price'), 0),
            'discount': safe_int(request.form.get('discount'), 0),
            'stock': safe_int(request.form.get('stock'), 0),
            'category_id': request.form.get('category_id'),
            'image': image_filename,
            'brand': request.form.get('brand', ''),
            'is_featured': bool(request.form.get('is_featured')),
            'is_new': bool(request.form.get('is_new')),
            'is_active': bool(request.form.get('is_active')),
        }, {'id': product_id})
        log_action('Modification produit', f'Produit: {name}')
        flash('Produit modifié avec succès!', 'success')
        return redirect(url_for('admin_products'))

    return render_template('admin/product_form.html', product=product, categories=cats, action='edit')


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
            'name_en': request.form.get('name_en', ''),
            'name_ar': request.form.get('name_ar', ''),
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


@app.route('/azawad/reinitialisations/traiter/<request_id>', methods=['POST'])
@login_required
def admin_resolve_reset_request(request_id):
    db.update('password_resets', {'dismissed': True}, {'id': request_id})
    log_action('Code de réinitialisation marqué traité', f'ID: {request_id}')
    flash('Demande marquée comme traitée.', 'success')
    return redirect(url_for('admin_reset_requests'))


@app.route('/azawad/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if request.method == 'POST':
        fields = ['site_name', 'owner_name', 'whatsapp', 'location',
                  'primary_color', 'secondary_color', 'accent_color',
                  'about_title', 'about_title_en', 'about_title_ar',
                  'about_text', 'about_text_en', 'about_text_ar',
                  'facebook', 'instagram', 'tiktok', 'promotions_active']

        for field in fields:
            value = request.form.get(field, '')
            db.upsert('settings', {'key': field, 'value': value}, on_conflict='key')

        dark_mode = '1' if request.form.get('dark_mode') else '0'
        db.upsert('settings', {'key': 'dark_mode', 'value': dark_mode}, on_conflict='key')

        # Upload logo
        if 'logo' in request.files:
            logo_file = request.files['logo']
            if logo_file and logo_file.filename and allowed_file(logo_file.filename):
                filename = secure_filename(logo_file.filename)
                if filename:
                    logo_filename = f'logo_{int(time.time())}_{filename}'
                    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
                    logo_file.save(os.path.join(Config.UPLOAD_FOLDER, logo_filename))
                    db.upsert('settings', {'key': 'logo_path', 'value': logo_filename}, on_conflict='key')

        log_action('Modification paramètres', 'Paramètres mis à jour')
        cache.delete_memoized(get_settings)
        flash('Paramètres sauvegardés!', 'success')
        return redirect(url_for('admin_settings'))

    return render_template('admin/settings.html')


@app.route('/azawad/password', methods=['POST'])
@login_required
def admin_change_password():
    old_pwd = request.form.get('old_password', '')
    new_pwd = request.form.get('new_password', '')

    if len(new_pwd) < 8:
        flash('Le mot de passe doit contenir au moins 8 caractères.', 'error')
        return redirect(url_for('admin_settings'))

    sb = get_supabase()
    try:
        result = sb.rpc('change_admin_password', {
            'p_admin_id': session['user_id'],
            'p_old_password': old_pwd,
            'p_new_password': new_pwd
        }).execute()

        if result.data is True:
            log_action('Changement mot de passe', f'Utilisateur: {session.get("username")}')
            flash('Mot de passe changé avec succès!', 'success')
        else:
            flash('Ancien mot de passe incorrect.', 'error')
    except Exception as e:
        flash('Erreur lors du changement de mot de passe.', 'error')

    return redirect(url_for('admin_settings'))


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
    cart_module.add_to_cart(product_id, quantity)
    flash('Produit ajouté au panier.', 'success')
    return redirect(request.referrer or url_for('products'))


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

@app.route('/commande/valider', methods=['GET', 'POST'])
@customer_login_required
def checkout():
    items, total = cart_module.get_cart_details()
    if not items:
        flash('Votre panier est vide.', 'error')
        return redirect(url_for('cart_view'))

    if request.method == 'POST':
        shipping_name = request.form.get('shipping_name', '').strip()
        shipping_phone = request.form.get('shipping_phone', '').strip()
        shipping_address = request.form.get('shipping_address', '').strip()
        notes = request.form.get('notes', '').strip()

        if not shipping_name or not shipping_phone or not shipping_address:
            flash('Veuillez remplir toutes les informations de livraison.', 'error')
            return render_template('public/checkout.html', items=items, total=total)

        order, error = create_order_from_cart(
            current_user.id, items, shipping_name, shipping_phone, shipping_address, notes
        )

        if error:
            flash(error, 'error')
            return render_template('public/checkout.html', items=items, total=total)

        cart_module.clear_cart()
        log_action('Nouvelle commande', f'N° {order["order_number"]} - Client: {current_user.email}')
        flash(f'Commande {order["order_number"]} enregistrée avec succès !', 'success')
        return redirect(url_for('order_confirmation', order_id=order['id']))

    # Pré-remplissage avec les infos du profil
    rows = db.fetch_all('customers', filters={'id': current_user.id}, limit=1)
    customer = rows[0] if rows else {}
    return render_template('public/checkout.html', items=items, total=total, customer=customer)


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
    orders = get_all_orders(status_filter if status_filter else None)
    return render_template('admin/orders.html', orders=orders, statuses=ORDER_STATUSES,
                            status_filter=status_filter)


@app.route('/azawad/commande/<order_id>')
def admin_order_detail(order_id):
    if 'logged_in' not in session:
        return redirect(url_for('admin_login'))
    order, items = get_order_with_items(order_id)
    if not order:
        flash('Commande introuvable.', 'error')
        return redirect(url_for('admin_orders'))
    return render_template('admin/order_detail.html', order=order, items=items, statuses=ORDER_STATUSES)


@app.route('/azawad/commande/statut/<order_id>', methods=['POST'])
def admin_update_order_status(order_id):
    if 'logged_in' not in session:
        return redirect(url_for('admin_login'))
    new_status = request.form.get('status', '')
    if update_order_status(order_id, new_status):
        log_action('Statut commande modifié', f'Commande: {order_id} -> {new_status}')
        flash('Statut de la commande mis à jour.', 'success')
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
    return render_template('public/account/profile.html', customer=customer)


@app.route('/compte/commandes')
@customer_login_required
def customer_orders():
    orders = get_customer_orders(current_user.id)
    return render_template('public/account/orders.html', orders=orders)


@app.route('/compte/commande/<order_id>')
@customer_login_required
def customer_order_detail(order_id):
    order, items = get_order_with_items(order_id)
    if not order or str(order.get('customer_id')) != str(current_user.id):
        flash('Commande introuvable.', 'error')
        return redirect(url_for('customer_orders'))
    return render_template('public/account/order_detail.html', order=order, items=items)


@app.route('/compte/commande/<order_id>/facture')
@customer_login_required
def customer_order_invoice(order_id):
    order, items = get_order_with_items(order_id)
    if not order or str(order.get('customer_id')) != str(current_user.id):
        flash('Commande introuvable.', 'error')
        return redirect(url_for('customer_orders'))

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
        try:
            generate_reset_code(email)
            log_action('Demande de code de réinitialisation', f'Email: {email}')
        except Exception:
            pass

        settings = get_settings()
        whatsapp_number = settings.get('whatsapp', '22791720755')
        message = quote(f"Bonjour, je veux mon code pour réinitialiser mon mot de passe. Email : {email}")
        return redirect(f"https://wa.me/{whatsapp_number}?text={message}")

    return render_template('public/account/forgot_password.html')


@app.route('/compte/reinitialiser', methods=['GET', 'POST'])
def customer_reset_password():
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

    return render_template('public/account/reset_password.html')


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

