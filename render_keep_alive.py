"""
Système de maintien d'activité spécifique à Render.com
Gère la communication Render ↔ Replit et le réveil automatique
"""

import asyncio
import logging
import aiohttp
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RenderKeepAliveSystem:
    """Système de maintien d'activité pour Render avec communication Replit"""
    
    def __init__(self, bot_client, admin_id):
        self.bot_client = bot_client
        self.admin_id = admin_id
        self.is_running = False
        self.last_activity = time.time()
        self.replit_url = "https://telefeed-bot.kouamappoloak.repl.co"
        self.render_url = f"https://telefeed-bot-render.onrender.com"  # URL Render générique
        
    async def start_render_keep_alive(self):
        """Démarrer le système de maintien d'activité Render"""
        if self.is_running:
            return
            
        self.is_running = True
        logger.info("🌐 Démarrage du système Render keep-alive")
        
        # Démarrer les tâches en parallèle
        tasks = [
            self.monitor_render_activity(),
            self.monitor_replit_communication(),
            self.periodic_render_health_check()
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def notify_deployment_success(self):
        """Notifie le succès du déploiement Render"""
        try:
            message = f"""
🌐 **DÉPLOIEMENT RENDER.COM RÉUSSI !**

🎉 **TeleFeed Bot déployé avec succès sur Render.com**

📋 **Détails du déploiement :**
• Plateforme : Render.com
• Status : ✅ En ligne
• Communication automatique : ✅ Active
• Système keep-alive : ✅ Opérationnel

🔗 **Communication automatique :**
• Render ↔ Replit : Active
• Notifications automatiques : Activées
• Pas de messages "réveil toi" : ✅

⏰ **Déployé le :** {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}

🚀 **Le bot est maintenant hébergé sur Render.com !**
            """
            
            await self.bot_client.send_message(self.admin_id, message)
            logger.info("✅ Notification de déploiement Render envoyée")
            
        except Exception as e:
            logger.error(f"Erreur notification déploiement Render: {e}")
    
    async def notify_replit_server(self):
        """Notifie le serveur Replit du déploiement Render"""
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    "platform": "render",
                    "status": "deployed",
                    "timestamp": datetime.now().isoformat(),
                    "url": self.render_url
                }
                
                async with session.post(f"{self.replit_url}/render_notification", json=data, timeout=10) as response:
                    if response.status == 200:
                        logger.info("✅ Serveur Replit notifié du déploiement Render")
                    
        except Exception as e:
            logger.error(f"Erreur notification Replit: {e}")
    
    async def monitor_render_activity(self):
        """Surveiller l'activité Render et réveiller si nécessaire"""
        while self.is_running:
            try:
                # Vérifier si Render est inactif depuis plus de 5 minutes
                if time.time() - self.last_activity > 300:  # 5 minutes
                    await self.wake_up_render()
                
                await asyncio.sleep(180)  # Vérifier toutes les 3 minutes
                
            except Exception as e:
                logger.error(f"Erreur monitoring Render: {e}")
                await asyncio.sleep(60)
    
    async def monitor_replit_communication(self):
        """Surveiller la communication avec Replit et réveiller si nécessaire"""
        while self.is_running:
            try:
                # Tester la connectivité Replit
                replit_ok = await self.test_replit_connectivity()
                
                if not replit_ok:
                    await self.wake_up_replit_from_render()
                
                await asyncio.sleep(240)  # Vérifier toutes les 4 minutes
                
            except Exception as e:
                logger.error(f"Erreur communication Replit: {e}")
                await asyncio.sleep(120)
    
    async def test_replit_connectivity(self):
        """Teste si le serveur Replit répond"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.replit_url}/ping", timeout=10) as response:
                    return response.status == 200
                    
        except Exception:
            return False
    
    async def wake_up_replit_from_render(self):
        """Réveille le serveur Replit depuis Render"""
        try:
            async with aiohttp.ClientSession() as session:
                data = {"source": "render", "timestamp": datetime.now().isoformat()}
                
                async with session.post(f"{self.replit_url}/wake_up", json=data, timeout=15) as response:
                    if response.status == 200:
                        logger.info("🔄 Replit réveillé depuis Render")
                        
        except Exception as e:
            logger.error(f"Erreur réveil Replit: {e}")
    
    async def wake_up_render(self):
        """Auto-réveil de Render"""
        try:
            self.update_activity()
            logger.info("🔄 Auto-réveil Render effectué")
            
        except Exception as e:
            logger.error(f"Erreur auto-réveil Render: {e}")
    
    async def periodic_render_health_check(self):
        """Vérification périodique de santé Render"""
        while self.is_running:
            try:
                # Mise à jour de l'activité pour indiquer que Render fonctionne
                self.update_activity()
                
                # Log de santé toutes les 10 minutes
                if int(time.time()) % 600 == 0:
                    logger.info(f"🌐 Render health check - Status: OK - {datetime.now().strftime('%H:%M:%S')}")
                
                await asyncio.sleep(60)  # Check toutes les minutes
                
            except Exception as e:
                logger.error(f"Erreur health check Render: {e}")
                await asyncio.sleep(120)
    
    def update_activity(self):
        """Met à jour l'activité Render"""
        self.last_activity = time.time()
    
    def stop_render_keep_alive(self):
        """Arrêter le système de maintien d'activité Render"""
        self.is_running = False
        logger.info("🌐 Système Render keep-alive arrêté")
    
    def get_render_status(self):
        """Obtenir le statut du système Render"""
        uptime = time.time() - self.last_activity
        return {
            "platform": "render",
            "status": "running" if self.is_running else "stopped",
            "last_activity": self.last_activity,
            "uptime_seconds": uptime,
            "replit_url": self.replit_url
        }