import json
import uuid

from sqlalchemy.orm import Session

from app.audit.models import AuditLog


def record_event(
    db: Session,
    action: str,
    user_id: uuid.UUID | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Adiciona um evento à transação atual; o chamador decide quando confirmar."""
    event = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=json.dumps(details, ensure_ascii=False) if details else None,
        ip_address=ip_address,
    )
    db.add(event)
    return event
