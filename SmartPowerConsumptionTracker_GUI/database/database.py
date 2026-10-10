import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class Database:
    def __init__(self, database_path: str | Path | None = None):
        self.database_path = (
            Path(database_path)
            if database_path is not None
            else Path(__file__).resolve().parent / "power.db"
        )

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path)
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            with connection:  # commit on success, rollback on error
                yield connection
        finally:
            connection.close()

    def create_tables(self) -> None:
        try:
            self._create_tables()
        except sqlite3.DatabaseError as error:
            # Corrupt / not-a-database file: set it aside and start fresh.
            if "malformed" not in str(error) and "not a database" not in str(error):
                raise
            backup = self.database_path.with_name(
                f"{self.database_path.name}.corrupt-{int(time.time())}"
            )
            self.database_path.replace(backup)
            for suffix in ("-journal", "-wal", "-shm"):
                Path(str(self.database_path) + suffix).unlink(missing_ok=True)
            print(f"Corrupt database moved to {backup.name}; created a new one.")
            self._create_tables()

    def _create_tables(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS appliances (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    watts REAL NOT NULL CHECK (watts > 0),
                    hours REAL NOT NULL CHECK (hours > 0 AND hours <= 24)
                );
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )

    # --- tiny key/value store (used to remember the electricity rate) ---
    def get_setting(self, key: str, default: str) -> str:
        with self.connect() as c:
            row = c.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row[0] if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self.connect() as c:
            c.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )





