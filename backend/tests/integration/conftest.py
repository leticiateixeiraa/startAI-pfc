"""
Fixtures dos testes de integração.

Equivalente, em FastAPI, ao `@SpringBootTest(webEnvironment = RANDOM_PORT)`
com `RestClient` visto em aula:

- `url_base` sobe a aplicação de verdade com o uvicorn em uma PORTA
  ALEATÓRIA (o sistema operacional escolhe uma porta livre), uma única vez
  por execução do pytest. Por isso os testes continuam passando mesmo com a
  API de desenvolvimento ligada na porta 8000.
- `api` é um cliente HTTP real (httpx) apontado para esse servidor. O httpx
  não lança exceção em 4xx/5xx, então os cenários de erro são verificados
  com asserções sobre status e corpo.

Cada requisição percorre todas as camadas reais:
HTTP -> autenticação (JWT) -> router -> service -> SQLAlchemy -> banco de
teste. O banco de teste é o SQLite em memória configurado em
`tests/conftest.py` (nasce vazio e some ao final da execução); o banco de
desenvolvimento nunca é tocado.

Somente serviços EXTERNOS são simulados: o Gemini (fixture `gemini_falso`,
que substitui só o cliente `genai.Client`, mantendo real toda a montagem do
prompt e a validação da resposta) e o envio de e-mail por SMTP (fixture
`emails_enviados`).
"""
import json
import socket
import threading
from types import SimpleNamespace

import httpx
import pytest
import uvicorn

from app.main import app
from app.models import base


@pytest.fixture(scope="session")
def url_base():
    # O socket é aberto antes do servidor: a porta já aceita conexões na fila
    # do sistema operacional, então nenhum teste precisa esperar (sleep) o
    # uvicorn terminar de subir.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))  # porta 0 = porta aleatória livre
    sock.listen(128)
    porta = sock.getsockname()[1]

    servidor = uvicorn.Server(uvicorn.Config(app, lifespan="on", log_level="warning"))
    thread = threading.Thread(target=servidor.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()

    yield f"http://127.0.0.1:{porta}"

    servidor.should_exit = True
    thread.join(timeout=10)
    sock.close()


@pytest.fixture
def api(url_base):
    # trust_env=False: ignora proxies configurados na máquina e fala direto
    # com o servidor local de teste.
    with httpx.Client(base_url=url_base, trust_env=False, timeout=10) as cliente:
        yield cliente


@pytest.fixture
def db():
    """Sessão direta no banco de teste, usada SÓ para conferir o que a API
    gravou (ou, quando não há endpoint para isso, preparar um dado)."""
    sessao = base.SessionLocal()
    try:
        yield sessao
    finally:
        sessao.close()


class GeminiFalso:
    """Substituto do `genai.Client` do Google.

    Cada resposta enfileirada com `responder(...)` é devolvida por uma
    chamada a `generate_content`. Os prompts recebidos ficam guardados em
    `prompts`, para o teste conferir o que a aplicação mandou ao modelo.
    """

    def __init__(self):
        self.respostas: list[str] = []
        self.prompts: list[str] = []
        self.models = self

    def responder(self, conteudo) -> None:
        self.respostas.append(conteudo if isinstance(conteudo, str) else json.dumps(conteudo))

    def __call__(self, api_key: str):  # genai.Client(api_key=...)
        return self

    def generate_content(self, model, contents, config):
        self.prompts.append(contents)
        if not self.respostas:
            raise AssertionError("O teste não preparou resposta para o Gemini falso")
        return SimpleNamespace(text=self.respostas.pop(0))


@pytest.fixture
def gemini_falso(monkeypatch):
    falso = GeminiFalso()
    monkeypatch.setenv("GEMINI_API_KEY", "chave-falsa-dos-testes")
    monkeypatch.setattr("app.questions.llm_service.genai.Client", falso)
    return falso


@pytest.fixture
def emails_enviados(monkeypatch):
    """Troca o envio real por SMTP por uma caixa de saída em memória.

    Cada item é (destinatário, token), o que permite ao teste "abrir o
    e-mail" e usar o link de redefinição de senha.
    """
    caixa_de_saida: list[tuple[str, str]] = []
    monkeypatch.setattr(
        "app.auth.router.enviar_email_redefinicao_senha",
        lambda email, token: caixa_de_saida.append((email, token)),
    )
    return caixa_de_saida
