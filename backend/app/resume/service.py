import json
import uuid

from sqlalchemy.orm import Session

from app.resume.models import ResumeAnalysis
from app.resume.schemas import ResumeAnalysisOut


def buscar(db: Session, user_id: uuid.UUID) -> ResumeAnalysis | None:
    return db.query(ResumeAnalysis).filter(ResumeAnalysis.user_id == user_id).first()


def salvar(
    db: Session,
    user_id: uuid.UUID,
    file_name: str,
    file_type: str,
    target_role: str | None,
    resultado: dict,
) -> ResumeAnalysis:
    """Guarda a análise; se o aluno já tinha uma, ela é substituída."""
    registro = buscar(db, user_id)
    if registro is None:
        registro = ResumeAnalysis(user_id=user_id)
        db.add(registro)
    registro.file_name = file_name
    registro.file_type = file_type
    registro.target_role = target_role
    registro.result = json.dumps(resultado, ensure_ascii=False)
    db.flush()
    return registro


def montar_saida(registro: ResumeAnalysis) -> ResumeAnalysisOut:
    return ResumeAnalysisOut(
        file_name=registro.file_name,
        file_type=registro.file_type,
        target_role=registro.target_role,
        analyzed_at=registro.updated_at or registro.created_at,
        **json.loads(registro.result),
    )
