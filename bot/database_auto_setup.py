
import os
import psycopg2
import logging
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

logger = logging.getLogger(__name__)

async def setup_render_database():
    """Configure automatiquement la base de données PostgreSQL sur Render"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.warning("DATABASE_URL non trouvé - utilisation du fallback JSON")
        return False
    
    try:
        # Connexion à la base de données
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Créer les tables nécessaires
        create_tables_sql = """
        -- Table pour les licences utilisateur
        CREATE TABLE IF NOT EXISTS user_licenses (
            user_id BIGINT PRIMARY KEY,
            license_code VARCHAR(255) NOT NULL,
            validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            active BOOLEAN DEFAULT true
        );
        
        -- Table pour les connexions téléphoniques
        CREATE TABLE IF NOT EXISTS user_connections (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            phone_number VARCHAR(20) NOT NULL,
            connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            active BOOLEAN DEFAULT true,
            UNIQUE(user_id, phone_number)
        );
        
        -- Table pour les redirections
        CREATE TABLE IF NOT EXISTS user_redirections (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            name VARCHAR(255) NOT NULL,
            phone_number VARCHAR(20) NOT NULL,
            channel_name VARCHAR(255),
            source_id BIGINT,
            destination_id BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            active BOOLEAN DEFAULT true,
            UNIQUE(user_id, name)
        );
        
        -- Table pour les sessions Telegram
        CREATE TABLE IF NOT EXISTS telegram_sessions (
            user_id BIGINT PRIMARY KEY,
            phone_number VARCHAR(20) NOT NULL,
            session_data BYTEA,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Table pour les redirections en attente
        CREATE TABLE IF NOT EXISTS pending_redirections (
            user_id BIGINT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            phone_number VARCHAR(20) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Index pour améliorer les performances
        CREATE INDEX IF NOT EXISTS idx_user_connections_user_id ON user_connections(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_redirections_user_id ON user_redirections(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_redirections_phone ON user_redirections(phone_number);
        """
        
        cursor.execute(create_tables_sql)
        
        logger.info("✅ Base de données PostgreSQL configurée automatiquement sur Render")
        
        # Vérifier que les tables ont été créées
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        logger.info(f"📊 Tables créées: {[table[0] for table in tables]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur configuration base de données: {e}")
        return False

async def test_database_connection():
    """Tester la connexion à la base de données"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        return False
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        logger.info("✅ Connexion base de données PostgreSQL réussie")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test connexion base de données échoué: {e}")
        return False
