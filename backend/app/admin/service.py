"""
feat(admin): consultas do painel administrativo.

As regras ficam aqui (e não no router nem nos models), seguindo o padrão
dos demais módulos.
"""
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.audit.models import AuditLog
from app.auth.models import User
from app.interview.models import InterviewAnswer, InterviewSession

METRICS_DAYS = 30
# Os dias do gráfico seguem o horário de Brasília, e não o UTC do servidor.
FUSO_PADRAO = ZoneInfo("America/Sao_Paulo")


def list_users(db: Session, search: str | None, limit: int) -> list[dict]:
    query = db.query(User)
    if search:
        termo = f"%{search.strip().lower()}%"
        query = query.filter(
            func.lower(User.email).like(termo) | func.lower(User.name).like(termo)
        )
    users = query.order_by(User.created_at.desc()).limit(limit).all()

    contagem = dict(
        db.query(InterviewSession.user_id, func.count(InterviewSession.id))
        .filter(InterviewSession.user_id.in_([user.id for user in users]))
        .group_by(InterviewSession.user_id)
        .all()
    ) if users else {}

    return [
        {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "interview_count": contagem.get(user.id, 0),
        }
        for user in users
    ]


def user_summary(db: Session, user: User) -> dict:
    total = (
        db.query(func.count(InterviewSession.id))
        .filter(InterviewSession.user_id == user.id)
        .scalar()
        or 0
    )
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "interview_count": total,
    }


def list_audit_logs(
    db: Session,
    user_id,
    action: str | None,
    date_from: date | None,
    date_to: date | None,
    limit: int,
) -> list[AuditLog]:
    query = db.query(AuditLog)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if date_from:
        inicio = datetime.combine(date_from, datetime.min.time(), tzinfo=timezone.utc)
        query = query.filter(AuditLog.created_at >= inicio)
    if date_to:
        fim = datetime.combine(date_to + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
        query = query.filter(AuditLog.created_at < fim)
    return query.order_by(AuditLog.created_at.desc()).limit(limit).all()


def _ultimos_dias(dias: int) -> list[str]:
    hoje = datetime.now(FUSO_PADRAO).date()
    return [(hoje - timedelta(days=offset)).isoformat() for offset in range(dias - 1, -1, -1)]


def get_metrics(db: Session) -> dict:
    agora = datetime.now(timezone.utc)

    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active.is_(True)).scalar() or 0
    new_users = (
        db.query(func.count(User.id))
        .filter(User.created_at >= agora - timedelta(days=METRICS_DAYS))
        .scalar()
        or 0
    )

    total_interviews = db.query(func.count(InterviewSession.id)).scalar() or 0
    finished = (
        db.query(func.count(InterviewSession.id))
        .filter(InterviewSession.finished.is_(True))
        .scalar()
        or 0
    )
    total_answers = db.query(func.count(InterviewAnswer.id)).scalar() or 0

    failed_logins = (
        db.query(func.count(AuditLog.id))
        .filter(
            AuditLog.action == "auth.login_failed",
            AuditLog.created_at >= agora - timedelta(days=7),
        )
        .scalar()
        or 0
    )

    por_tipo = (
        db.query(InterviewSession.presentation_type, func.count(InterviewSession.id))
        .group_by(InterviewSession.presentation_type)
        .all()
    )

    datas = db.query(InterviewSession.created_at).filter(
        InterviewSession.created_at >= agora - timedelta(days=METRICS_DAYS + 1)
    )
    por_dia_banco = Counter(
        criado_em.astimezone(FUSO_PADRAO).date().isoformat()
        for (criado_em,) in datas
        if criado_em is not None
    )

    return {
        "total_users": total_users,
        "active_users": active_users,
        "blocked_users": total_users - active_users,
        "new_users_last_30_days": new_users,
        "total_interviews": total_interviews,
        "finished_interviews": finished,
        "completion_rate": round(finished / total_interviews, 4) if total_interviews else 0.0,
        "total_answers": total_answers,
        "average_answers_per_interview": (
            round(total_answers / total_interviews, 2) if total_interviews else 0.0
        ),
        "failed_logins_last_7_days": failed_logins,
        "interviews_by_type": sorted(
            ({"key": tipo or "nao_informado", "count": quantidade} for tipo, quantidade in por_tipo),
            key=lambda item: item["count"],
            reverse=True,
        ),
        "interviews_per_day": [
            {"key": dia_iso, "count": por_dia_banco.get(dia_iso, 0)}
            for dia_iso in _ultimos_dias(METRICS_DAYS)
        ],
    }
