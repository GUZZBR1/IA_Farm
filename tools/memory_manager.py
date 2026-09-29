import sqlite3
import json
from datetime import datetime
import os

class MemoryManager:
    def __init__(self, db_path="data/user_memory.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS user_profile (key TEXT PRIMARY KEY, value TEXT, category TEXT, updated_at DATETIME)")
            cursor.execute("CREATE TABLE IF NOT EXISTS interaction_history (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, query TEXT, response TEXT, metadata TEXT)")
            conn.commit()

    def save_profile_fact(self, key, value, category="general"):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO user_profile (key, value, category, updated_at) VALUES (?, ?, ?, ?)", 
                           (key, value, category, datetime.now().isoformat()))
            conn.commit()

    def get_profile_fact(self, key):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM user_profile WHERE key = ?", (key,))
            result = cursor.fetchone()
            return result[0] if result else None

    def get_all_profile_context(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM user_profile")
            facts = cursor.fetchall()
            return "\n".join([f"{k}: {v}" for k, v in facts])

    def add_interaction(self, query, response, metadata=None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO interaction_history (timestamp, query, response, metadata) VALUES (?, ?, ?, ?)", 
                           (datetime.now().isoformat(), query, response, json.dumps(metadata)))
            conn.commit()

    def get_recent_history(self, limit=5):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT query, response FROM interaction_history ORDER BY timestamp DESC LIMIT ?", (limit,))
            history = cursor.fetchall()
            return "\n".join([f"User: {q}\nAI: {r}" for q, r in reversed(history)])

if __name__ == "__main__":
    import sys
    # Use a fixed path for testing to avoid relative path issues
    test_db = "/home/guzzbr/meus-projetos/IA_Farm/data/user_memory.db"
    mem = MemoryManager(db_path=test_db)
    mem.save_profile_fact("region", "Vale do Paraíba", "location")
    mem.save_profile_fact("soil_type", "Latossolo Vermelho", "technical")
    print("Profile Context:\n", mem.get_all_profile_context())
    mem.add_interaction("Qual a dose de N?", "A dose recomendada é 100kg/ha")
    print("\nRecent History:\n", mem.get_recent_history())
