"""
Configuration sécurisée du projet HDATTAHER MOBILE
Version Supabase (PostgreSQL)
"""
import os
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


class Config:
    # --- Clé secrète forte ---
    SECRET_KEY = os.environ.get('SECRET_KEY') or _get_or_create_secret_key()

    # --- Supabase ---
    SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
    SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', '')
    SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')

    # --- Uploads ---
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # --- Sessions sécurisées ---
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 heure

    # --- Protection CSRF (Flask-WTF) ---
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    # --- Rate limiting connexion ---
    LOGIN_MAX_ATTEMPTS = 5
    LOGIN_LOCKOUT_SECONDS = 300

    # --- SEO / domaine du site ---
    SITE_URL = os.environ.get('SITE_URL', 'https://hdattahermobile.com')
