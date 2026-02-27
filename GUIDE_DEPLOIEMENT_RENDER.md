# 🚀 Guide de Déploiement — HDATTAHER MOBILE sur Render

## Prérequis

- Un compte **GitHub** (gratuit)
- Un compte **Render** (gratuit)
- Votre projet fonctionnel en local

---

## Étape 1 : Créer un compte GitHub

1. Allez sur **https://github.com/signup**
2. Créez un compte avec votre email
3. Confirmez votre email

---

## Étape 2 : Pousser le projet sur GitHub

### Depuis votre terminal (dans le dossier du projet) :

```bash
# Initialiser Git (si pas déjà fait)
git init

# Ajouter tous les fichiers
git add .

# Premier commit
git commit -m "HDATTAHER MOBILE - Prêt pour production"

# Créer le dépôt sur GitHub :
# Allez sur https://github.com/new
# Nom : hdattaher-mobile
# Visibility : Private (recommandé)
# NE cochez PAS "Add a README"
# Cliquez "Create repository"

# Connecter et pousser (remplacez VOTRE_USERNAME par votre nom GitHub)
git remote add origin https://github.com/VOTRE_USERNAME/hdattaher-mobile.git
git branch -M main
git push -u origin main
```

### ⚠️ Vérifications importantes :
- Le fichier `.env` ne doit **PAS** être poussé (il est dans `.gitignore`)
- Le fichier `.secret_key` ne doit **PAS** être poussé
- Le fichier `database.db` ne doit **PAS** être poussé

---

## Étape 3 : Créer un compte Render

1. Allez sur **https://render.com**
2. Cliquez **"Get Started for Free"**
3. Connectez-vous avec **GitHub** (recommandé — plus simple)
4. Autorisez Render à accéder à vos dépôts

---

## Étape 4 : Créer le Web Service sur Render

1. Dashboard Render → cliquez **"New +"** → **"Web Service"**
2. Sélectionnez votre dépôt **hdattaher-mobile**
3. Configurez :

| Paramètre | Valeur |
|---|---|
| **Name** | `hdattaher-mobile` |
| **Region** | `Frankfurt (EU)` (le plus proche du Niger) |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120` |
| **Plan** | `Free` (pour commencer) |

4. **NE CLIQUEZ PAS** encore sur "Create Web Service"

---

## Étape 5 : Ajouter les Variables d'Environnement

Avant de créer le service, descendez à la section **"Environment Variables"** et ajoutez :

| Clé | Valeur |
|---|---|
| `SUPABASE_URL` | `https://kgdpwegtqzbmbqhoqqdj.supabase.co` |
| `SUPABASE_ANON_KEY` | Votre clé anon (depuis Supabase Dashboard → Settings → API) |
| `SUPABASE_SERVICE_KEY` | Votre clé service (depuis Supabase Dashboard → Settings → API) |
| `SECRET_KEY` | Cliquez "Generate" (Render génère une clé sécurisée) |
| `FLASK_ENV` | `production` |

### ⚠️ Important :
- **NE METTEZ JAMAIS** vos clés Supabase dans le code
- Render chiffre automatiquement ces variables
- La variable `PORT` est ajoutée automatiquement par Render

---

## Étape 6 : Déployer

1. Cliquez **"Create Web Service"**
2. Render va :
   - Cloner votre dépôt
   - Installer les dépendances (`pip install -r requirements.txt`)
   - Lancer gunicorn avec votre `Procfile`
3. Attendez 2-3 minutes que le build se termine
4. Vous verrez le statut passer à **"Live"** ✅

### URL de votre site :
```
https://hdattaher-mobile.onrender.com
```

---

## Étape 7 : Vérifier le déploiement

1. Ouvrez votre URL Render dans un navigateur
2. Vérifiez la page d'accueil
3. Testez la connexion admin : `https://hdattaher-mobile.onrender.com/admin/login`
4. Vérifiez que les produits s'affichent
5. Testez le menu mobile sur téléphone

---

## 📁 Structure des fichiers de production

```
hdattaher_mobile/
├── Procfile              ← Commande de démarrage Render
├── render.yaml           ← Blueprint Render (optionnel)
├── runtime.txt           ← Version Python
├── requirements.txt      ← Dépendances Python
├── wsgi.py               ← Point d'entrée WSGI
├── .env.example          ← Template des variables
├── .gitignore            ← Fichiers exclus de Git
├── app.py                ← Application Flask
├── config.py             ← Configuration
├── database.py           ← Client Supabase
├── static/               ← CSS, JS, images
│   ├── css/
│   ├── js/
│   └── uploads/
└── templates/            ← Templates HTML
    ├── admin/
    └── public/
```

---

## ⚠️ Problèmes courants et solutions

### 1. "Application Error" au premier déploiement
**Cause** : Variables d'environnement manquantes
**Solution** : Vérifiez dans Render → Environment que toutes les variables sont configurées

### 2. Le site ne charge pas les images
**Cause** : Les images uploadées localement ne sont pas sur Render
**Solution** : Re-uploadez vos images produits via l'admin une fois déployé.
Render utilise un système de fichiers éphémère — les uploads disparaissent à chaque redéploiement.
**Solution à long terme** : Migrer les images vers Supabase Storage.

### 3. Le site "dort" après 15 minutes (plan gratuit)
**Cause** : Le plan gratuit de Render met le service en veille
**Solution** :
- Premier chargement après veille = ~30 secondes d'attente
- Pour éviter ça : passer au plan Starter ($7/mois)
- Ou utiliser un service de ping comme UptimeRobot (gratuit)

### 4. Erreur CSRF
**Cause** : Le SECRET_KEY change entre les redéploiements
**Solution** : Utilisez un SECRET_KEY fixe dans les variables Render (pas "Generate" à chaque fois)

---

## 🔄 Mises à jour futures

Pour chaque modification :

```bash
git add .
git commit -m "Description de la modification"
git push origin main
```

Render détecte automatiquement le push et redéploie en 2-3 minutes.

---

## 📊 Récapitulatif des coûts

| Service | Coût |
|---|---|
| **Render (Free)** | 0 FCFA/mois |
| **Supabase (Free)** | 0 FCFA/mois |
| **GitHub (Free)** | 0 FCFA/mois |
| **Domaine personnalisé** | ~5,000 - 15,000 FCFA/an (optionnel) |
| **Total minimum** | **0 FCFA/mois** ✅ |

---

## 🌐 Domaine personnalisé (optionnel)

Si vous voulez `www.hdattahermobile.com` au lieu de `hdattaher-mobile.onrender.com` :

1. Achetez un domaine sur **Namecheap**, **Google Domains** ou **OVH**
2. Render Dashboard → Settings → Custom Domains
3. Ajoutez votre domaine
4. Configurez les DNS chez votre registrar (CNAME vers Render)
5. Render génère un certificat SSL gratuit automatiquement

---

**Votre site sera accessible dans le monde entier ! 🌍**
