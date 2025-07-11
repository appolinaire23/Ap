import logging
import os
import shutil
from telethon import events
from datetime import datetime

logger = logging.getLogger(__name__)

async def handle_deploy(event, client):
    """
    Handle deployment command - sends the complete multi-platform package
    Premium feature for licensed users
    """
    try:
        user_id = event.sender_id
        
        # Check if user has premium access
        if not await is_premium_user(user_id):
            await event.respond("❌ **Accès premium requis**\n\nCette fonctionnalité est réservée aux utilisateurs premium.\nUtilisez `/valide` pour activer votre licence.")
            return
        
        await event.respond("📦 **Préparation du package Render.com COMPLET...**\n\n⏳ Création du package avec TOUTES les fonctionnalités du bot...")
        
        # Create the complete Render.com package
        import subprocess
        result = subprocess.run(['python', 'create_render_complete_package.py'], capture_output=True, text=True, cwd='.')
        
        # Find the generated ZIP file (with timestamp)
        import glob
        zip_files = glob.glob('TeleFeed_Render_COMPLETE_*.zip')
        
        if zip_files:
            # Get the newest file
            zip_path = max(zip_files, key=os.path.getctime)
            
            # Get file size for verification
            file_size = os.path.getsize(zip_path)
            size_mb = file_size / (1024 * 1024)
            
            # Send the ZIP file
            await client.send_file(
                user_id,
                zip_path,
                caption=f"""🌐 **Package Render.com COMPLET - {size_mb:.1f} MB**

🎯 **TOUTES LES FONCTIONNALITÉS INCLUSES**
• Licences, paiements, connexions
• Redirections, transformations, filtres  
• Administration complète
• Communication automatique

📦 **Configuration Render.com :**
• Background Worker optimisé
• Point d'entrée : main_render_fixed.py
• PostgreSQL + fallback JSON
• Documentation complète

✅ **Corrections appliquées - Prêt déploiement**""",
                attributes=[],
                force_document=True
            )
            
            logger.info(f"Complete multi-platform package sent to user {user_id} - Size: {size_mb:.1f} MB")
            
            # Clean up old zip files after sending
            for old_zip in zip_files:
                try:
                    os.remove(old_zip)
                except:
                    pass
            
        else:
            await event.respond("❌ **Package non disponible**\n\nLe package de déploiement n'a pas pu être généré. Veuillez réessayer.")
            
    except Exception as e:
        logger.error(f"Error in deploy handling: {e}")
        await event.respond("❌ Erreur lors du traitement du déploiement. Veuillez réessayer.")

async def is_premium_user(user_id):
    """Check if user has premium access"""
    # For now, allow admin user
    ADMIN_ID = int(os.getenv('ADMIN_ID', '1190237801'))
    return user_id == ADMIN_ID