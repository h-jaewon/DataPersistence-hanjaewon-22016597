import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "orders.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT    NOT NULL,
                state      TEXT    NOT NULL DEFAULT '주문접수',
                created_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
        """)
        # 상태 변경 이력 - 이것이 영속성의 핵심
        conn.execute("""
            CREATE TABLE IF NOT EXISTS state_history (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id   INTEGER NOT NULL,
                from_state TEXT,
                to_state   TEXT    NOT NULL,
                changed_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (order_id) REFERENCES orders(id)
            )
        """)
