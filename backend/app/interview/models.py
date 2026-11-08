"""
feat(interview-db): cria tabelas de sessão de entrevista e respostas (mock)

Observação para o time: no contrato combinado, a "sessão de entrevista" é
quem o módulo `questions` (Leonardo) cria via POST /interviews, devolvendo
{"session_id": ..., "questions": [...]}. Como esse módulo ainda não existe,
o `interview` cria e mantém sua PRÓPRIA versão simplificada de sessão só
para poder ser desenvolvido e testado em paralelo com dados mockados,
conforme combinado no roteiro ("pode ser desenvolvido em paralelo usando
respostas mockadas enquanto o módulo questions não estiver pronto").

Quando o módulo `questions` estiver pronto:
- migrar a criação da sessão pra lá (POST /interviews vira o dono da tabela
  `interview_sessions`, populando as perguntas com a IA real em vez do
  QUESTION_BANK fixo em app/interview/service.py);
- este módulo passa a só receber session_id + resposta, persistir e decidir
  a próxima pergunta — o que já é a única responsabilidade real dele.
"""
import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    category = Column(String, nullable=False)
    presentation_type = Column(String, nullable=True)

    # Índice da próxima pergunta "fixa" do banco (QUESTION_BANK) a ser usada
    # quando não há adaptação. Não avança quando uma pergunta adaptada é
    # inserida no meio do fluxo (ver app/interview/service.py).
    current_index = Column(Integer, nullable=False, default=0)

    # Texto da pergunta que está atualmente pendente de resposta. Guardado
    # explicitamente (em vez de derivado só do índice) porque uma pergunta
    # adaptada pode não existir no QUESTION_BANK.
    current_question_text = Column(Text, nullable=True)

    finished = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False, index=True)
    order_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False, index=True)
    order_index = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=False)
    # feat(speech): "text" (digitada) ou "voice" (transcrita do áudio). A duração
    # só existe nas respostas por voz e alimenta o analisador de oratória.
    input_mode = Column(String(10), nullable=False, default="text")
    audio_duration_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
