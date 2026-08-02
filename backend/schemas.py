from datetime import datetime

from pydantic import BaseModel, Field

from backend.enums import SentenceResultStatus, VocabResultStatus


class SentenceResult(BaseModel):
    sentence_id: int
    #TODO: session_id: int - add when session is wired to sentences too, NULL until then
    status: SentenceResultStatus


class SentencePair(BaseModel):
    id: int | None = None
    target: str
    source: str
    lemmas: list[str] = []  # Needs default since initally empty


class SentenceRequest(BaseModel):
    known_percent: int = Field(ge=0, le=100)
    sentences_already_queued: list[int] = []


class WordResult(BaseModel):
    word_id: int
    response_time_ms: int | None = None
    answered_at: datetime | None = None
    raw_keystrokes: str | None = None
    status: VocabResultStatus
    session_position: int


class VocabResults(BaseModel):
    session_id: int
    word_results: list[WordResult]


class GoogleToken(BaseModel):
    credential: str
