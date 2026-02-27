from pydantic import BaseModel
from datetime import datetime


class Message(BaseModel):
    created_at: datetime | None
    user_id: int | None
    is_response: bool
    content: str


class MessageCollection(BaseModel):
    content: list[Message]


class User(BaseModel):
    id: int | None
    name: str
    hashed_access_token: str | None
