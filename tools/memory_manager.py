import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]

class MemoryManager:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path) if db_path else PROJECT_ROOT / "data" / "user_memory.db"
        self._init_db()

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS user_profile (key TEXT PRIMARY KEY, value TEXT, category TEXT, updated_at DATETIME)")
            cursor.execute("CREATE TABLE IF NOT EXISTS interaction_history (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, query TEXT, response TEXT, metadata TEXT)")

    def save_profile_fact(self, key, value, category="general"):
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO user_profile (key, value, category, updated_at) VALUES (?, ?, ?, ?)", 
                           (key, value, category, datetime.now().isoformat()))

    def get_profile_fact(self, key):
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM user_profile WHERE key = ?", (key,))
            result = cursor.fetchone()
            return result[0] if result else None

    def get_all_profile_context(self):
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM user_profile")
            facts = cursor.fetchall()
            return "\n".join([f"{k}: {v}" for k, v in facts])

    def add_interaction(self, query, response, metadata=None):
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO interaction_history (timestamp, query, response, metadata) VALUES (?, ?, ?, ?)", 
                           (datetime.now().isoformat(), query, response, json.dumps(metadata)))

    def get_recent_history(self, limit=5):
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT query, response FROM interaction_history ORDER BY timestamp DESC LIMIT ?", (limit,))
            history = cursor.fetchall()
            return "\n".join([f"User: {q}\nAI: {r}" for q, r in reversed(history)])

if __name__ == "__main__":
    mem = MemoryManager()
    mem.save_profile_fact("region", "Vale do Paraíba", "location")
    mem.save_profile_fact("soil_type", "Latossolo Vermelho", "technical")
    print("Profile Context:\n", mem.get_all_profile_context())
    mem.add_interaction("Qual a dose de N?", "A dose recomendada é 100kg/ha")
    print("\nRecent History:\n", mem.get_recent_history())
