"""Testes unitários do nível da vaga (estágio, júnior, pleno, sênior) nos prompts."""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.evaluation.llm_avaliacao import avaliar_respostas
from app.questions import llm_service
from app.questions.llm_service import (
    SENIORITY_LEVELS,
    generate_adapted_question,
    generate_questions,
    seniority_rule,
)


def _gemini_respondendo(monkeypatch, conteudo: dict) -> MagicMock:
    cliente = MagicMock()
    cliente.models.generate_content.return_value = SimpleNamespace(text=json.dumps(conteudo))
    monkeypatch.setattr(llm_service.genai, "Client", MagicMock(return_value=cliente))
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    return cliente


def _prompt(cliente: MagicMock) -> str:
    return cliente.models.generate_content.call_args.kwargs["contents"]


def test_regra_do_nivel_deve_trazer_o_nome_e_ficar_vazia_sem_nivel():
    assert seniority_rule("senior").startswith("Nível da vaga: Sênior.")
    assert seniority_rule(None) == ""
    assert seniority_rule("inexistente") == ""


def test_geracao_de_perguntas_deve_incluir_o_nivel_no_prompt(monkeypatch):
    cliente = _gemini_respondendo(monkeypatch, {"questions": [f"Pergunta {n}?" for n in range(1, 6)]})

    generate_questions("Desenvolvedor", "tecnica", "Criar APIs REST com Python.", "estagio")

    prompt = _prompt(cliente)
    assert SENIORITY_LEVELS["estagio"]["rule"] in prompt
    assert "dificuldade" in prompt


def test_geracao_sem_nivel_nao_deve_mencionar_nivel(monkeypatch):
    cliente = _gemini_respondendo(monkeypatch, {"questions": [f"Pergunta {n}?" for n in range(1, 6)]})

    generate_questions("Desenvolvedor", "tecnica", "Criar APIs REST com Python.")

    assert "Nível da vaga" not in _prompt(cliente)


def test_pergunta_adaptada_deve_considerar_o_nivel(monkeypatch):
    cliente = _gemini_respondendo(monkeypatch, {"question": "Como você escalaria isso?"})

    generate_adapted_question("Fale de um projeto.", "Fiz uma API.", [], "tecnica", "senior")

    assert SENIORITY_LEVELS["senior"]["rule"] in _prompt(cliente)


def test_avaliacao_deve_ajustar_a_exigencia_ao_nivel(monkeypatch):
    avaliacao = {
        "summary": "Ok",
        "answers": [
            {
                "index": 1,
                "relevance": 8,
                "coherence": 8,
                "completeness": 8,
                "adequacy": 8,
                "feedback": "Bom.",
            }
        ],
    }
    cliente = _gemini_respondendo(monkeypatch, avaliacao)

    avaliar_respostas([("Fale de você.", "Sou estudante.")], "tecnica", "junior")

    prompt = _prompt(cliente)
    assert "Nível da vaga: Júnior" in prompt
    assert "Ajuste a exigência" in prompt
