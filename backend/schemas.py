from datetime import datetime

from pydantic import BaseModel

from backend.enums import SentenceResultStatus, VocabResultStatus, SessionBoundType, SessionType


class SentenceResult(BaseModel):
    sentence_id: int
    session_id: int
    status: SentenceResultStatus


class SentencePair(BaseModel):
    id: int | None = None
    target: str
    source: str
    lemmas: list[str] = []  # Needs default since initally empty


class SentenceRequest(BaseModel):
    sentences_already_queued: list[int] = []


class WordResult(BaseModel):
    word_id: int
    response_time_ms: int | None = None
    answered_at: datetime
    raw_keystrokes: str | None = None
    status: VocabResultStatus
    session_position: int


class VocabResults(BaseModel):
    session_id: int
    word_results: list[WordResult]


class GoogleToken(BaseModel):
    credential: str


class SessionRequest(BaseModel):
    bound_type: SessionBoundType
    bound_value: int
    session_type: SessionType
