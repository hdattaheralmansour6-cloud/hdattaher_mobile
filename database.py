"""
HDATTAHER MOBILE - Module Base de Données Supabase
Remplace SQLite par Supabase (PostgreSQL)
"""
from config import Config
from supabase import create_client, Client


# ============================================================
#  CLIENT SUPABASE (SINGLETON)
# ============================================================

_supabase_client: Client = None


def get_supabase() -> Client:
    """Obtenir le client Supabase."""
    global _supabase_client
    if _supabase_client is None:
        url = Config.SUPABASE_URL
        key = Config.SUPABASE_SERVICE_KEY
        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL et SUPABASE_SERVICE_KEY doivent etre definis dans .env"
            )
        _supabase_client = create_client(url, key)
    return _supabase_client


# ============================================================
#  CLASSE HELPER CRUD
# ============================================================

class SupabaseDB:
    """Simplification des opérations CRUD avec Supabase."""

    @staticmethod
    def fetch_all(table, columns='*', filters=None, order=None, limit=None):
        """Récupérer plusieurs lignes."""
        sb = get_supabase()
        query = sb.table(table).select(columns)

        if filters:
            if isinstance(filters, dict):
                for col, val in filters.items():
                    query = query.eq(col, val)
            elif isinstance(filters, list):
                for f in filters:
                    if len(f) == 3:
                        col, op, val = f
                        ops = {
                            'eq': query.eq, 'neq': query.neq,
                            'gt': query.gt, 'gte': query.gte,
                            'lt': query.lt, 'lte': query.lte,
                            'like': query.like, 'ilike': query.ilike,
                        }
                        if op in ops:
                            query = ops[op](col, val)

        if order:
            if isinstance(order, tuple):
                col, ascending = order
                query = query.order(col, desc=not ascending)
            elif isinstance(order, str):
                query = query.order(order, desc=True)

        if limit:
            query = query.limit(limit)

        result = query.execute()
        return result.data if result.data else []

    @staticmethod
    def fetch_one(table, columns='*', filters=None):
        results = SupabaseDB.fetch_all(table, columns, filters, limit=1)
        return results[0] if results else None

    @staticmethod
    def insert(table, data):
        sb = get_supabase()
        result = sb.table(table).insert(data).execute()
        return result.data[0] if result.data else None

    @staticmethod
    def update(table, data, filters):
        sb = get_supabase()
        query = sb.table(table).update(data)
        for col, val in filters.items():
            query = query.eq(col, val)
        result = query.execute()
        return result.data if result.data else []

    @staticmethod
    def upsert(table, data, on_conflict=None):
        sb = get_supabase()
        if on_conflict:
            result = sb.table(table).upsert(data, on_conflict=on_conflict).execute()
        else:
            result = sb.table(table).upsert(data).execute()
        return result.data if result.data else []

    @staticmethod
    def delete(table, filters):
        sb = get_supabase()
        query = sb.table(table).delete()
        for col, val in filters.items():
            query = query.eq(col, val)
        result = query.execute()
        return result.data if result.data else []

    @staticmethod
    def count(table, filters=None):
        sb = get_supabase()
        query = sb.table(table).select('*', count='exact').limit(0)
        if filters:
            if isinstance(filters, dict):
                for col, val in filters.items():
                    query = query.eq(col, val)
        result = query.execute()
        return result.count if result.count is not None else 0


# Alias global
db = SupabaseDB


# ============================================================
#  FONCTIONS SPÉCIALISÉES
# ============================================================

def verify_admin_password(username, password):
    """Vérifier le login admin via RPC bcrypt côté serveur."""
    sb = get_supabase()
    try:
        result = sb.rpc('verify_admin_login', {
            'p_username': username,
            'p_password': password
        }).execute()
        if result.data and len(result.data) > 0:
            return result.data[0]
    except Exception:
        pass
    return None


def get_settings_dict():
    """Récupérer tous les paramètres sous forme de dict."""
    rows = db.fetch_all('settings', 'key, value')
    return {row['key']: row['value'] for row in rows}


def init_supabase():
    """Vérifier la connexion à Supabase au démarrage."""
    try:
        sb = get_supabase()
        result = sb.table('settings').select('key').limit(1).execute()
        print("[OK] Connexion Supabase reussie!")
        return True
    except Exception as e:
        print(f"[ERREUR] Connexion Supabase echouee: {e}")
        return False
