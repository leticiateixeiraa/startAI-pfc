"""
test(interview-backend): testes do entrevistador dinâmico (mock)

Rode com: pytest
Requer o mesmo banco de teste configurado via DATABASE_URL usado pelos
demais testes (ver test_auth.py).

Cada teste registra e loga seu próprio usuário (com e-mail aleatório) pra
não depender de estado deixado por outros testes.
"""
import uuid

from fastapi.testclient import TestClient

from app.main import app


def email_unico(prefixo: str) -> str:
    return f"{prefixo}_{uuid.uuid4().hex[:8]}@example.com"


def _criar_usuario_autenticado(client: TestClient, prefixo: str) -> dict:
    payload = {
        "email": email_unico(prefixo),
        "password": "senha-forte-123",
        "name": "Usuário de Teste",
        "terms_accepted": True,
    }
    client.post("/auth/register", json=payload)
    login_response = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_mock_start_retorna_primeira_pergunta():
    with TestClient(app) as client:
        headers = _criar_usuario_autenticado(client, "gabriel_start")

        response = client.post(
            "/interviews/mock-start",
            json={"category": "entrevista_de_emprego"},
            headers=headers,
        )
        assert response.status_code == 201
        body = response.json()
        assert "session_id" in body
        assert len(body["questions"]) == 1
        assert body["questions"][0] != ""


def test_resposta_com_palavra_chave_gera_pergunta_adaptada():
    with TestClient(app) as client:
        headers = _criar_usuario_autenticado(client, "gabriel_adapt")

        start = client.post(
            "/interviews/mock-start",
            json={"category": "entrevista_de_emprego"},
            headers=headers,
        )
        session_id = start.json()["session_id"]

        response = client.post(
            f"/interviews/{session_id}/answer",
            json={
                "answer_text": (
                    "Enfrentei um grande desafio no meu último projeto, "
                    "mas consegui resolver estudando bastante o problema."
                )
            },
            headers=headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["adapted"] is True
        assert body["finished"] is False
        assert body["question"] is not None


def test_resposta_curta_pede_mais_detalhes():
    with TestClient(app) as client:
        headers = _criar_usuario_autenticado(client, "gabriel_curta")

        start = client.post(
            "/interviews/mock-start",
            json={"category": "entrevista_de_emprego"},
            headers=headers,
        )
        session_id = start.json()["session_id"]

        response = client.post(
            f"/interviews/{session_id}/answer",
            json={"answer_text": "Sou organizado."},
            headers=headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["adapted"] is True
        assert "detalhar" in body["question"].lower()


def test_fluxo_completo_ate_finalizar():
    with TestClient(app) as client:
        headers = _criar_usuario_autenticado(client, "gabriel_fluxo")

        categorias = client.get("/questions/categories")
        assert categorias.status_code == 200
        assert {categoria["id"] for categoria in categorias.json()} == {
            "entrevista_de_emprego",
            "apresentacao_academica",
        }

        start = client.post(
            "/interviews/mock-start",
            json={"category": "apresentacao_academica"},
            headers=headers,
        )
        session_id = start.json()["session_id"]

        historico = client.get("/interviews/history", headers=headers)
        assert historico.status_code == 200
        sessao = next(item for item in historico.json() if item["session_id"] == session_id)
        assert sessao["category"] == "apresentacao_academica"
        assert sessao["answered_count"] == 0

        # Respostas neutras (sem palavras-chave, com bastante conteúdo) pra
        # percorrer o roteiro fixo sem disparar adaptação, até finalizar.
        resposta_neutra = (
            "Esta é uma resposta suficientemente longa e detalhada para não "
            "disparar nenhuma regra de adaptação do entrevistador mockado."
        )

        finished = False
        for _ in range(10):  # limite de segurança contra loop infinito no teste
            response = client.post(
                f"/interviews/{session_id}/answer",
                json={"answer_text": resposta_neutra},
                headers=headers,
            )
            assert response.status_code == 200
            body = response.json()
            if body["finished"]:
                finished = True
                assert body["question"] is None
                break

        assert finished is True

        # Depois de finalizada, novas respostas devem ser rejeitadas.
        response = client.post(
            f"/interviews/{session_id}/answer",
            json={"answer_text": "qualquer coisa"},
            headers=headers,
        )
        assert response.status_code == 400


def test_answer_sem_token_falha():
    with TestClient(app) as client:
        fake_session_id = uuid.uuid4()
        response = client.post(
            f"/interviews/{fake_session_id}/answer",
            json={"answer_text": "resposta qualquer"},
        )
        assert response.status_code == 401


def test_answer_de_sessao_de_outro_usuario_falha():
    with TestClient(app) as client:
        headers_dono = _criar_usuario_autenticado(client, "gabriel_dono")
        headers_outro = _criar_usuario_autenticado(client, "gabriel_outro")

        start = client.post(
            "/interviews/mock-start",
            json={"category": "entrevista_de_emprego"},
            headers=headers_dono,
        )
        session_id = start.json()["session_id"]

        response = client.post(
            f"/interviews/{session_id}/answer",
            json={"answer_text": "tentando responder a sessão de outra pessoa"},
            headers=headers_outro,
        )
        assert response.status_code == 403
