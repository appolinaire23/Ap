"""
Gestionnaire de sessions amélioré pour Render.com
Résout les erreurs PostgreSQL et gère les sessions sans base de données
"""

import json
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SessionManagerRender:
    """Gestionnaire de sessions pour Render.com avec fallback"""
    
    def __init__(self):
        self.sessions_file = 'user_data.json'  # Fallback vers fichier JSON
        self.db_connection = None
        self.use_postgres = False
        
        # Essayer de se connecter à PostgreSQL si disponible
        self._try_postgres_connection()
    
    def _try_postgres_connection(self):
        """Essayer de se connecter à PostgreSQL avec gestion d'erreur"""
        try:
            import psycopg2
            from urllib.parse import urlparse
            
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                logger.info("DATABASE_URL non définie, utilisation du fichier JSON")
                return
            
            # Parse URL PostgreSQL
            url = urlparse(database_url)
            
            # Connexion PostgreSQL
            self.db_connection = psycopg2.connect(
                host=url.hostname,
                port=url.port,
                user=url.username,
                password=url.password,
                database=url.path[1:],  # Supprimer le '/' initial
                sslmode='require'
            )
            
            self.use_postgres = True
            logger.info("✅ Connexion PostgreSQL établie pour Render")
            
            # Créer la table si elle n'existe pas
            self._create_sessions_table()
            
        except Exception as e:
            logger.warning(f"PostgreSQL non disponible, fallback vers JSON: {e}")
            self.use_postgres = False
    
    def _create_sessions_table(self):
        """Créer la table sessions si elle n'existe pas"""
        try:
            if not self.use_postgres:
                return
                
            cursor = self.db_connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    phone VARCHAR(20) NOT NULL,
                    session_file VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, phone)
                )
            """)
            self.db_connection.commit()
            cursor.close()
            logger.info("✅ Table sessions créée/vérifiée")
            
        except Exception as e:
            logger.error(f"Erreur création table: {e}")
    
    async def save_session(self, user_id, phone, session_file):
        """Sauvegarder une session"""
        try:
            if self.use_postgres:
                return await self._save_session_postgres(user_id, phone, session_file)
            else:
                return await self._save_session_json(user_id, phone, session_file)
                
        except Exception as e:
            logger.error(f"Erreur sauvegarde session: {e}")
            # Fallback vers JSON en cas d'erreur PostgreSQL
            return await self._save_session_json(user_id, phone, session_file)
    
    async def _save_session_postgres(self, user_id, phone, session_file):
        """Sauvegarder en PostgreSQL"""
        cursor = self.db_connection.cursor()
        cursor.execute("""
            INSERT INTO user_sessions (user_id, phone, session_file, last_used)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, phone) 
            DO UPDATE SET session_file = %s, last_used = %s
        """, (user_id, phone, session_file, datetime.now(), session_file, datetime.now()))
        
        self.db_connection.commit()
        cursor.close()
        logger.info(f"Session PostgreSQL sauvée: {phone}")
    
    async def _save_session_json(self, user_id, phone, session_file):
        """Sauvegarder en JSON (fallback)"""
        try:
            # Charger les données existantes
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {}
            
            # Ajouter/mettre à jour la session
            user_key = str(user_id)
            if user_key not in data:
                data[user_key] = {}
            
            data[user_key][phone] = {
                'session_file': session_file,
                'created_at': datetime.now().isoformat(),
                'last_used': datetime.now().isoformat()
            }
            
            # Sauvegarder
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Session JSON sauvée: {phone}")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde JSON: {e}")
    
    async def get_user_sessions(self, user_id):
        """Récupérer les sessions d'un utilisateur"""
        try:
            if self.use_postgres:
                return await self._get_sessions_postgres(user_id)
            else:
                return await self._get_sessions_json(user_id)
                
        except Exception as e:
            logger.error(f"Erreur récupération sessions: {e}")
            # Fallback vers JSON
            return await self._get_sessions_json(user_id)
    
    async def _get_sessions_postgres(self, user_id):
        """Récupérer depuis PostgreSQL"""
        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT phone, session_file, created_at, last_used
            FROM user_sessions 
            WHERE user_id = %s
            ORDER BY last_used DESC
        """, (user_id,))
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'phone': row[0],
                'session_file': row[1],
                'created_at': row[2].strftime('%d/%m/%Y %H:%M:%S') if row[2] else 'N/A',
                'last_used': row[3].strftime('%d/%m/%Y %H:%M:%S') if row[3] else 'N/A'
            })
        
        cursor.close()
        return sessions
    
    async def _get_sessions_json(self, user_id):
        """Récupérer depuis JSON"""
        try:
            if not os.path.exists(self.sessions_file):
                return []
            
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            user_key = str(user_id)
            if user_key not in data:
                return []
            
            sessions = []
            for phone, session_data in data[user_key].items():
                sessions.append({
                    'phone': phone,
                    'session_file': session_data.get('session_file', ''),
                    'created_at': session_data.get('created_at', 'N/A'),
                    'last_used': session_data.get('last_used', 'N/A')
                })
            
            return sessions
            
        except Exception as e:
            logger.error(f"Erreur lecture JSON: {e}")
            return []
    
    async def cleanup_old_sessions(self, days_old=7):
        """Nettoyer les anciennes sessions"""
        try:
            if self.use_postgres:
                await self._cleanup_postgres(days_old)
            else:
                await self._cleanup_json(days_old)
                
        except Exception as e:
            logger.error(f"Erreur nettoyage sessions: {e}")
    
    async def _cleanup_postgres(self, days_old):
        """Nettoyer PostgreSQL"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        cursor = self.db_connection.cursor()
        cursor.execute("""
            DELETE FROM user_sessions 
            WHERE last_used < %s
        """, (cutoff_date,))
        self.db_connection.commit()
        cursor.close()
    
    async def _cleanup_json(self, days_old):
        """Nettoyer JSON"""
        # Implémentation du nettoyage JSON si nécessaire
        pass

# Instance globale
session_manager_render = SessionManagerRender()