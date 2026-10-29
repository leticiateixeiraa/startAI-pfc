"""
feat(auth-backend): implementa endpoint POST /auth/register
feat(auth-backend): implementa endpoint POST /auth/login com JWT
feat(auth-backend): implementa endpoint GET /auth/me
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.base import get_db
from app.auth.dependencies import get_current_user
from app.auth.models import PasswordResetToken, User
from app.auth.schemas import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserLogin,
    UserOut,
)
from app.auth.service import (
    RESET_TOKEN_EXPIRE_MINUTES,
    criar_hash_senha,
    criar_token_acesso,
    gerar_hash_token,
    gerar_token_redefinicao,
    verificar_senha,
)
from app.auth.email_service import ErroEnvioEmail, enviar_email_redefinicao_senha
from app.audit.service import record_event

router = APIRouter(prefix="/auth", tags=["auth"])

_DUMMY_HASH = criar_hash_senha("senha-inexistente-0")


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, request: Request, db: Session = Depends(get_db)):
    email = str(user_in.email).strip().lower()
    existing = db.query(User).filter(func.lower(User.email) == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")

    user = User(
        email=email,
        hashed_password=criar_hash_senha(user_in.password),
        name=user_in.name,
        # feat(lgpd): consentimento é pré-requisito para o cadastro
        # (validado em UserCreate.must_accept_terms).
        terms_accepted_at=datetime.now(timezone.utc),
        terms_version=user_in.terms_version,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    record_event(db, "auth.registered", user.id, "user", str(user.id), ip_address=_client_ip(request))
    record_event(
        db,
        "lgpd.consent_accepted",
        user.id,
        "user",
        str(user.id),
        {"terms_version": user_in.terms_version},
        ip_address=_client_ip(request),
    )
    db.commit()
    return user


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, request: Request, db: Session = Depends(get_db)):
    email = str(credentials.email).strip().lower()
    user = db.query(User).filter(func.lower(User.email) == email).first()
    senha_ok = verificar_senha(
        credentials.password, user.hashed_password if user else _DUMMY_HASH
    )
    if not user or not senha_ok:
        # A falha também é auditada (sem guardar a senha nem o e-mail digitado).
        record_event(
            db,
            "auth.login_failed",
            user.id if user else None,
            "user",
            str(user.id) if user else None,
            ip_address=_client_ip(request),
        )
        db.commit()
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos")

    if not user.is_active:
        # feat(admin): a conta foi desativada por um administrador. A checagem
        # vem depois da senha para não revelar a situação da conta a terceiros.
        record_event(
            db,
            "auth.login_blocked",
            user.id,
            "user",
            str(user.id),
            ip_address=_client_ip(request),
        )
        db.commit()
        raise HTTPException(
            status_code=403,
            detail="Esta conta está desativada. Entre em contato com o suporte.",
        )

    access_token = criar_token_acesso(id_usuario=str(user.id))
    record_event(db, "auth.login", user.id, "user", str(user.id), ip_address=_client_ip(request))
    db.commit()
    return Token(access_token=access_token)


@router.get("/me", response_model=UserOut)
def me(user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user


@router.post("/forgot-password")
def esqueci_senha(payload: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    user = db.query(User).filter(func.lower(User.email) == email).first()

    resposta = {"message": "Se esse e-mail estiver cadastrado, você vai receber um link de redefinição."}

    if not user:
        return resposta

    token_bruto, hash_token = gerar_token_redefinicao()
    db.add(PasswordResetToken(
        user_id=user.id,
        token_hash=hash_token,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES),
    ))
    record_event(db, "auth.password_reset_requested", user.id, "user", str(user.id), ip_address=_client_ip(request))
    db.commit()

    try:
        enviar_email_redefinicao_senha(user.email, token_bruto)
    except ErroEnvioEmail as exc:
        raise HTTPException(status_code=502, detail="Não foi possível enviar o e-mail agora. Tente de novo mais tarde.") from exc

    return resposta


@router.post("/reset-password")
def redefinir_senha(payload: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    hash_token = gerar_hash_token(payload.token)
    token_redefinicao = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == hash_token).first()

    invalido = (
        not token_redefinicao
        or token_redefinicao.used_at is not None
        or token_redefinicao.expires_at < datetime.now(timezone.utc)
    )
    if invalido:
        raise HTTPException(status_code=400, detail="Link inválido ou expirado. Solicite uma nova redefinição.")

    user = db.query(User).filter(User.id == token_redefinicao.user_id).first()
    user.hashed_password = criar_hash_senha(payload.new_password)
    token_redefinicao.used_at = datetime.now(timezone.utc)

    record_event(db, "auth.password_reset_completed", user.id, "user", str(user.id), ip_address=_client_ip(request))
    db.commit()

    return {"message": "Senha redefinida com sucesso."}