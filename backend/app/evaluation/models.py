"""
feat(evaluation-db): tabelas da avaliação das respostas por IA.

Uma entrevista finalizada tem no máximo UMA avaliação (session_id único):
depois de gerada, ela fica salva e é só consultada. Assim o Gemini não é
chamado de novo toda vez que o aluno abre o resultado, e a nota não muda
entre uma visita e outra.

As notas são de 0 a 10 por critério. A nota de cada resposta e a nota geral
NÃO vêm da IA: são médias calculadas pelo backend (ver service.py), para a
regra ser sempre a mesma e fácil de explicar.
"""
import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import Base


class InterviewEvaluation(Base):
    __tablename__ = "interview_evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    overall_score = Column(Float, nullable=False)
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AnswerEvaluation(Base):
    __tablename__ = "answer_evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id = Column(
        UUID(as_uuid=True), ForeignKey("interview_evaluations.id"), nullable=False, index=True
    )
    answer_id = Column(UUID(as_uuid=True), ForeignKey("interview_answers.id"), nullable=False)
    order_index = Column(Integer, nullable=False)

    # Critérios definidos na ficha do projeto (funcionalidade 9).
    relevance = Column(Integer, nullable=False)
    coherence = Column(Integer, nullable=False)
    completeness = Column(Integer, nullable=False)
    adequacy = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)

    feedback = Column(Text, nullable=False)
    # Listas curtas guardadas como JSON em texto, igual ao `details` da
    # auditoria: funciona no PostgreSQL e no SQLite dos testes.
    strengths = Column(Text, nullable=False, default="[]")
    improvements = Column(Text, nullable=False, default="[]")
