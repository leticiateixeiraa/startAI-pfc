"""
Regras de negócio de autenticação: hash de senha e geração/validação de JWT.

Contrato combinado com o time (item 6 do roteiro):
- token JWT é passado no header: Authorization: Bearer <token>
- payload do token traz "sub" = user_id
"""
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app import config  # noqa: F401  (carrega o .env antes de ler as variáveis)

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY or SECRET_KEY == "troque-por-uma-chave-secreta-forte":
    raise RuntimeError(
        "JWT_SECRET_KEY não configurada. Rode `python scripts/configurar_env.py` "
        "na raiz do projeto, que gera a chave automaticamente."
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24))
RESET_TOKEN_EXPIRE_MINUTES = 30

contexto_senha = CryptContext(schemes=["bcrypt"], deprecated="auto")


def criar_hash_senha(senha: str) -> str:
    return contexto_senha.hash(senha)


def verificar_senha(senha_pura: str, senha_hash: str) -> bool:
    return contexto_senha.verify(senha_pura, senha_hash)


def criar_token_acesso(id_usuario: str) -> str:
    expira_em = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": id_usuario, "exp": expira_em, "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decodificar_token_acesso(token: str) -> str | None:
    """Retorna o id_usuario (sub) se o token for válido, ou None."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.JWTError:
        return None


def gerar_token_redefinicao() -> tuple[str, str]:
    """Retorna (token que vai no e-mail, hash que vai pro banco)."""
    token_bruto = secrets.token_urlsafe(32)
    hash_token = hashlib.sha256(token_bruto.encode()).hexdigest()
    return token_bruto, hash_token


def gerar_hash_token(token_bruto: str) -> str:
    return hashlib.sha256(token_bruto.encode()).hexdigest()
