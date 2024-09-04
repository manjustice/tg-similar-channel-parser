from datetime import datetime
from enum import Enum
from typing import NamedTuple, Self

from app.utils import get_unix_timestamp


class Channel(NamedTuple):
    name: str
    url: str
    parsed_at: datetime

    readable_fields = ["Channel name", "Channel url", "Comment"]
    MAX_URL_LENGTH = 60

    @classmethod
    def create(cls, name: str, url: str) -> Self | None:
        if name == "Telegram" or url == name:
            return None

        if len(url) > cls.MAX_URL_LENGTH or "t.me" not in url:
            return None

        url = f"https://{url}"
        parsed_at = datetime.now()

        return cls(name, url, parsed_at)


class StatusType(Enum):
    WAITING = "waiting"
    PARSER_USING = "parser_using"
    NOT_WORKING = "not_working"
    PASSWORD_REQUIRED = "password_required"
    INCORRECT_PASSWORD = "incorrect_password"


class TgAccount(NamedTuple):
    session_data: str
    phone_number: str
    password: str | None = None
    status: str | None = None
    waiting_ends: int | None = None

    @classmethod
    def from_dict(cls, dict_: dict) -> Self:
        if not isinstance(dict_, dict):
            return None

        session_data = dict_.get("session_data")
        phone_number = dict_.get("phone_number")

        if session_data is None or phone_number is None:
            raise ValueError("Session data is required")

        password = dict_.get("password")
        status = dict_.get("status")
        waiting_ends = dict_.get("waiting_ends")

        if status is not None:
            status = StatusType(status.lower())

        if status is not None and status == StatusType.WAITING.value:
            if not isinstance(waiting_ends, int):
                raise ValueError(f"Invalid waiting_ends parameter: {waiting_ends}")
            if waiting_ends > get_unix_timestamp():
                return None

        return cls(
            session_data=session_data,
            password=password,
            status=status,
            phone_number=phone_number,
            waiting_ends=waiting_ends
        )
