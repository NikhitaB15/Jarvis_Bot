import os
import sqlite3
from pathlib import Path
from typing import Dict, Any, List

class DatabaseManager:
    """Manages telemetry logging and nudge persistence.
    
    Supports local SQLite logging in data/jarvis_activity.db and can be upgraded
    to PostgreSQL / Supabase via DATABASE_URL environment variables.
    """

    def __init__(self, db_path: str = "data/jarvis_activity.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            # Telemetry sync log
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS telemetry_sync_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    ts TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            # Generated nudges table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS generated_nudges (
                    id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    message TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    suggested_action TEXT,
                    ts TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def save_telemetry_sync(self, client_id: str, platform: str, ts: str, payload_json: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO telemetry_sync_log (client_id, platform, ts, payload_json)
                VALUES (?, ?, ?, ?)
                """,
                (client_id, platform, ts, payload_json),
            )
            conn.commit()

    def save_nudge(self, nudge_id: str, category: str, message: str, priority: str, suggested_action: str, ts: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO generated_nudges (id, category, message, priority, suggested_action, ts)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (nudge_id, category, message, priority, suggested_action, ts),
            )
            conn.commit()

    def get_recent_nudges(self, limit: int = 10) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT id, category, message, priority, suggested_action, ts
                FROM generated_nudges
                ORDER BY ts DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]
