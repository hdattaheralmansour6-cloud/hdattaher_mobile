"""
Configuration sécurisée du projet HDATTAHER MOBILE
Version Supabase (PostgreSQL)
"""
import os
import hmac
import hashlib
import secrets

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Charger les variables d'environnement depuis .env
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, '.env'))
except ImportError:
    pass


# Générer une clé secrète forte et persistante
_secret_key_file = os.path.join(BASE_DIR, '.secret_key')
def _get_or_create_secret_key():
    if os.path.exists(_secret_key_file):
        with open(_secret_key_file, 'r') as f:
            key = f.read().strip()
            if len(key) >= 32:
                return key
    key = secrets.token_hex(32)
    with open(_secret_key_file, 'w') as f:
        f.write(key)
    return key


def _get_secret_key():
    """
    Clé secrète des sessions, identique pour les 2 workers et à chaque redéploiement :
    1. SECRET_KEY définie dans l'environnement (Render) si elle existe ;
    2. sinon dérivée de SUPABASE_SERVICE_KEY (stable, jamais exposée) ;
    3. sinon fichier .secret_key (développement local uniquement).
    Une clé qui change à chaque déploiement invalide toutes les sessions et fait
    échouer les formulaires déjà ouverts ("The CSRF session token is missing").
    """
    env_key = os.environ.get('SECRET_KEY')
    if env_key:
        return env_key
    service_key = os.environ.get('SUPABASE_SERVICE_KEY', '')
    if service_key:
        return hmac.new(service_key.encode('utf-8'), b'hdattaher-mobile-flask-secret-v1',
                        hashlib.sha256).hexdigest()
    return _get_or_create_secret_key()


class Config:
    # --- Clé secrète forte et stable ---
    SECRET_KEY = _get_secret_key()

    # --- Supabase ---
    SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
    SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', '')
    SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')

    # --- Uploads ---
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # Paiement par transfert d'argent mobile (le client envoie le reçu en capture d'écran)
    PAYMENT_NUMBER = '91720755'
    PAYMENT_METHODS = ('Amanata', 'Nita')

    # --- Sessions sécurisées ---
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # Cookie envoyé uniquement en HTTPS (désactivé en développement local en http)
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV', 'production') != 'development'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 heure

    # --- Protection CSRF (Flask-WTF) ---
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    # --- Rate limiting connexion ---
    LOGIN_MAX_ATTEMPTS = 5
    LOGIN_LOCKOUT_SECONDS = 300

    # --- SEO / domaine du site ---
    SITE_URL = os.environ.get('SITE_URL', 'https://hdattahermobile.com')

    # --- Performance : cache navigateur pour les fichiers statiques (7 jours) ---
    SEND_FILE_MAX_AGE_DEFAULT = 7 * 24 * 60 * 60
