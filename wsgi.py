"""
WSGI Entry Point — Production
Utilisé par gunicorn : gunicorn wsgi:app
"""
import os
from config import Config

# Créer le dossier uploads si nécessaire
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

# Initialiser Supabase au chargement du module
from database import init_supabase
init_supabase()

# Importer l'application Flask
from app import app

if __name__ == '__main__':
    app.run()
