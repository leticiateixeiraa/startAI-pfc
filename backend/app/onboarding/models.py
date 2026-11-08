"""
feat(onboarding-db): respostas do questionário de primeiro acesso.

Uma linha por usuário (user_id único). Se o aluno refizer o questionário,
a mesma linha é atualizada. Quem pulou o questionário também ganha uma
linha (skipped = True), para não ser perguntado de novo a cada login.
"""
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, false

from app.models.base import Base


class CareerOnboarding(Base):
    __tablename__ = "career_onboarding"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    skipped = Column(Boolean, nullable=False, default=False, server_default=false())
    # JSON em texto, igual ao `details` da auditoria: {pergunta: alternativa}
    # e {área: pontos}. Funciona no PostgreSQL e no SQLite dos testes.
    answers = Column(Text, nullable=False, default="{}")
    scores = Column(Text, nullable=False, default="{}")
    recommended_area = Column(String(40), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
