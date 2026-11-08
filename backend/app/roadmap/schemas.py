import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RoadmapItemIn(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str | None = None


class RoadmapCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    objective: str | None = None
    items: list[RoadmapItemIn] = Field(min_length=1, max_length=30)


class RoadmapItemStatusIn(BaseModel):
    status: str = Field(pattern="^(pending|in_progress|completed)$")


class ResourceOut(BaseModel):
    type: str
    title: str
    url: str
    description: str | None = None


class RoadmapItemOut(RoadmapItemIn):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_index: int
    status: str
    # Só nas trilhas geradas por IA.
    focus: str | None = None
    estimated_time: str | None = None
    practice: str | None = None
    tips: list[str] = []
    resources: list[ResourceOut] = []


class RoadmapOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    # Entrevista que originou a trilha (None nas criadas à mão).
    session_id: uuid.UUID | None = None
    title: str
    objective: str | None
    summary: str | None = None
    created_at: datetime
    updated_at: datetime
    items: list[RoadmapItemOut]