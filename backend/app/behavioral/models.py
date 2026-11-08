"""
feat(behavioral-db): perfil comportamental de cada entrevista comportamental.

É gerado junto com a avaliação da entrevista (na MESMA chamada ao Gemini) e,
como ela, é gravado uma vez só (evaluation_id único). O perfil consolidado
do aluno não é gravado: é a média calculada na hora a partir destas linhas
(ver service.py).

Uma coluna por competência, e não um JSON, para a média por competência ser
uma consulta simples e o diagrama de classes ficar explícito.
"""
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import Base


class BehavioralProfile(Base):
    __tablename__ = "behavioral_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id = Column(
        UUID(as_uuid=True), ForeignKey("interview_evaluations.id"), nullable=False, unique=True
    )
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False, unique=True, index=True
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Competências (0 a 10) — chaves de app/behavioral/competencias.py.
    comunicacao = Column(Integer, nullable=False)
    trabalho_em_equipe = Column(Integer, nullable=False)
    lideranca = Column(Integer, nullable=False)
    resolucao_de_problemas = Column(Integer, nullable=False)
    adaptabilidade = Column(Integer, nullable=False)
    inteligencia_emocional = Column(Integer, nullable=False)

    # Uso do método STAR nas respostas (0 a 10).
    star_situation = Column(Integer, nullable=False)
    star_task = Column(Integer, nullable=False)
    star_action = Column(Integer, nullable=False)
    star_result = Column(Integer, nullable=False)

    archetype = Column(String(40), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
