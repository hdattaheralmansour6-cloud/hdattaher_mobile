"""
HDATTAHER MOBILE - Authentification des comptes clients (Flask-Login)
Séparé de l'authentification admin (qui reste inchangée dans app.py).
"""
import secrets
from datetime import datetime, timedelta

from flask_login import LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from database import db

login_manager = LoginManager()
login_manager.login_view = 'customer_login'
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "info"


class Customer(UserMixin):
    """Wrapper Flask-Login autour d'une ligne de la table 'customers'."""

    def __init__(self, row):
        self.id = row['id']
        self.full_name = row.get('full_name', '')
        self.email = row.get('email', '')
        self.phone = row.get('phone', '')
        self.address = row.get('address', '')
        self.is_active_account = row.get('is_active', True)

    def get_id(self):
        return str(self.id)

    @property
    def is_active(self):
        return self.is_active_account


@login_manager.user_loader
def load_customer(customer_id):
    rows = db.fetch_all('customers', filters={'id': customer_id}, limit=1)
    if rows:
        return Customer(rows[0])
    return None


def get_customer_by_email(email):
    rows = db.fetch_all('customers', filters={'email': email.strip().lower()}, limit=1)
    return rows[0] if rows else None


def create_customer(full_name, email, phone, password):
    email = email.strip().lower()
    if get_customer_by_email(email):
        return None, "Un compte existe déjà avec cet email."

    password_hash = generate_password_hash(password)
    row = db.insert('customers', {
        'full_name': full_name.strip(),
        'email': email,
        'phone': phone.strip() if phone else None,
        'password_hash': password_hash,
    })
    if not row:
        return None, "Erreur lors de la création du compte."
    return Customer(row), None


def verify_customer_password(email, password):
    row = get_customer_by_email(email)
    if not row:
        return None
    if not check_password_hash(row['password_hash'], password):
        return None
    if not row.get('is_active', True):
        return None
    return row


def update_customer_last_login(customer_id):
    db.update('customers', {'last_login': datetime.utcnow().isoformat()}, {'id': customer_id})


def update_customer_profile(customer_id, full_name, phone, address):
    db.update('customers', {
        'full_name': full_name.strip(),
        'phone': phone.strip() if phone else None,
        'address': address.strip() if address else None,
        'updated_at': datetime.utcnow().isoformat(),
    }, {'id': customer_id})


def change_customer_password(customer_id, new_password):
    db.update('customers', {
        'password_hash': generate_password_hash(new_password),
        'updated_at': datetime.utcnow().isoformat(),
    }, {'id': customer_id})


# ============================================================
#  RÉINITIALISATION DE MOT DE PASSE
# ============================================================

def create_password_reset_token(email):
    """Crée un jeton de réinitialisation valable 1 heure. Retourne None si l'email n'existe pas."""
    customer = get_customer_by_email(email)
    if not customer:
        return None

    token = secrets.token_urlsafe(32)
    expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    db.insert('password_resets', {
        'customer_id': customer['id'],
        'token': token,
        'expires_at': expires_at,
    })
    return token


def verify_reset_token(token):
    """Retourne le customer_id si le jeton est valide et non expiré, sinon None."""
    rows = db.fetch_all('password_resets', filters={'token': token}, limit=1)
    if not rows:
        return None
    reset = rows[0]
    if reset.get('used'):
        return None
    expires_at = reset.get('expires_at')
    if expires_at:
        try:
            exp = datetime.fromisoformat(expires_at.replace('Z', '+00:00')).replace(tzinfo=None)
        except Exception:
            exp = datetime.utcnow() - timedelta(seconds=1)
        if exp < datetime.utcnow():
            return None
    return reset['customer_id']


def consume_reset_token(token):
    db.update('password_resets', {'used': True}, {'token': token})
