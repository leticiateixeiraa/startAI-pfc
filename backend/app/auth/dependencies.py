"""
chore(auth): configura middleware de autenticação nas rotas protegidas
feat(admin): adiciona verificação de conta ativa e de papel de administrador

Dependencies reutilizáveis nos endpoints:

    from app.auth.dependencies import get_current_user, require_admin

    @router.get("/rota-protegida")
    def minha_rota(user_id: str = Depends(get_current_user)):
        ...

    @router.get("/admin/rota")
    def rota_admin(admin_id: str = Depends(require_admin)):
        ...
"""
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.schemas import ROLE_ADMIN
from app.auth.service import decodificar_token_acesso
from app.models.base import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _erro_401(detalhe: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detalhe,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> str:
    id_usuario = decodificar_token_acesso(token)
    if id_usuario is None:
        raise _erro_401("Token inválido ou expirado")

    # A conta é conferida no banco a cada requisição: um usuário desativado
    # pelo administrador perde o acesso na hora, mesmo com um token ainda válido.
    try:
        user = db.query(User).filter(User.id == uuid.UUID(id_usuario)).first()
    except ValueError:
        user = None
    if user is None or not user.is_active:
        raise _erro_401("Conta inexistente ou desativada")
    return id_usuario


def require_admin(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> str:
    """Libera a rota só para administradores. O papel vem do banco, nunca do token."""
    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if user is None or user.role != ROLE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores",
        )
    return user_id
