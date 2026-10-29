"""
feat(admin): endpoints do painel administrativo.

Todas as rotas exigem `require_admin`: usuário comum recebe 403 e quem não
está autenticado recebe 401. O papel de administrador é conferido no banco a
cada requisição e só pode ser concedido pelo script
`python -m app.scripts.promote_admin <email>`.
"""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.admin import service
from app.admin.schemas import AdminMetricsOut, AdminUserOut, UserStatusIn
from app.audit.schemas import AuditLogOut
from app.audit.service import record_event
from app.auth.dependencies import require_admin
from app.auth.models import User
from app.models.base import get_db

router = APIRouter(prefix="/admin", tags=["admin"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/users", response_model=list[AdminUserOut])
def list_users(
    search: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=100, ge=1, le=500),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return service.list_users(db, search, limit)


@router.patch("/users/{user_id}", response_model=AdminUserOut)
def update_user_status(
    user_id: uuid.UUID,
    payload: UserStatusIn,
    request: Request,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if str(user_id) == admin_id:
        raise HTTPException(status_code=400, detail="Você não pode desativar a sua própria conta")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.is_active = payload.is_active
    record_event(
        db,
        "admin.user_unblocked" if payload.is_active else "admin.user_blocked",
        uuid.UUID(admin_id),
        "user",
        str(user.id),
        ip_address=_client_ip(request),
    )
    db.commit()
    db.refresh(user)
    return service.user_summary(db, user)


@router.get("/audit/logs", response_model=list[AuditLogOut])
def list_audit_logs(
    request: Request,
    user_id: uuid.UUID | None = None,
    action: str | None = Query(default=None, max_length=80),
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="A data inicial não pode ser depois da final")

    logs = service.list_audit_logs(db, user_id, action, date_from, date_to, limit)
    # O próprio acesso do administrador à auditoria geral fica registrado.
    record_event(
        db,
        "admin.audit_viewed",
        uuid.UUID(admin_id),
        "audit_log",
        None,
        {"user_id": str(user_id) if user_id else None, "action": action},
        ip_address=_client_ip(request),
    )
    db.commit()
    return logs


@router.get("/metrics", response_model=AdminMetricsOut)
def metrics(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return service.get_metrics(db)
