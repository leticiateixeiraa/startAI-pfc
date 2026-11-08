"""
Testes de integração da recomendação de vagas (app/jobs/router.py).
Responsável pelo módulo: Letícia Teixeira da Rocha Batista.

Endpoint: GET /jobs/recommendations (?refresh=true força nova busca).

O usuário é criado pela API; as entrevistas e notas são gravadas direto no
banco (o fluxo da entrevista já é testado nos outros arquivos). Só a API de vagas
(Jooble) é simulada, pela fixture `vagas_falsas`.
"""
import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.audit.models import AuditLog
from app.evaluation.models import InterviewEvaluation
from app.interview.models import InterviewAnswer, InterviewSession
from app.jobs import jooble
from app.jobs.models import JobRecommendation
from app.onboarding.models import CareerOnboarding

from tests.integration.apoio import SENHA, usuario_autenticado

URL = "/jobs/recommendations"


def _vaga(titulo, descricao="", empresa="Empresa"):
    return {
        "external_id": str(uuid.uuid4())[:8],
        "title": titulo,
        "company": empresa,
        "location": "São Paulo, SP",
        "salary_min": 3500.0,
        "salary_max": None,
        "url": "https://br.jooble.org/desc/1",
        "description": descricao,
        "posted_at": datetime(2026, 11, 1, tzinfo=timezone.utc),
    }


VAGAS_PADRAO = [
    _vaga("Analista de Dados Sênior", "SQL e Python", "A"),
    _vaga("Vendedor Externo", "Atendimento", "B"),
    _vaga("Analista de Dados Júnior", "Buscamos SQL, Python e Power BI", "C"),
    _vaga("Analista de Dados Júnior", "Buscamos SQL, Python e Power BI", "C"),  # repetida
]


class ApiDeVagasFalsa:
    def __init__(self):
        self.termos = []
        self.vagas = list(VAGAS_PADRAO)
        self.falhar = False

    def buscar(self, termo):
        self.termos.append(termo)
        if self.falhar:
            raise jooble.VagasIndisponiveis("O serviço de vagas não respondeu agora.")
        return [dict(vaga) for vaga in self.vagas]


@pytest.fixture
def vagas_falsas(monkeypatch):
    falsa = ApiDeVagasFalsa()
    monkeypatch.setattr("app.jobs.service.jooble.buscar_vagas", falsa.buscar)
    return falsa


def _entrevista(db, user_id, cargo="Analista de Dados Júnior", nivel="junior", nota=None, resposta="Uso SQL e Python."):
    sessao = InterviewSession(
        user_id=uuid.UUID(user_id),
        category="entrevista_de_emprego",
        presentation_type="tecnica",
        seniority=nivel,
        job_title=cargo,
        finished=True,
    )
    db.add(sessao)
    db.flush()
    db.add(InterviewAnswer(session_id=sessao.id, order_index=0, question_text="Pergunta?", answer_text=resposta))
    if nota is not None:
        db.add(InterviewEvaluation(session_id=sessao.id, user_id=sessao.user_id, overall_score=nota, summary="Ok"))
    db.commit()
    return sessao


# --- RN01: sem perfil ------------------------------------------------------------


def test_sem_entrevista_nem_questionario_deve_convidar_a_treinar(api, vagas_falsas):
    _, headers = usuario_autenticado(api, "semperfil")

    resposta = api.get(URL, headers=headers)

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["profile"] is None and corpo["jobs"] == []
    assert "entrevista" in corpo["message"]
    assert vagas_falsas.termos == []


def test_so_com_questionario_deve_usar_o_cargo_da_area_indicada(api, db, vagas_falsas):
    usuario, headers = usuario_autenticado(api, "questionario")
    db.add(CareerOnboarding(user_id=uuid.UUID(usuario["id"]), recommended_area="dados_ia", scores="{}", answers="{}"))
    db.commit()

    perfil = api.get(URL, headers=headers).json()["profile"]

    assert perfil["source"] == "questionario"
    assert perfil["job_title"] == "Analista de Dados"
    assert perfil["area"] == "Dados e Inteligência Artificial"
    assert "SQL" in perfil["skills"]
    assert vagas_falsas.termos == ["Analista de Dados"]


