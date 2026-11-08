"""
feat(jobs-db): vagas recomendadas para cada usuário.

Guarda o último lote de vagas buscado na API da Jooble para cada usuário
(RN04 do service.py). Assim, abrir a página de novo não gasta a cota
gratuita da API, e se a API cair as últimas vagas continuam aparecendo.

`search_key` é o "cargo|nível" usado na busca: se o perfil do aluno mudar
(fez entrevista para outro cargo, por exemplo), o lote antigo deixa de valer.
"""
import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import Base


class JobRecommendation(Base):
    __tablename__ = "job_recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    search_key = Column(String(220), nullable=False)
    position = Column(Integer, nullable=False)  # ordem na lista (0 = mais compatível)

    # Dados da vaga como vieram da Jooble (já limpos).
    external_id = Column(String(64), nullable=True)
    title = Column(String(300), nullable=False)
    company = Column(String(200), nullable=True)
    location = Column(String(200), nullable=True)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    url = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    posted_at = Column(DateTime(timezone=True), nullable=True)

    # Calculados pelo backend (RN03).
    compatibility = Column(Integer, nullable=False)
    reasons = Column(Text, nullable=False, default="[]")  # JSON, igual ao `details` da auditoria

    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
