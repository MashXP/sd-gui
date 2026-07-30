import sqlite3
import os
import time

NEW_COLUMNS = {
    "generation_time": "REAL",
    "mode": "TEXT",
    "steps": "INTEGER",
    "cfg_scale": "REAL",
    "sampler": "TEXT",
}

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
            cursor.execute("PRAGMA table_info(history)")
            existing = {row[1] for row in cursor.fetchall()}
            for col, coltype in NEW_COLUMNS.items():
                if col not in existing:
                    cursor.execute(f"ALTER TABLE history ADD COLUMN {col} {coltype}")
            conn.commit()

    def add_entry(self, model, prompt, negative_prompt, width, height, seed,
                  output_path, full_cmd, generation_time=None, mode=None,
                  steps=None, cfg_scale=None, sampler=None):
        now = time.time()
        date_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO history (timestamp, date_str, model, prompt, negative_prompt,
                                     width, height, seed, output_path, full_cmd,
                                     generation_time, mode, steps, cfg_scale, sampler)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (now, date_str, model, prompt, negative_prompt, width, height,
                  str(seed), output_path, full_cmd, generation_time, mode,
                  steps, cfg_scale, sampler))
            conn.commit()

    def count_all(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM history")
            return cursor.fetchone()[0]

    def get_all(self, limit=100, offset=0):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, date_str, model, prompt, negative_prompt,
                       width, height, seed, output_path, full_cmd,
                       generation_time, mode, steps, cfg_scale, sampler
                FROM history
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            return cursor.fetchall()

    def search(self, query, limit=100):
        with self._get_connection() as conn:
            search_pattern = f"%{query}%"
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, date_str, model, prompt, negative_prompt,
                       width, height, seed, output_path, full_cmd,
                       generation_time, mode, steps, cfg_scale, sampler
                FROM history
                WHERE prompt LIKE ? OR model LIKE ? OR output_path LIKE ?
                ORDER BY id DESC
                LIMIT ?
            """, (search_pattern, search_pattern, search_pattern, limit))
            return cursor.fetchall()

    def delete_entry(self, entry_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM history WHERE id = ?", (entry_id,))
            conn.commit()

    def delete_entries(self, entry_ids):
        if not entry_ids:
            return
        placeholders = ",".join("?" for _ in entry_ids)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM history WHERE id IN ({placeholders})", entry_ids)
            conn.commit()

    def clear(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM history")
            conn.commit()
