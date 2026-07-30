import sqlite3
import os
import time

class HistoryDB:
    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    date_str TEXT,
                    model TEXT,
                    prompt TEXT,
                    negative_prompt TEXT,
                    width INTEGER,
                    height INTEGER,
                    seed TEXT,
                    output_path TEXT,
                    full_cmd TEXT
                )
            """)
            conn.commit()

    def add_entry(self, model, prompt, negative_prompt, width, height, seed, output_path, full_cmd):
        now = time.time()
        date_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO history (timestamp, date_str, model, prompt, negative_prompt, width, height, seed, output_path, full_cmd)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (now, date_str, model, prompt, negative_prompt, width, height, str(seed), output_path, full_cmd))
            conn.commit()

    def get_all(self, limit=100):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, date_str, model, prompt, negative_prompt, width, height, seed, output_path, full_cmd
                FROM history
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return rows

    def search(self, query, limit=100):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            search_pattern = f"%{query}%"
            cursor.execute("""
                SELECT id, date_str, model, prompt, negative_prompt, width, height, seed, output_path, full_cmd
                FROM history
                WHERE prompt LIKE ? OR model LIKE ? OR output_path LIKE ?
                ORDER BY id DESC
                LIMIT ?
            """, (search_pattern, search_pattern, search_pattern, limit))
            return cursor.fetchall()

    def clear(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM history")
            conn.commit()
