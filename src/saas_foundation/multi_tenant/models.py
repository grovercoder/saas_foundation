from dataclasses import dataclass
from datetime import datetime


@dataclass
class Account:
    id: int
    name: str
    created_at: datetime | None = None


@dataclass
class User:
    id: int
    account_id: int
    username: str
    password_hash: str
    reset_token: str | None = None
    reset_token_created_at: datetime | None = None
    created_at: datetime | None = None
