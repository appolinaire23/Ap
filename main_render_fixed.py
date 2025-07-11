"""
Point d'entrée principal pour le déploiement Render.com
Configuration Worker avec redirections actives
CORRECTION POUR RENDER: Worker au lieu de Web Service
"""

import os
import asyncio
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement directement
load_dotenv()

# Configuration Render directe (sans config/)
API_ID = int(os.getenv('API_ID', '29177661'))
API_HASH = os.getenv('API_HASH', 'a8639172fa8d35dbfd8ea46286d349ab')
BOT_TOKEN = os.getenv('BOT_TOKEN', '8168829272:AAEdBli_8E0Du_uHVTGLRLCN6KV7Gwox0WQ')
ADMIN_ID = int(os.getenv('ADMIN_ID', '1190237801'))

# Configuration Render
RENDER_PORT = int(os.getenv('PORT', 10000))
REPLIT_URL = os.getenv('REPLIT_URL', 'https://telefeed-bot.kouamappoloak.repl.co')

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start_with_render_worker():
    """Démarrage avec Render Worker (pas Web Service)"""
    try:
        print("🌐 Démarrage TeleFeed Bot sur Render.com (Worker)")

        # Import direct des handlers
        from telethon import TelegramClient, events
        from bot.handlers import (
            start, valide, payer_semaine, payer_mois, payer, deposer,
            connect, redirection, transformation, whitelist, blacklist,
            chats, help_command, admin_command, confirm_command,
            generate_command, users_command, stats_command, sessions_command,
            railway_command, handle_unknown_command
        )

        # Créer le client Telegram
        client = TelegramClient('bot', API_ID, API_HASH)

        # Connexion avec le token du bot
        await client.start(bot_token=BOT_TOKEN)

        print(f"🌐 Bot Render démarré sur Worker")
        print(f"🔗 Communication avec Replit: {REPLIT_URL}")

        # Enregistrer tous les handlers
        client.add_event_handler(start, events.NewMessage(pattern='/start'))
        client.add_event_handler(valide, events.NewMessage(pattern='/valide'))
        client.add_event_handler(payer_semaine, events.NewMessage(pattern='/payer une semaine'))
        client.add_event_handler(payer_mois, events.NewMessage(pattern='/payer un mois'))
        client.add_event_handler(payer, events.NewMessage(pattern='/payer'))
        client.add_event_handler(deposer, events.NewMessage(pattern='/deposer'))
        client.add_event_handler(connect, events.NewMessage(pattern='/connect'))
        client.add_event_handler(redirection, events.NewMessage(pattern='/redirection'))
        client.add_event_handler(transformation, events.NewMessage(pattern='/transformation'))
        client.add_event_handler(whitelist, events.NewMessage(pattern='/whitelist'))
        client.add_event_handler(blacklist, events.NewMessage(pattern='/blacklist'))
        client.add_event_handler(chats, events.NewMessage(pattern='/chats'))
        client.add_event_handler(help_command, events.NewMessage(pattern='/help'))
        client.add_event_handler(admin_command, events.NewMessage(pattern='/admin'))
        client.add_event_handler(confirm_command, events.NewMessage(pattern='/confirm'))
        client.add_event_handler(generate_command, events.NewMessage(pattern='/generate'))
        client.add_event_handler(users_command, events.NewMessage(pattern='/users'))
        client.add_event_handler(stats_command, events.NewMessage(pattern='/stats'))
        client.add_event_handler(sessions_command, events.NewMessage(pattern='/sessions'))
        client.add_event_handler(railway_command, events.NewMessage(pattern='/railway'))
        client.add_event_handler(handle_unknown_command, events.NewMessage)

        logger.info("🚀 Bot TeleFeed démarré avec succès!")

        # Démarrer la restauration des redirections
        try:
            from bot.simple_restorer import SimpleRedirectionRestorer
            restorer = SimpleRedirectionRestorer()
            asyncio.create_task(restorer.start_restoration())
            logger.info("🔄 Système de restauration automatique des redirections activé")
        except Exception as e:
            logger.error(f"Erreur restauration redirections: {e}")

        # Démarrer le système de communication automatique
        try:
            from auto_communication import AutoCommunicationSystem
            auto_comm = AutoCommunicationSystem(client, ADMIN_ID)
            asyncio.create_task(auto_comm.start_auto_communication())
            logger.info("🔄 Système de communication automatique démarré")
        except Exception as e:
            logger.error(f"Erreur communication automatique: {e}")

        # Démarrer le système Render keep-alive
        try:
            from render_keep_alive import RenderKeepAliveSystem
            render_keep_alive = RenderKeepAliveSystem(client, ADMIN_ID)
            asyncio.create_task(render_keep_alive.start_render_keep_alive())

            # Notifier le déploiement réussi
            await render_keep_alive.notify_deployment_success()
        except Exception as e:
            logger.error(f"Erreur keep-alive Render: {e}")

        # Exécuter le bot
        await client.run_until_disconnected()

    except Exception as e:
        logger.error(f"Erreur démarrage Render: {e}")
        # En cas d'erreur, essayer de démarrer quand même
        import sys
        sys.exit(1)

if __name__ == "__main__":
    # Configuration Render
    os.environ['RENDER_DEPLOYMENT'] = 'true'
    os.environ['PORT'] = str(RENDER_PORT)

    print("✅ Configuration Render.com activée")
    print(f"🌐 Port Render: {RENDER_PORT}")

    # Configuration automatique de la base de données
    try:
        from bot.database_auto_setup import setup_render_database, test_database_connection
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        print("🔄 Test de connexion base de données PostgreSQL...")
        db_connected = loop.run_until_complete(test_database_connection())

        if db_connected:
            print("✅ Connexion PostgreSQL réussie")
            print("🔄 Configuration automatique des tables...")
            setup_success = loop.run_until_complete(setup_render_database())

            if setup_success:
                print("✅ Base de données PostgreSQL configurée automatiquement")
            else:
                print("⚠️ Configuration automatique échouée - fallback JSON activé")
        else:
            print("⚠️ Connexion PostgreSQL échouée - fallback JSON activé")

    except Exception as e:
        print(f"⚠️ Erreur configuration automatique base de données: {e}")
        print("🔄 Fallback vers base de données JSON...")

    # Démarrer avec Render
    asyncio.run(start_with_render_worker())