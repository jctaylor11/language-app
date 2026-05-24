from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy import Enum, ForeignKey

from backend.enums import ResultStatus


class Base(DeclarativeBase):
    pass


class Word(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(primary_key=True)
    target: Mapped[str]
    source: Mapped[str]
    part_of_speech: Mapped[str]


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default="now()")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    started_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))


class SessionResult(Base):
    __tablename__ = "session_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id"))
    response_time_ms: Mapped[int | None]
    answered_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    raw_keystrokes: Mapped[str | None]
    status: Mapped[ResultStatus] = mapped_column(Enum(ResultStatus, name="result_status"))
    session_position: Mapped[int]


class UserWord(Base):
    __tablename__ = "user_words"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id"), primary_key=True)
    added_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default="now()")