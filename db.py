import sqlite3
from typing import Optional, Any

DB_NAME = 'hotel_bot.db'

class Database:
    def __init__(self, db_name: str = DB_NAME):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS account_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT NOT NULL,
                session_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS new_listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id TEXT NOT NULL,
                data TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    # --- Account Sessions ---
    def add_account_session(self, account_id: str, session_data: str):
        self.cursor.execute(
            'INSERT INTO account_sessions (account_id, session_data) VALUES (?, ?)',
            (account_id, session_data)
        )
        self.conn.commit()

    def get_account_session(self, account_id: str) -> Optional[Any]:
        self.cursor.execute(
            'SELECT * FROM account_sessions WHERE account_id = ? ORDER BY created_at DESC LIMIT 1',
            (account_id,)
        )
        return self.cursor.fetchone()

    # --- New Listings ---
    def add_new_listing(self, listing_id: str, data: str, status: str = 'pending'):
        self.cursor.execute(
            'INSERT INTO new_listings (listing_id, data, status) VALUES (?, ?, ?)',
            (listing_id, data, status)
        )
        self.conn.commit()

    def get_new_listing(self, listing_id: str) -> Optional[Any]:
        self.cursor.execute(
            'SELECT * FROM new_listings WHERE listing_id = ?',
            (listing_id,)
        )
        return self.cursor.fetchone()

    def update_listing_status(self, listing_id: str, status: str):
        self.cursor.execute(
            'UPDATE new_listings SET status = ? WHERE listing_id = ?',
            (status, listing_id)
        )
        self.conn.commit()

    def close(self):
        self.conn.close() 