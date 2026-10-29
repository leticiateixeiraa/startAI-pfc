import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AdminUserOut(BaseModel):
    """Dados cadastrais vistos pelo administrador.

    Por minimização (LGPD), o administrador NÃO tem acesso ao conteúdo das
    respostas das entrevistas: vê apenas a quantidade de sessões de cada conta.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    name: str | None
    role: str
    is_active: bool
    created_at: datetime | None
    interview_count: int = 0


class UserStatusIn(BaseModel):
    is_active: bool


class CountByKey(BaseModel):
    key: str
    count: int


class AdminMetricsOut(BaseModel):
    total_users: int
    active_users: int
    blocked_users: int
    new_users_last_30_days: int
    total_interviews: int
    finished_interviews: int
    completion_rate: float
    total_answers: int
    average_answers_per_interview: float
    failed_logins_last_7_days: int
    interviews_by_type: list[CountByKey]
    interviews_per_day: list[CountByKey]
