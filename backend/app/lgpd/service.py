"""
feat(lgpd): exclusão definitiva da conta e dos dados pessoais.

Usado em dois lugares, com a MESMA regra:
- DELETE /auth/me           -> o próprio titular exclui a conta (Art. 18, VI)
- DELETE /admin/users/{id}  -> o administrador atende um pedido de exclusão

RN01 - São APAGADOS do banco: cadastro, entrevistas (sessões, perguntas e
       respostas), avaliações da IA, questionário de primeiro acesso, trilhas
       de estudo e tokens de redefinição de senha.
RN02 - Os registros de AUDITORIA não são apagados, e sim ANONIMIZADOS: o
       vínculo com a pessoa (user_id) e o endereço IP são removidos, mas o
       fato "aconteceu um login / uma entrevista" continua registrado. A
       política de privacidade usa legítimo interesse (segurança) para os
       logs, e a LGPD permite manter dados anonimizados (Art. 12 e 16).
RN03 - Tudo acontece em uma transação só: se qualquer etapa falhar, nada é
       apagado e a conta continua como estava.
RN04 - O último administrador ativo não pode excluir a própria conta, para
       o sistema nunca ficar sem quem o administre.
RN05 - Pelo painel, o administrador não exclui a si mesmo nem outro
       administrador: o papel precisa ser revogado antes, pelo script
       `python -m app.scripts.promote_admin <email> --revoke`.

O banco não tem ON DELETE CASCADE, por isso a ordem abaixo importa: primeiro
os "filhos" (ex.: avaliação de cada resposta), depois os "pais".
"""
from sqlalchemy.orm import Session

from app.audit.models import AuditLog
from app.auth.models import PasswordResetToken, User
from app.auth.schemas import ROLE_ADMIN
from app.evaluation.models import AnswerEvaluation, InterviewEvaluation
from app.interview.models import InterviewAnswer, InterviewQuestion, InterviewSession
from app.onboarding.models import CareerOnboarding
from app.roadmap.models import LearningRoadmap, LearningRoadmapItem


class ExclusaoNaoPermitida(Exception):
    """A conta não pode ser excluída (RN04)."""


def eh_ultimo_admin(db: Session, user: User) -> bool:
    if user.role != ROLE_ADMIN:
        return False
    outros_admins = (
        db.query(User)
        .filter(User.role == ROLE_ADMIN, User.is_active.is_(True), User.id != user.id)
        .count()
    )
    return outros_admins == 0


def excluir_conta(db: Session, user: User) -> dict:
    """Apaga os dados da conta e anonimiza a auditoria.

    Não faz commit: quem chama registra o evento de exclusão e confirma tudo
    junto, na mesma transação (RN03). Devolve quantos registros de cada tipo
    foram apagados, sem nenhum dado pessoal.
    """
    if eh_ultimo_admin(db, user):
        raise ExclusaoNaoPermitida(
            "Esta é a única conta de administrador ativa e não pode ser excluída"
        )

    sessoes = db.query(InterviewSession.id).filter(InterviewSession.user_id == user.id)
    avaliacoes = db.query(InterviewEvaluation.id).filter(InterviewEvaluation.user_id == user.id)
    trilhas = db.query(LearningRoadmap.id).filter(LearningRoadmap.user_id == user.id)

    def apagar(consulta) -> int:
        return consulta.delete(synchronize_session=False)

    resumo = {
        "answer_evaluations": apagar(
            db.query(AnswerEvaluation).filter(AnswerEvaluation.evaluation_id.in_(avaliacoes))
        ),
        "interview_evaluations": apagar(
            db.query(InterviewEvaluation).filter(InterviewEvaluation.user_id == user.id)
        ),
        "interview_answers": apagar(
            db.query(InterviewAnswer).filter(InterviewAnswer.session_id.in_(sessoes))
        ),
        "interview_questions": apagar(
            db.query(InterviewQuestion).filter(InterviewQuestion.session_id.in_(sessoes))
        ),
        "interview_sessions": apagar(
            db.query(InterviewSession).filter(InterviewSession.user_id == user.id)
        ),
        "roadmap_items": apagar(
            db.query(LearningRoadmapItem).filter(LearningRoadmapItem.roadmap_id.in_(trilhas))
        ),
        "roadmaps": apagar(db.query(LearningRoadmap).filter(LearningRoadmap.user_id == user.id)),
        "career_onboarding": apagar(
            db.query(CareerOnboarding).filter(CareerOnboarding.user_id == user.id)
        ),
        "password_reset_tokens": apagar(
            db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id)
        ),
    }

    # RN02: anonimiza o que a própria pessoa fez...
    resumo["audit_logs_anonymized"] = (
        db.query(AuditLog)
        .filter(AuditLog.user_id == user.id)
        .update({AuditLog.user_id: None, AuditLog.ip_address: None}, synchronize_session=False)
    )
    # ...e tira o id dela dos eventos em que ela era o "alvo" (ex.: um admin
    # desativou a conta). O administrador que agiu continua identificado.
    db.query(AuditLog).filter(
        AuditLog.resource_type == "user", AuditLog.resource_id == str(user.id)
    ).update({AuditLog.resource_id: None}, synchronize_session=False)

    db.delete(user)
    db.flush()
    return resumo
