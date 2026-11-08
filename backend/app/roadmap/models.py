import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import Base


class LearningRoadmap(Base):
    __tablename__ = "learning_roadmaps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(160), nullable=False)
    objective = Column(Text, nullable=True)
    # feat(roadmap-ia): trilha gerada a partir da avaliação de uma entrevista.
    # Uma por entrevista (único); None nas trilhas criadas à mão (POST /roadmaps).
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=True, unique=True, index=True
    )
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class LearningRoadmapItem(Base):
    __tablename__ = "learning_roadmap_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    roadmap_id = Column(UUID(as_uuid=True), ForeignKey("learning_roadmaps.id"), nullable=False, index=True)
    order_index = Column(Integer, nullable=False)
    title = Column(String(160), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    # Campos da trilha gerada por IA (vazios nas etapas criadas à mão).
    focus = Column(Text, nullable=True)  # por que a etapa existe (ponto fraco da entrevista)
    estimated_time = Column(String(60), nullable=True)
    practice = Column(Text, nullable=True)  # exercício prático sugerido
    # Listas em JSON (texto), como no restante do projeto.
    tips = Column(Text, nullable=False, default="[]", server_default="[]")
    resources = Column(Text, nullable=False, default="[]", server_default="[]")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)