import sqlite3
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class AdminDB:
    def __init__(self):
        self.db_path = "database.db"  # Sesuaikan dengan path database Anda

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def get_admin(self, discord_id: str) -> Optional[Dict]:
        """Get admin data from database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT discord_id, username, is_active 
                FROM admins 
                WHERE discord_id = ?
            """, (discord_id,))
            
            result = cursor.fetchone()
            
            if result:
                return {
                    "discord_id": result[0],
                    "username": result[1],
                    "is_active": bool(result[2])
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting admin: {e}")
            return None
            
        finally:
            if 'conn' in locals():
                conn.close()

    def create_admin_table(self):
        """Create admins table if not exists"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    discord_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error creating admin table: {e}")
            raise
            
        finally:
            if 'conn' in locals():
                conn.close()

# Create singleton instance
admin_db = AdminDB()