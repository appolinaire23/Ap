import logging
import os
import zipfile
import shutil
from telethon import events
from datetime import datetime
import subprocess

logger = logging.getLogger(__name__)

async def create_complete_railway_package():
    """Créer le package complet Railway via create_deployment_package.py"""
    try:
        # Exécuter le script de création de package complet
        result = subprocess.run(['python', 'create_deployment_package.py'], 
                              capture_output=True, text=True, cwd='.')

        if result.returncode == 0:
            # Le fichier créé est TeleFeed_Railway_Complete_Deploy.zip
            zip_path = 'TeleFeed_Railway_Complete_Deploy.zip'
            if os.path.exists(zip_path):
                logger.info(f"Package Railway complet créé: {zip_path}")
                return zip_path

        logger.error(f"Erreur création package complet: {result.stderr}")
        return None

    except Exception as e:
        logger.error(f"Erreur lors de la création du package complet: {e}")
        return None

async def handle_deploy(event, client):
    """
    Handle deployment command - creates ZIP file with all bot files
    Premium feature for licensed users
    """
    try:
        user_id = event.sender_id

        # Check if user has premium access
        if not await is_premium_user(user_id):
            await event.respond("❌ **Accès premium requis**\n\nCette fonctionnalité est réservée aux utilisateurs premium.\nUtilisez `/valide` pour activer votre licence.")
            return

        await event.respond("📦 **Création du package de déploiement...**\n\n⏳ Préparation des fichiers en cours...")

        # Create deployment ZIP
        zip_path = await create_deployment_zip()

        if zip_path and os.path.exists(zip_path):
            # Send the ZIP file
            await client.send_file(
                user_id,
                zip_path,
                caption="""
🚂 **Package de déploiement Railway COMPLET**

📁 **Contenu du package :**
• Tous les fichiers du bot
• Configuration Railway (railway.json, Dockerfile, nixpacks.toml)
• Système de communication automatique Railway ↔ Replit
• Variables d'environnement (.env.example)
• Documentation complète

🚀 **Prêt pour le déploiement sur Railway.app**

📋 **Instructions :**
1. Décompressez le fichier ZIP
2. Uploadez sur GitHub
3. Déployez sur Railway.app
4. Configurez les variables d'environnement
5. Recevez automatiquement la notification de succès !

✅ **Communication automatique Railway ↔ Replit ↔ Bot intégrée**
                """,
                attributes=[],
                force_document=True
            )

            # Clean up
            os.remove(zip_path)
            logger.info(f"Deployment package sent to user {user_id}")

        else:
            await event.respond("❌ **Erreur lors de la création du package**\n\nVeuillez réessayer plus tard.")

    except Exception as e:
        logger.error(f"Error in deploy handling: {e}")
        await event.respond("❌ Erreur lors du traitement du déploiement. Veuillez réessayer.")

