from pydantic import BaseModel


class TranscriptionOut(BaseModel):
    transcript: str
    duration_seconds: float | None
    word_count: int