# --- Perfil pelas entrevistas e compatibilidade -----------------------------------


def test_deve_recomendar_vagas_ordenadas_por_compatibilidade(api, db, vagas_falsas):
    usuario, headers = usuario_autenticado(api, "entrevistas")
    _entrevista(db, usuario["id"], nota=8.0, resposta="Faço dashboards no Power BI com SQL e Python.")

    resposta = api.get(URL, headers=headers)

    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    perfil = corpo["profile"]
    assert perfil["job_title"] == "Analista de Dados"
    assert perfil["recommended_seniority"] == "junior"
    assert perfil["average_score"] == 8.0
    assert {"SQL", "Python", "Power BI"} <= set(perfil["skills"])

    titulos = [vaga["title"] for vaga in corpo["jobs"]]
    assert titulos[0] == "Analista de Dados Júnior"
    assert titulos[-1] == "Vendedor Externo"
    assert len(titulos) == 3  # a repetida foi descartada
    notas = [vaga["compatibility"] for vaga in corpo["jobs"]]
    assert notas == sorted(notas, reverse=True)
    assert corpo["jobs"][0]["compatibility"] == 100
    assert corpo["jobs"][0]["reasons"]
    assert corpo["from_cache"] is False


def test_nota_baixa_deve_recomendar_um_nivel_abaixo_e_buscar_estagio(api, db, vagas_falsas):
    usuario, headers = usuario_autenticado(api, "notabaixa")
    _entrevista(db, usuario["id"], nota=3.0)

    perfil = api.get(URL, headers=headers).json()["profile"]

    assert perfil["practiced_seniority"] == "junior"
    assert perfil["recommended_seniority"] == "estagio"
    assert "3,0" in perfil["level_reason"]
    assert vagas_falsas.termos == ["Estágio Analista de Dados"]


def test_cargo_mais_treinado_deve_ganhar_do_mais_recente(api, db, vagas_falsas):
    usuario, headers = usuario_autenticado(api, "maistreinado")
    _entrevista(db, usuario["id"], cargo="Analista de Dados Júnior")
    _entrevista(db, usuario["id"], cargo="Analista de Dados")
    _entrevista(db, usuario["id"], cargo="Desenvolvedor Front-end Júnior")

    perfil = api.get(URL, headers=headers).json()["profile"]

    assert perfil["job_title"] == "Analista de Dados"
    assert perfil["interviews_count"] == 2


# --- RN04: vagas salvas por 24h ----------------------------------------------------


def test_segunda_visita_deve_usar_as_vagas_salvas_sem_chamar_a_api(api, db, vagas_falsas):
    usuario, headers = usuario_autenticado(api, "cache")
    _entrevista(db, usuario["id"], nota=7.5)

    primeira = api.get(URL, headers=headers).json()
    segunda = api.get(URL, headers=headers).json()

    assert len(vagas_falsas.termos) == 1
    assert segunda["from_cache"] is True
    assert [v["id"] for v in segunda["jobs"]] == [v["id"] for v in primeira["jobs"]]
    db.expire_all()
    assert db.query(JobRecommendation).filter_by(user_id=uuid.UUID(usuario["id"])).count() == 3


def test_atualizar_deve_buscar_de_novo_e_substituir_a_lista(api, db, vagas_falsas):
    usuario, headers = usuario_autenticado(api, "atualizar")
    _entrevista(db, usuario["id"])
    api.get(URL, headers=headers)
    vagas_falsas.vagas = [_vaga("Analista de Dados Júnior", "SQL", "Nova")]

    corpo = api.get(URL, params={"refresh": "true"}, headers=headers).json()

    assert len(vagas_falsas.termos) == 2
    assert [v["company"] for v in corpo["jobs"]] == ["Nova"]
    db.expire_all()
    assert db.query(JobRecommendation).filter_by(user_id=uuid.UUID(usuario["id"])).count() == 1