async def create_deployment_zip():
    """Create a ZIP file with all necessary deployment files including Railway support"""
    try:
        # Individual files to include
        files_to_include = [
            'main.py',
            'main_railway.py',
            'main_render.py',
            'main_render_fixed.py',
            'requirements.txt',
            'Procfile',
            'runtime.txt',
            'render.yaml',
            '.env.example',
            'user_data.json',
            'http_server.py',
            'auto_communication.py',
            'railway_keep_alive.py',
            'render_keep_alive.py',
            'RENDER_DATABASE_SETUP.md',
            'DEPLOYMENT_GUIDE.md',
            'PROJECT_OVERVIEW.md',
            'railway.json',
            'nixpacks.toml',
            'Dockerfile'
        ]

        zip_path = 'TeleFeed_Deployment.zip'

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add individual files
            for item in files_to_include:
                if os.path.exists(item):
                    zipf.write(item, os.path.basename(item))
                    logger.info(f"Added file to ZIP: {item}")

            # Add all bot files directly (no bot/ folder)
            bot_dir = 'bot'
            if os.path.exists(bot_dir):
                for file in os.listdir(bot_dir):
                    file_path = os.path.join(bot_dir, file)
                    if os.path.isfile(file_path) and not file.endswith('.session') and '__pycache__' not in file:
                        zipf.write(file_path, file)
                        logger.info(f"Added file to ZIP: {file}")

            # Add all config files directly (no config/ folder)
            config_dir = 'config'
            if os.path.exists(config_dir):
                for file in os.listdir(config_dir):
                    file_path = os.path.join(config_dir, file)
                    if os.path.isfile(file_path) and '__pycache__' not in file:
                        zipf.write(file_path, file)
                        logger.info(f"Added file to ZIP: {file}")

            # Create deployment instructions for Railway
            instructions = f"""
# 🚂 TeleFeed Bot - Package Déploiement COMPLET (Railway + Render)

## 📦 Contenu du Package Mis à Jour
Ce package contient TOUS les fichiers nécessaires pour déployer TeleFeed Bot sur Railway.app ET Render.com avec configuration automatique.

### ✅ Fichiers Inclus (Dernière Version)
- **main_render_fixed.py** - Version corrigée Render.com avec Worker
- **render.yaml** - Configuration Render complète avec PostgreSQL
- **bot/database_auto_setup.py** - Configuration automatique base de données
- **bot/session_manager.py** - Gestionnaire de sessions PostgreSQL
- **RENDER_DATABASE_SETUP.md** - Documentation configuration PostgreSQL
- **railway.json** - Configuration Railway complète
- **Dockerfile + nixpacks.toml** - Configuration conteneur
- **Tous les modules bot/** - Code complet du bot

## 🚀 Instructions de Déploiement

### Option 1: Railway.app
1. Créer repository GitHub et uploader tous les fichiers
2. Connecter Railway → GitHub → Sélectionner le repository
3. Variables d'environnement Railway :
```
API_ID=29177661
API_HASH=a8639172fa8d35dbfd8ea46286d349ab
BOT_TOKEN=8168829272:AAEdBli_8E0Du_uHVTGLRLCN6KV7Gwox0WQ
ADMIN_ID=1190237801
RAILWAY_DEPLOYMENT=true
REPLIT_URL=https://telefeed-bot.kouamappoloak.repl.co
```

### Option 2: Render.com (NOUVEAU)
1. Utiliser le fichier **render.yaml** pour Blueprint Deployment
2. PostgreSQL configuré automatiquement
3. Variables d'environnement automatiques via render.yaml
4. Lancer avec **main_render_fixed.py**

### 🔄 Configuration Automatique Render PostgreSQL
- **Base de données** : Créée automatiquement (telefeed_db)
- **Tables** : Configurées automatiquement au démarrage
- **Connexion** : Test automatique + fallback JSON si échec
- **Sessions** : Persistantes en PostgreSQL

### 4. Fonctionnalités Automatiques
✅ Communication automatique Railway/Render ↔ Replit ↔ Bot
✅ Configuration automatique PostgreSQL (Render)
✅ Notification de déploiement réussi dans Telegram
✅ Système de maintien d'activité intelligent
✅ Réveil automatique des plateformes
✅ Redirections automatiques persistantes
✅ Interface admin complète (/railway, /render commands)

### 5. Déploiement One-Click
- **Railway** : Détection automatique railway.json
- **Render** : Blueprint deployment avec render.yaml
- **Base de données** : Configuration automatique PostgreSQL
- **Notification** : Message de succès automatique dans Telegram

## 📞 Vérification
Une fois déployé :
- **Railway** : `/railway` dans le bot
- **Render** : `/render` dans le bot (nouveau)

Package créé le : {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}
Communication Railway/Render ↔ Replit ↔ Bot : ACTIVE
Base de données PostgreSQL : AUTO-CONFIGURÉE

## 🆕 Nouvelles Fonctionnalités
- ✅ Support Render.com avec PostgreSQL
- ✅ Configuration automatique base de données
- ✅ Sessions persistantes PostgreSQL
- ✅ Fallback JSON si PostgreSQL indisponible
- ✅ Blueprint deployment Render
- ✅ Worker Render (pas Web Service)

## Support
Pour toute assistance, contactez le support TeleFeed.
            """

            zipf.writestr("DEPLOYMENT_INSTRUCTIONS.md", instructions)

            # Create .env.example if it doesn't exist
            env_example = """
# TeleFeed Bot Configuration
API_ID=your_api_id_here
API_HASH=your_api_hash_here
BOT_TOKEN=your_bot_token_here
DATABASE_URL=postgresql://user:password@host:port/database
ADMIN_ID=your_admin_id_here
            """

            if not os.path.exists('.env.example'):
                zipf.writestr(".env.example", env_example)

        logger.info(f"Deployment ZIP created: {zip_path}")
        return zip_path

    except Exception as e:
        logger.error(f"Error creating deployment ZIP: {e}")
        return None

async def is_premium_user(user_id):
    """Check if user has premium access"""
    from bot.database import is_user_licensed
    return await is_user_licensed(user_id)