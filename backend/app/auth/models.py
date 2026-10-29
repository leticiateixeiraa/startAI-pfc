import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, true

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # feat(lgpd): registra o aceite do Termo de Uso / Política de Privacidade
    terms_accepted_at = Column(DateTime(timezone=True), nullable=True)
    terms_version = Column(String(20), nullable=True)
    # feat(admin): papel do usuário ("user" ou "admin") e situação da conta.
    # O papel nunca é definido pelo cadastro público: só pelo script
    # app/scripts/promote_admin.py. Conta desativada não consegue logar.
    role = Column(String(20), nullable=False, default="user", server_default="user")
    is_active = Column(Boolean, nullable=False, default=True, server_default=true())

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token_hash = Column(String, nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")