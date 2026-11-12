import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.audit.models import AuditLog
from app.audit.schemas import AuditLogOut
from app.auth.dependencies import get_current_user
from app.models.base import get_db

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs", response_model=list[AuditLogOut])
def list_logs(
    limit: int = Query(default=100, ge=1, le=500),
    action: str | None = None,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(AuditLog).filter(AuditLog.user_id == uuid.UUID(user_id))
    if action:
        query = query.filter(AuditLog.action == action)
    return query.order_by(AuditLog.created_at.desc()).limit(limit).all()