def test_vagas_salvas_ha_mais_de_24h_devem_ser_buscadas_de_novo(api, db, vagas_falsas):
    usuario, headers = usuario_autenticado(api, "expirado")
    _entrevista(db, usuario["id"])
    api.get(URL, headers=headers)
    db.query(JobRecommendation).filter_by(user_id=uuid.UUID(usuario["id"])).update(
        {JobRecommendation.fetched_at: datetime.now(timezone.utc) - timedelta(hours=25)}
    )
    db.commit()

    corpo = api.get(URL, headers=headers).json()

    assert len(vagas_falsas.termos) == 2
    assert corpo["from_cache"] is False


def test_mudanca_de_cargo_deve_invalidar_as_vagas_salvas(api, db, vagas_falsas):
    usuario, headers = usuario_autenticado(api, "outrocargo")
    _entrevista(db, usuario["id"], cargo="Analista de Dados")
    api.get(URL, headers=headers)
    _entrevista(db, usuario["id"], cargo="Desenvolvedor Back-end")
    _entrevista(db, usuario["id"], cargo="Desenvolvedor Back-end")

    api.get(URL, headers=headers)

    assert vagas_falsas.termos == ["Analista de Dados", "Desenvolvedor Back-end"]


# --- RN05: API fora do ar -------------------------------------------------------


def test_api_fora_do_ar_deve_mostrar_as_ultimas_vagas_com_aviso(api, db, vagas_falsas):
    usuario, headers = usuario_autenticado(api, "foradoar")
    _entrevista(db, usuario["id"])
    api.get(URL, headers=headers)
    vagas_falsas.falhar = True

    resposta = api.get(URL, params={"refresh": "true"}, headers=headers)

    assert resposta.status_code == 200
    assert len(resposta.json()["jobs"]) == 3
    assert "últimas vagas salvas" in resposta.json()["warning"]


def test_api_fora_do_ar_sem_vagas_salvas_deve_retornar_503(api, db, vagas_falsas):
    usuario, headers = usuario_autenticado(api, "semcache")
    _entrevista(db, usuario["id"])
    vagas_falsas.falhar = True

    resposta = api.get(URL, headers=headers)

    assert resposta.status_code == 503


# --- Auditoria, segurança e LGPD --------------------------------------------------


def test_busca_na_api_deve_ser_auditada_sem_dados_pessoais(api, db, vagas_falsas):
    usuario, headers = usuario_autenticado(api, "auditoria")
    _entrevista(db, usuario["id"], resposta="Meu nome completo é Maria e uso SQL.")

    api.get(URL, headers=headers)
    api.get(URL, headers=headers)  # do cache: não gera novo evento

    db.expire_all()
    eventos = db.query(AuditLog).filter_by(action="jobs.recommended", user_id=uuid.UUID(usuario["id"])).all()
    assert len(eventos) == 1
    assert json.loads(eventos[0].details) == {"count": 3, "refresh": False}


def test_sem_token_deve_retornar_401(api):
    assert api.get(URL).status_code == 401


def test_usuario_so_ve_as_proprias_vagas(api, db, vagas_falsas):
    dono, headers_dono = usuario_autenticado(api, "dono")
    _entrevista(db, dono["id"])
    api.get(URL, headers=headers_dono)
    _, headers_outro = usuario_autenticado(api, "outro")

    corpo = api.get(URL, headers=headers_outro).json()

    assert corpo["profile"] is None and corpo["jobs"] == []


def test_excluir_a_conta_deve_apagar_as_vagas_recomendadas(api, db, vagas_falsas):
    usuario, headers = usuario_autenticado(api, "lgpdvagas")
    _entrevista(db, usuario["id"])
    api.get(URL, headers=headers)

    resposta = api.request("DELETE", "/auth/me", json={"password": SENHA}, headers=headers)

    assert resposta.status_code == 200, resposta.text
    db.expire_all()
    assert db.query(JobRecommendation).filter_by(user_id=uuid.UUID(usuario["id"])).count() == 0
