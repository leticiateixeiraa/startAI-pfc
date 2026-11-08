"""Testes unitários da trilha de estudos gerada por IA (app/roadmap/llm_trilha.py)."""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.questions import llm_service
from app.questions.llm_service import LLMGenerationError
from app.roadmap.llm_trilha import gerar_trilha
from app.roadmap.recursos import RECURSOS, link_de_video

CONTEXTO = {
    "job_title": "Desenvolvedor Back-end Júnior",
    "presentation_type": "tecnica",
    "seniority": "junior",
    "overall_score": 5.5,
    "criteria": {"relevance": 7, "completeness": 4},
    "improvements": ["Cite resultados"],
    "mistakes": ['"REST é um protocolo": REST é um estilo de arquitetura.'],
    "next_steps": ["Revisar HTTP"],
}


def _etapa(numero: int, **extra) -> dict:
    return {
        "title": f"Etapa {numero}",
        "description": f"Estude o assunto {numero}.",
        "focus": "Ponto fraco da entrevista.",
        "estimated_time": "1 semana",
        "tips": ["Dica 1", "Dica 2"],
        "practice": "Construa uma API.",
        "resources": [{"id": "leetcode"}],
        **extra,
    }


def _gemini_respondendo(monkeypatch, conteudo) -> MagicMock:
    cliente = MagicMock()
    cliente.models.generate_content.return_value = SimpleNamespace(
        text=conteudo if isinstance(conteudo, str) else json.dumps(conteudo)
    )
    monkeypatch.setattr(llm_service.genai, "Client", MagicMock(return_value=cliente))
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    return cliente


def test_deve_devolver_trilha_validada_com_links_do_catalogo(monkeypatch):
    _gemini_respondendo(monkeypatch, {"title": "Rumo ao back-end", "steps": [_etapa(n) for n in range(1, 6)]})

    trilha = gerar_trilha(CONTEXTO)

    assert trilha["title"] == "Rumo ao back-end"
    assert len(trilha["steps"]) == 5
    recurso = trilha["steps"][0]["resources"][0]
    assert recurso["url"] == RECURSOS["leetcode"]["url"]
    assert recurso["title"] == RECURSOS["leetcode"]["name"]


def test_ids_fora_do_catalogo_e_links_escritos_pela_ia_devem_ser_descartados(monkeypatch):
    recursos = [
        {"id": "site-inventado"},
        {"type": "site", "title": "Blog", "url": "https://link-inventado.example/artigo"},
        {"id": "mdn"},
        {"id": "mdn"},  # repetido
        {"type": "video", "title": "HTTP para iniciantes", "search": "protocolo HTTP explicado"},
        {"type": "video", "title": "Sem busca"},
    ]
    _gemini_respondendo(
        monkeypatch, {"title": "T", "steps": [_etapa(1, resources=recursos), _etapa(2), _etapa(3)]}
    )

    resultado = gerar_trilha(CONTEXTO)["steps"][0]["resources"]

    assert [item["title"] for item in resultado] == ["MDN Web Docs", "HTTP para iniciantes"]
    assert resultado[1]["url"] == link_de_video("protocolo HTTP explicado")
    assert resultado[1]["url"].startswith("https://www.youtube.com/results?search_query=")
    assert all("link-inventado" not in item["url"] for item in resultado)


def test_etapas_incompletas_sao_descartadas_e_o_limite_e_respeitado(monkeypatch):
    etapas = [_etapa(n) for n in range(1, 12)] + [{"title": "Sem descrição"}]
    _gemini_respondendo(monkeypatch, {"title": "T", "steps": etapas})

    trilha = gerar_trilha(CONTEXTO)

    assert len(trilha["steps"]) == 8
    assert all(etapa["description"] for etapa in trilha["steps"])


def test_prompt_deve_trazer_vaga_nivel_erros_e_catalogo(monkeypatch):
    cliente = _gemini_respondendo(monkeypatch, {"title": "T", "steps": [_etapa(n) for n in range(1, 4)]})

    gerar_trilha(CONTEXTO)

    prompt = cliente.models.generate_content.call_args.kwargs["contents"]
    assert "Desenvolvedor Back-end Júnior" in prompt
    assert "Nível da vaga: Júnior" in prompt
    assert "REST é um estilo de arquitetura" in prompt
    assert "- leetcode: LeetCode" in prompt
    assert "NÃO escreva links" in prompt


@pytest.mark.parametrize(
    "conteudo, mensagem",
    [
        ({"steps": [_etapa(1), _etapa(2), _etapa(3)]}, "título"),
        ({"title": "T", "steps": "várias"}, "formato inválido"),
        ({"title": "T", "steps": [_etapa(1), _etapa(2)]}, "menos de 3 etapas"),
        (["lista"], "formato inválido"),
        ("não é json", "gerar a trilha"),
    ],
)
def test_deve_recusar_trilha_invalida(monkeypatch, conteudo, mensagem):
    _gemini_respondendo(monkeypatch, conteudo)

    with pytest.raises(LLMGenerationError, match=mensagem):
        gerar_trilha(CONTEXTO)


def test_deve_recusar_sem_chave_do_gemini():
    with pytest.raises(LLMGenerationError, match="GEMINI_API_KEY"):
        gerar_trilha(CONTEXTO)
