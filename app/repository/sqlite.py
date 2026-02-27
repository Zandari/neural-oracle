import typing
from contextlib import asynccontextmanager
from datetime import datetime

import aiosqlite

from ..models import Message, User
from ..security import verify_access_token
from .base import Repository


class SQLiteRepository(Repository):
    def __init__(self, connection: aiosqlite.Connection) -> None:
        super().__init__()
        self._connection = connection
        self._connection.row_factory = aiosqlite.Row

    @classmethod
    @asynccontextmanager
    async def from_uri(cls, uri: str) -> typing.AsyncGenerator[typing.Self]:
        async with aiosqlite.connect(uri) as connection:
            yield cls(connection)

    async def init_database(self) -> bool:
        await self._init_user_table()
        await self._init_chat_table()
        return self._connection.total_changes > 0

    async def _init_user_table(self) -> None:
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                hashed_access_token TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await self._connection.commit()

    async def _init_chat_table(self) -> None:
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS chat (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                content TEXT NOT NULL,
                is_response INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(user_id) REFERENCES user(id)
            );
        """)
        await self._connection.commit()

    async def get_messages_by_user_id(self, user_id: int) -> list[Message]:
        result: list[Message] = []

        async with self._connection.execute(
            "SELECT * FROM chat WHERE user_id = ? ORDER BY created_at;",
            (user_id,),
        ) as cursor:
            async for row in cursor:
                result.append(Message(
                    created_at=datetime.fromisoformat(row["created_at"]),
                    user_id=row["user_id"],
                    content=row["content"],
                    is_response=row["is_response"] == 1,
                ))

        return result

    async def put_message(self, message: Message) -> bool:
        await self._connection.execute(
            """
            INSERT INTO chat (user_id, content, created_at, is_response)
            VALUES (?, ?, ?, ?);
            """,
            (message.user_id, message.content, message.created_at, message.is_response),
        )
        await self._connection.commit()
        return self._connection.total_changes > 0

    async def get_user_by_access_key(self, access_token: str) -> User | None:

        async with self._connection.execute("SELECT * FROM user;") as cursor:
            async for row in cursor:
                hashed_token = row["hashed_access_token"]
                if verify_access_token(access_token, hashed_token):
                    return User(
                        id=row["id"],
                        name=row["name"],
                        hashed_access_token=hashed_token
                    )
        return None

    async def get_users(self) -> list[User]:
        result: list[User] = []

        async with self._connection.execute("SELECT * FROM user;") as cursor:
            async for row in cursor:
                result.append(User(
                    id=row["id"],
                    name=row["name"],
                    hashed_access_token=row["hashed_access_token"]
                ))

        return result

    async def put_user(self, user: User) -> bool:
        await self._connection.execute(
            "INSERT INTO user (name, hashed_access_token) VALUES (?, ?);",
            (user.name, user.hashed_access_token),
        )
        await self._connection.commit()
        return self._connection.total_changes > 0

    async def delete_user_by_id(self, user_id: int) -> bool:
        await self._connection.execute(
            "DELETE FROM user WHERE id = ?;",
            (user_id,),
        )
        await self._connection.commit()
        return self._connection.total_changes > 0
