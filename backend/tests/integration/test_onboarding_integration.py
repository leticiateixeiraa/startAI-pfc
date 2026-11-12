"""
Testes de integração do questionário de primeiro acesso (app/onboarding).

Endpoints: GET /onboarding/questions, GET /onboarding/me, POST /onboarding
e POST /onboarding/skip. Nenhum serviço externo é usado.
"""
import uuid

from app.audit.models import AuditLog
from app.onboarding.models import CareerOnboarding
from app.onboarding.questionario import PERGUNTAS
from tests.integration.apoio import SENHA, usuario_autenticado


def _respostas_para(area: str) -> dict[str, str]:
    """Escolhe, em cada pergunta, a alternativa que mais pontua a área."""
    return {
        pergunta["id"]: max(pergunta["options"], key=lambda opcao: opcao["weights"].get(area, 0))["id"]
        for pergunta in PERGUNTAS
    }


def test_usuario_novo_deve_estar_com_questionario_pendente(api):
    _, headers = usuario_autenticado(api, "novo")

    corpo = api.get("/onboarding/me", headers=headers).json()

    assert corpo == {"status": "pending", "result": None}


def test_perguntas_devem_vir_sem_os_pesos(api):
    _, headers = usuario_autenticado(api, "perguntas")

    perguntas = api.get("/onboarding/questions", headers=headers).json()

    assert [pergunta["id"] for pergunta in perguntas] == [pergunta["id"] for pergunta in PERGUNTAS]
    assert set(perguntas[0]["options"][0]) == {"id", "text"}


def test_post_deve_calcular_area_recomendada_gravar_e_auditar(api, db):
    usuario, headers = usuario_autenticado(api, "dados")

    resposta = api.post("/onboarding", json={"answers": _respostas_para("dados_ia")}, headers=headers)

    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert corpo["recommended_area"]["key"] == "dados_ia"
    assert corpo["recommended_area"]["suggested_job_title"]
    assert corpo["ranking"][0]["key"] == "dados_ia"
    assert api.get("/onboarding/me", headers=headers).json()["status"] == "completed"
    db.expire_all()
    evento = db.query(AuditLog).filter_by(
        action="onboarding.completed", user_id=uuid.UUID(usuario["id"])
    ).one()
    assert "dados_ia" in evento.details


def test_refazer_deve_atualizar_o_mesmo_registro(api, db):
    usuario, headers = usuario_autenticado(api, "refaz")
    api.post("/onboarding", json={"answers": _respostas_para("qa")}, headers=headers)

    corpo = api.post("/onboarding", json={"answers": _respostas_para("mobile")}, headers=headers).json()

    assert corpo["recommended_area"]["key"] == "mobile"
    db.expire_all()
    assert db.query(CareerOnboarding).filter_by(user_id=uuid.UUID(usuario["id"])).count() == 1


def test_questionario_incompleto_deve_retornar_400_e_nao_gravar(api, db):
    usuario, headers = usuario_autenticado(api, "incompleto")

    resposta = api.post("/onboarding", json={"answers": {PERGUNTAS[0]["id"]: "a"}}, headers=headers)

    assert resposta.status_code == 400
    db.expire_all()
    assert db.query(CareerOnboarding).filter_by(user_id=uuid.UUID(usuario["id"])).count() == 0


def test_pular_deve_marcar_como_pulado_e_nao_apagar_resultado_existente(api):
    _, headers_pulou = usuario_autenticado(api, "pulou")
    _, headers_respondeu = usuario_autenticado(api, "respondeu")
    api.post("/onboarding", json={"answers": _respostas_para("seguranca")}, headers=headers_respondeu)

    pulou = api.post("/onboarding/skip", headers=headers_pulou).json()
    respondeu = api.post("/onboarding/skip", headers=headers_respondeu).json()

    assert pulou == {"status": "skipped", "result": None}
    assert api.get("/onboarding/me", headers=headers_pulou).json()["status"] == "skipped"
    assert respondeu["status"] == "completed"
    assert respondeu["result"]["recommended_area"]["key"] == "seguranca"


def test_endpoints_sem_token_devem_retornar_401(api):
    assert api.get("/onboarding/me").status_code == 401
    assert api.get("/onboarding/questions").status_code == 401
    assert api.post("/onboarding", json={"answers": {}}).status_code == 401


def test_exclusao_de_conta_deve_apagar_o_questionario(api, db):
    usuario, headers = usuario_autenticado(api, "lgpdonb")
    api.post("/onboarding", json={"answers": _respostas_para("backend")}, headers=headers)

    resposta = api.request("DELETE", "/auth/me", json={"password": SENHA}, headers=headers)

    assert resposta.status_code in (200, 204), resposta.text
    db.expire_all()
    assert db.query(CareerOnboarding).filter_by(user_id=uuid.UUID(usuario["id"])).count() == 0
