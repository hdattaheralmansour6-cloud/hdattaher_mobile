"""
HDATTAHER MOBILE - Authentification des comptes clients (Flask-Login)
Séparé de l'authentification admin (qui reste inchangée dans app.py).
"""
import random
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
#  RÉINITIALISATION DE MOT DE PASSE PAR CODE (contact WhatsApp)
# ============================================================

def _parse_expiry(expires_at):
    """Convertit une date ISO Supabase en datetime naïf, ou une date déjà expirée si invalide."""
    if not expires_at:
        return datetime.utcnow() - timedelta(seconds=1)
    try:
        return datetime.fromisoformat(expires_at.replace('Z', '+00:00')).replace(tzinfo=None)
    except Exception:
        return datetime.utcnow() - timedelta(seconds=1)


def generate_reset_code(email):
    """
    Crée un code de réinitialisation à 6 chiffres, valable 30 minutes.
    Le code n'est JAMAIS renvoyé au client sur le site : il doit contacter
    la boutique sur WhatsApp pour l'obtenir depuis l'espace admin.
    Retourne True si un compte existe avec cet email, False sinon (usage interne,
    la réponse affichée au client reste identique dans les deux cas pour la sécurité).
    """
    customer = get_customer_by_email(email)
    if not customer:
        return False

    try:
        code = f"{random.randint(0, 999999):06d}"
        expires_at = (datetime.utcnow() + timedelta(minutes=30)).isoformat()
        db.insert('password_resets', {
            'customer_id': customer['id'],
            'code': code,
            'expires_at': expires_at,
            'used': False,
        })
    except Exception as e:
        # Ne bloque jamais le client si la table n'est pas encore prête côté Supabase,
        # mais on garde une trace de l'erreur exacte dans les logs Render pour diagnostiquer.
        print(f"[generate_reset_code] Erreur insertion password_resets : {e}")
        return False
    return True


def verify_reset_code(email, code):
    """Retourne le customer_id si l'email + le code correspondent à une demande valide et non expirée."""
    customer = get_customer_by_email(email)
    if not customer or not code:
        return None

    try:
        rows = db.fetch_all('password_resets', filters={
            'customer_id': customer['id'], 'code': code.strip(), 'used': False,
        })
    except Exception:
        return None
    if not rows:
        return None

    # En cas de plusieurs codes générés, on prend le plus récent
    reset = sorted(rows, key=lambda r: r.get('created_at') or '', reverse=True)[0]
    if _parse_expiry(reset.get('expires_at')) < datetime.utcnow():
        return None
    return reset['customer_id']


def consume_reset_code(email, code):
    customer = get_customer_by_email(email)
    if not customer:
        return
    try:
        db.update('password_resets', {'used': True},
                  {'customer_id': customer['id'], 'code': code.strip()})
    except Exception:
        pass


def get_pending_reset_requests():
    """
    Liste des demandes de réinitialisation en attente (code non utilisé et non expiré),
    avec les infos client, pour l'espace admin (l'admin y récupère le code à envoyer
    manuellement sur WhatsApp).
    """
    try:
        rows = db.fetch_all(
            'password_resets', '*, customers(full_name, email, phone)',
            filters={'used': False}, order=('created_at', False),
        )
    except Exception as e:
        # La table n'existe peut-être pas encore (migration SQL non exécutée) :
        # on ne casse jamais l'espace admin pour autant.
        print(f"[get_pending_reset_requests] Erreur lecture password_resets : {e}")
        return []
    pending = []
    now = datetime.utcnow()
    for r in rows:
        if _parse_expiry(r.get('expires_at')) < now:
            continue
        customer = r.pop('customers', None)
        r['customer_name'] = customer['full_name'] if customer else 'Client supprimé'
        r['customer_email'] = customer['email'] if customer else ''
        r['customer_phone'] = customer['phone'] if customer else ''
        pending.append(r)
    return pending


def count_pending_reset_requests():
    try:
        return len(get_pending_reset_requests())
    except Exception:
        return 0
