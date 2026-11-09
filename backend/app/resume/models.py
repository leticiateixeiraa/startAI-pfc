"""
feat(resume-db): análise de currículo feita pela IA.

Uma linha por usuário (user_id único): enviar outro currículo substitui a
análise anterior. O ARQUIVO não é guardado (nem em disco, nem no banco): ele
é lido em memória, enviado ao Gemini e descartado. Fica só o resultado da
análise, que é apagado junto com a conta (app/lgpd/service.py).
"""
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import Base


class ResumeAnalysis(Base):
    __tablename__ = "resume_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # "pdf" ou "docx"
    target_role = Column(String(120), nullable=True)
    # JSON em texto (mesmo padrão do onboarding): funciona no PostgreSQL e no
    # SQLite dos testes.
    result = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
