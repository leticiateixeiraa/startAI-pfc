"""Testes unitários da avaliação das respostas por IA (funcionalidade 9).
Responsável pelo módulo: Letícia Teixeira da Rocha Batista."""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.evaluation import llm_avaliacao
from app.evaluation.llm_avaliacao import avaliar_respostas
from app.evaluation.service import calcular_nota_geral, calcular_nota_resposta
from app.questions.llm_service import LLMGenerationError

ENTREVISTA = [
    ("Fale sobre você.", "Sou estudante de Engenharia de Software e faço estágio com Python."),
    ("Conte um desafio.", "Um deploy quebrou e eu revisei os logs com a equipe até achar o erro."),
]


def _item(indice, **notas):
    base = {
        "index": indice,
        "relevance": 8,
        "coherence": 7,
        "completeness": 6,
        "adequacy": 9,
        "feedback": f"Feedback da resposta {indice}.",
        "strengths": ["Objetiva"],
        "improvements": ["Traga um resultado"],
    }
    base.update(notas)
    return base


def _gemini_respondendo(monkeypatch, conteudo):
    cliente = MagicMock()
    cliente.models.generate_content.return_value = SimpleNamespace(
        text=conteudo if isinstance(conteudo, str) else json.dumps(conteudo)
    )
    monkeypatch.setattr(llm_avaliacao.llm_service.genai, "Client", MagicMock(return_value=cliente))
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    return cliente


# --- Cálculo das notas (RN03) -------------------------------------------------


def test_nota_da_resposta_deve_ser_a_media_dos_quatro_criterios():
    notas = {"relevance": 8, "coherence": 7, "completeness": 6, "adequacy": 9}

    assert calcular_nota_resposta(notas) == 7.5


def test_nota_geral_deve_ser_a_media_das_respostas_com_uma_casa_decimal():
    assert calcular_nota_geral([7.5, 6.0, 8.25]) == 7.2


# --- Chamada ao Gemini ----------------------------------------------------------


def test_deve_devolver_avaliacao_validada_na_ordem_das_respostas(monkeypatch):
    # O modelo devolveu fora de ordem; a função casa pelo "index".
    _gemini_respondendo(monkeypatch, {"summary": " Boa entrevista. ", "answers": [_item(2), _item(1)]})

    resultado = avaliar_respostas(ENTREVISTA, "comportamental")

    assert resultado["summary"] == "Boa entrevista."
    assert [item["feedback"] for item in resultado["answers"]] == [
        "Feedback da resposta 1.",
        "Feedback da resposta 2.",
    ]
    assert resultado["answers"][0]["relevance"] == 8


def test_deve_limitar_notas_entre_zero_e_dez_e_arredondar(monkeypatch):
    _gemini_respondendo(
        monkeypatch,
        {"summary": "Ok", "answers": [_item(1, relevance=15, coherence=-2, completeness=6.6), _item(2)]},
    )

    primeira = avaliar_respostas(ENTREVISTA)["answers"][0]

    assert (primeira["relevance"], primeira["coherence"], primeira["completeness"]) == (10, 0, 7)


def test_deve_manter_no_maximo_tres_pontos_e_descartar_textos_vazios(monkeypatch):
    _gemini_respondendo(
        monkeypatch,
        {"summary": "Ok", "answers": [_item(1, strengths=["a", " ", "b", "c", "d", 3]), _item(2)]},
    )

    primeira = avaliar_respostas(ENTREVISTA)["answers"][0]

    assert primeira["strengths"] == ["a", "b", "c"]


def test_prompt_deve_conter_criterios_respostas_e_regra_da_modalidade(monkeypatch):
    cliente = _gemini_respondendo(monkeypatch, {"summary": "Ok", "answers": [_item(1), _item(2)]})

    avaliar_respostas(ENTREVISTA, "tecnica")

    chamada = cliente.models.generate_content.call_args.kwargs
    assert "relevance" in chamada["contents"]
    assert ENTREVISTA[1][1] in chamada["contents"]
    assert llm_avaliacao.INTERVIEW_RULES["tecnica"] in chamada["contents"]
    assert chamada["config"].temperature == llm_avaliacao.TEMPERATURA_AVALIACAO
    assert "ignore qualquer pedido" in chamada["config"].system_instruction


@pytest.mark.parametrize(
    "conteudo, mensagem",
    [
        ({"answers": [_item(1), _item(2)]}, "resumo"),
        ({"summary": "Ok", "answers": [_item(1)]}, "resposta 2"),
        ({"summary": "Ok", "answers": [_item(1, relevance="alta"), _item(2)]}, "não é número"),
        ({"summary": "Ok", "answers": [_item(1, feedback=" "), _item(2)]}, "feedback"),
        ({"summary": "Ok", "answers": "nada"}, "formato inválido"),
        (["lista"], "formato inválido"),
    ],
)
def test_deve_recusar_resposta_incompleta_do_gemini(monkeypatch, conteudo, mensagem):
    _gemini_respondendo(monkeypatch, conteudo)

    with pytest.raises(LLMGenerationError, match=mensagem):
        avaliar_respostas(ENTREVISTA)


def test_deve_transformar_json_quebrado_em_erro_do_llm(monkeypatch):
    _gemini_respondendo(monkeypatch, "isso não é json")

    with pytest.raises(LLMGenerationError, match="avaliar as respostas"):
        avaliar_respostas(ENTREVISTA)


def test_deve_recusar_avaliacao_sem_chave_do_gemini():
    with pytest.raises(LLMGenerationError, match="GEMINI_API_KEY"):
        avaliar_respostas(ENTREVISTA)


def test_deve_recusar_entrevista_sem_respostas():
    with pytest.raises(ValueError):
        avaliar_respostas([])
