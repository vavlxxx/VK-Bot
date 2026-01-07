import aiosqlite
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "bot.db"

class Database:
    def __init__(self):
        self.db_path = str(DB_PATH)

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 0
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_id) REFERENCES chats (id)
                )
            """)
            # Ensure only one active chat per user restriction is handled in logic, 
            # but let's add an index for performance
            await db.execute("CREATE INDEX IF NOT EXISTS idx_chats_user_id ON chats(user_id)")
            await db.commit()

    async def create_chat(self, user_id: int, title: str = "New Chat") -> int:
        async with aiosqlite.connect(self.db_path) as db:
            # Deactivate previous chats
            await db.execute("UPDATE chats SET is_active = 0 WHERE user_id = ? AND is_active = 1", (user_id,))
            
            cursor = await db.execute(
                "INSERT INTO chats (user_id, title, is_active) VALUES (?, ?, 1)",
                (user_id, title)
            )
            await db.commit()
            return cursor.lastrowid

    async def get_active_chat(self, user_id: int) -> Optional[int]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id FROM chats WHERE user_id = ? AND is_active = 1 ORDER BY id DESC LIMIT 1",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    async def set_active_chat(self, user_id: int, chat_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE chats SET is_active = 0 WHERE user_id = ?", (user_id,))
            await db.execute("UPDATE chats SET is_active = 1 WHERE id = ? AND user_id = ?", (chat_id, user_id))
            await db.commit()

    async def get_user_chats(self, user_id: int, limit: int = 10) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM chats WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def add_message(self, chat_id: int, role: str, content: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
                (chat_id, role, content)
            )
            await db.commit()

    async def get_chat_messages(self, chat_id: int, limit: int = 20) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            # We want chronological order for the AI context, but we might fetch last N
            # So fetch DESC limit N then reverse
            async with db.execute(
                "SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
                (chat_id, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                messages = [dict(row) for row in rows]
                return messages[::-1] # Reverse to get chronological order

    async def update_chat_title(self, chat_id: int, title: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE chats SET title = ? WHERE id = ?", (title, chat_id))
            await db.commit()

# Singleton
db = Database()
