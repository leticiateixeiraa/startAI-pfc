"""
Testes de integração do nível da vaga em POST /interviews e no histórico.
Só o Gemini é simulado.
"""
import uuid

from app.interview.models import InterviewSession

from tests.integration.apoio import montar_entrevista_ia, perguntas_geradas, usuario_autenticado


def test_post_interviews_deve_gravar_o_nivel_e_enviar_ao_gemini(api, db, gemini_falso):
    _, headers = usuario_autenticado(api, "nivel")
    gemini_falso.responder({"questions": perguntas_geradas()})

    resposta = api.post("/interviews", json=montar_entrevista_ia(seniority="pleno"), headers=headers)

    assert resposta.status_code == 201, resposta.text
    session_id = resposta.json()["session_id"]
    db.expire_all()
    assert db.query(InterviewSession).filter_by(id=uuid.UUID(session_id)).one().seniority == "pleno"
    assert "Nível da vaga: Pleno" in gemini_falso.prompts[0]
    historico = api.get("/interviews/history", headers=headers).json()
    assert historico[0]["seniority"] == "pleno"


def test_post_interviews_sem_nivel_continua_funcionando(api, gemini_falso):
    _, headers = usuario_autenticado(api, "semnivel")
    gemini_falso.responder({"questions": perguntas_geradas()})

    resposta = api.post("/interviews", json=montar_entrevista_ia(), headers=headers)

    assert resposta.status_code == 201, resposta.text
    assert "Nível da vaga" not in gemini_falso.prompts[0]


def test_post_interviews_com_nivel_invalido_deve_retornar_400_sem_chamar_o_gemini(api, gemini_falso):
    _, headers = usuario_autenticado(api, "nivelruim")

    resposta = api.post("/interviews", json=montar_entrevista_ia(seniority="diretor"), headers=headers)

    assert resposta.status_code == 400
    assert "Nível" in resposta.json()["detail"]
    assert gemini_falso.prompts == []
