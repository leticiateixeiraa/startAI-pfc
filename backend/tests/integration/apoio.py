"""
Funções auxiliares dos testes de integração (equivalentes ao
`buildBookRequest` e ao `criarLivro` da aula).

Todos os dados são criados pelos PRÓPRIOS endpoints da API. Os e-mails
levam `time.time_ns()`, então cada execução gera dados novos: a suíte pode
rodar várias vezes seguidas, em qualquer ordem, sem um teste depender de
dado deixado por outro.
"""
import time

import httpx

from app.scripts.promote_admin import alterar_papel

SENHA = "Entrevista#2026"
DESCRICAO_VAGA = (
    "Desenvolvimento de APIs REST em Python com FastAPI, PostgreSQL, testes "
    "automatizados e trabalho em equipe ágil."
)


def email_unico(prefixo: str) -> str:
    return f"{prefixo}_{time.time_ns()}@example.com"


def montar_cadastro(prefixo: str = "aluno", **extra) -> dict:
    return {
        "email": email_unico(prefixo),
        "password": SENHA,
        "name": "Pessoa de Teste",
        "terms_accepted": True,
        **extra,
    }


def cadastrar(api: httpx.Client, prefixo: str = "aluno", **extra) -> dict:
    """Cadastra pela API e devolve o corpo da resposta (id, email, name, role)."""
    resposta = api.post("/auth/register", json=montar_cadastro(prefixo, **extra))
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def autenticar(api: httpx.Client, email: str, senha: str = SENHA) -> dict:
    """Faz login pela API e devolve o header Authorization pronto."""
    resposta = api.post("/auth/login", json={"email": email, "password": senha})
    assert resposta.status_code == 200, resposta.text
    return {"Authorization": f"Bearer {resposta.json()['access_token']}"}


def usuario_autenticado(api: httpx.Client, prefixo: str = "aluno") -> tuple[dict, dict]:
    usuario = cadastrar(api, prefixo)
    return usuario, autenticar(api, usuario["email"])


def admin_autenticado(api: httpx.Client) -> tuple[dict, dict]:
    """Cria um administrador. O cadastro público nunca concede o papel de
    admin (regra RN05), então a promoção usa a mesma função do script
    oficial `python -m app.scripts.promote_admin`."""
    usuario = cadastrar(api, "admin")
    alterar_papel(usuario["email"])
    return usuario, autenticar(api, usuario["email"])


def iniciar_entrevista_mock(api: httpx.Client, headers: dict, categoria: str = "entrevista_de_emprego") -> dict:
    resposta = api.post("/interviews/mock-start", json={"category": categoria}, headers=headers)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def responder(api: httpx.Client, headers: dict, session_id: str, texto: str) -> httpx.Response:
    return api.post(f"/interviews/{session_id}/answer", json={"answer_text": texto}, headers=headers)


def montar_entrevista_ia(presentation_type: str = "tecnica", **extra) -> dict:
    return {
        "job_title": "Desenvolvedor Back-end Júnior",
        "presentation_type": presentation_type,
        "job_description": DESCRICAO_VAGA,
        **extra,
    }


def perguntas_geradas(prefixo: str = "Pergunta") -> list[str]:
    return [f"{prefixo} {numero} sobre a vaga?" for numero in range(1, 6)]


def montar_roadmap(titulo: str = "Plano de estudos", etapas: int = 3) -> dict:
    return {
        "title": titulo,
        "objective": "Melhorar respostas comportamentais",
        "items": [
            {"title": f"Etapa {numero}", "description": f"Descrição da etapa {numero}"}
            for numero in range(1, etapas + 1)
        ],
    }


def criar_roadmap(api: httpx.Client, headers: dict, **kwargs) -> dict:
    resposta = api.post("/roadmaps", json=montar_roadmap(**kwargs), headers=headers)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()
