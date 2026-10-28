import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

# feat(lgpd): versão vigente do Termo de Uso / Política de Privacidade.
# Ao publicar uma nova versão dos documentos, incremente este valor
# para que novos cadastros fiquem vinculados à versão correta.
CURRENT_TERMS_VERSION = "1.0"
BCRYPT_MAX_BYTES = 72
PASSWORD_MIN_LENGTH = 8
NAME_MIN_LENGTH = 2
NAME_MAX_LENGTH = 100

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None
    terms_accepted: bool
    terms_version: str = CURRENT_TERMS_VERSION

    @field_validator("name")
    @classmethod
    def validar_nome(cls, value: str | None) -> str | None:
        # O nome é opcional na API, mas, quando enviado, precisa ser válido.
        if value is None:
            return None
        value = " ".join(value.split())  # remove espaços extras
        if len(value) < NAME_MIN_LENGTH:
            raise ValueError(f"O nome precisa ter pelo menos {NAME_MIN_LENGTH} caracteres")
        if len(value) > NAME_MAX_LENGTH:
            raise ValueError(f"O nome pode ter no máximo {NAME_MAX_LENGTH} caracteres")
        if not any(c.isalpha() for c in value):
            raise ValueError("O nome precisa conter letras")
        return value

    @field_validator("terms_accepted")
    @classmethod
    def must_accept_terms(cls, value: bool) -> bool:
        if not value:
            raise ValueError(
                "É necessário aceitar o Termo de Uso e a Política de Privacidade para se cadastrar."
            )
        return value
    
    @field_validator("password")
    @classmethod
    def validar_forca_da_senha(cls, value: str) -> str:
        if len(value) < PASSWORD_MIN_LENGTH:
            raise ValueError(f"A senha precisa ter pelo menos {PASSWORD_MIN_LENGTH} caracteres")
        if len(value.encode("utf-8")) > BCRYPT_MAX_BYTES:
            raise ValueError("A senha pode ter no máximo 72 caracteres")
        if not any(c.isalpha() for c in value) or not any(c.isdigit() for c in value):
            raise ValueError("A senha precisa conter letras e números")
        if value.isalnum():
            raise ValueError("A senha precisa conter também um caractere especial (ex: ! @ # $ %)")
        return value

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: str | None = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validar_forca_da_senha(cls, value: str) -> str:
        if len(value) < PASSWORD_MIN_LENGTH:
            raise ValueError(f"A senha precisa ter pelo menos {PASSWORD_MIN_LENGTH} caracteres")
        if len(value.encode("utf-8")) > BCRYPT_MAX_BYTES:
            raise ValueError("A senha pode ter no máximo 72 caracteres")
        if not any(c.isalpha() for c in value) or not any(c.isdigit() for c in value):
            raise ValueError("A senha precisa conter letras e números")
        if value.isalnum():
            raise ValueError("A senha precisa conter também um caractere especial (ex: ! @ # $ %)")
        return value