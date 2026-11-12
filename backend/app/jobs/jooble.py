"""
Cliente da API de vagas da Jooble (https://br.jooble.org/api/about).

A Jooble junta vagas de vários sites de emprego. O plano gratuito dá 500
chamadas no total por chave, sem mensalidade e sem cartão; como as vagas
ficam salvas por 24h para cada aluno (RN04 do service.py), isso sobra para
o projeto. Cada país tem a sua chave: a do Brasil é pedida em
br.jooble.org/api/about e vai em JOOBLE_API_KEY no .env.

LGPD: para a Jooble vai SÓ o texto da busca (cargo e nível). Nome, e-mail
e respostas do aluno nunca saem do nosso backend.
"""
import html
import logging
import os
import re
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

# Endereço da API do domínio brasileiro. Fica no .env (JOOBLE_API_URL) caso a
# Jooble indique outro endereço junto com a chave.
URL_PADRAO = "https://br.jooble.org/api/"
TEMPO_LIMITE_SEGUNDOS = 10
MAX_RESULTADOS = 30
TAMANHO_DESCRICAO = 400


class VagasIndisponiveis(Exception):
    """A API de vagas não está configurada ou não respondeu."""


def _texto_limpo(valor) -> str:
    """Tira tags HTML (a Jooble destaca palavras com <b>) e espaços extras."""
    if not isinstance(valor, str):
        return ""
    sem_tags = re.sub(r"<[^>]+>", " ", html.unescape(valor))
    return re.sub(r"\s+", " ", sem_tags).strip()


def _valor(numero: str) -> float | None:
    """'3.500,00' ou '3500' -> 3500.0 (formato brasileiro)."""
    numero = numero.strip()
    if "," in numero:
        numero = numero.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", numero):
        numero = numero.replace(".", "")
    try:
        return float(numero)
    except ValueError:
        return None


def _salario(texto) -> tuple[float | None, float | None]:
    """A Jooble manda o salário como texto, ex.: 'R$ 3.000 - R$ 4.500'."""
    if not isinstance(texto, str) or not texto.strip():
        return None, None
    numeros = [_valor(n) for n in re.findall(r"\d[\d.,]*", texto)]
    numeros = [n for n in numeros if n and n >= 100]  # ignora "40h", "6x1"...
    if not numeros:
        return None, None
    return numeros[0], (numeros[1] if len(numeros) > 1 else None)


def _data(valor) -> datetime | None:
    if not isinstance(valor, str) or not valor.strip():
        return None
    # A Jooble pode mandar 7 casas nos segundos; o Python aceita até 6.
    texto = re.sub(r"(\.\d{6})\d+", r"\1", valor.strip().replace("Z", "+00:00"))
    try:
        data = datetime.fromisoformat(texto)
    except ValueError:
        return None
    return data if data.tzinfo else data.replace(tzinfo=timezone.utc)


def _normalizar(item: dict) -> dict | None:
    """Converte uma vaga da Jooble para o nosso formato. None se faltar o básico."""
    titulo = _texto_limpo(item.get("title"))
    url = item.get("link")
    # Só links http(s): evita que um link "javascript:" chegue ao navegador.
    if not titulo or not isinstance(url, str) or not re.match(r"^https?://", url):
        return None
    descricao = _texto_limpo(item.get("snippet"))
    if len(descricao) > TAMANHO_DESCRICAO:
        descricao = descricao[:TAMANHO_DESCRICAO].rsplit(" ", 1)[0] + "…"
    salario_min, salario_max = _salario(item.get("salary"))
    return {
        "external_id": str(item.get("id") or "")[:64] or None,
        "title": titulo[:300],
        "company": _texto_limpo(item.get("company"))[:200] or None,
        "location": _texto_limpo(item.get("location"))[:200] or None,
        "salary_min": salario_min,
        "salary_max": salario_max,
        "url": url,
        "description": descricao or None,
        "posted_at": _data(item.get("updated")),
    }


def buscar_vagas(termo: str) -> list[dict]:
    """Busca vagas no Brasil para o termo (ex.: "Analista de Dados")."""
    chave = os.getenv("JOOBLE_API_KEY")
    if not chave:
        raise VagasIndisponiveis(
            "A busca de vagas não está configurada. Adicione JOOBLE_API_KEY no .env."
        )
    url = (os.getenv("JOOBLE_API_URL") or URL_PADRAO).rstrip("/") + "/" + chave

    corpo = {
        "keywords": termo,
        "location": "",  # vazio = o país inteiro da chave (Brasil)
        "page": "1",
        "ResultOnPage": str(MAX_RESULTADOS),
    }
    try:
        resposta = httpx.post(url, json=corpo, timeout=TEMPO_LIMITE_SEGUNDOS)
        resposta.raise_for_status()
        dados = resposta.json()
    except httpx.HTTPStatusError as error:
        # Não loga a URL: ela contém a chave da API.
        logger.warning("Jooble respondeu com status %s", error.response.status_code)
        mensagem = "O serviço de vagas não respondeu agora. Tente novamente em alguns minutos."
        if error.response.status_code in (401, 403):
            mensagem = "A chave da API de vagas foi recusada (inválida ou sem chamadas restantes)."
        raise VagasIndisponiveis(mensagem) from error
    except (httpx.HTTPError, ValueError) as error:
        logger.warning("Falha ao consultar a Jooble: %s", type(error).__name__)
        raise VagasIndisponiveis(
            "O serviço de vagas não respondeu agora. Tente novamente em alguns minutos."
        ) from error

    resultados = dados.get("jobs") if isinstance(dados, dict) else None
    if not isinstance(resultados, list):
        raise VagasIndisponiveis("O serviço de vagas devolveu uma resposta inesperada.")
    vagas = [_normalizar(item) for item in resultados if isinstance(item, dict)]
    return [vaga for vaga in vagas if vaga]
