"""Testes unitários do questionário de primeiro acesso (app/onboarding)."""
import pytest

from app.onboarding.questionario import AREAS, PERGUNTAS
from app.onboarding.service import (
    RespostasInvalidas,
    area_recomendada,
    calcular_pontos,
    listar_perguntas,
    ranking,
)


def _respostas_para(area: str) -> dict[str, str]:
    """Escolhe, em cada pergunta, a alternativa que mais pontua a área."""
    return {
        pergunta["id"]: max(pergunta["options"], key=lambda opcao: opcao["weights"].get(area, 0))["id"]
        for pergunta in PERGUNTAS
    }


def test_toda_area_deve_ser_alcancavel_pelo_questionario():
    for area in AREAS:
        assert area_recomendada(calcular_pontos(_respostas_para(area))) == area


def test_pesos_devem_apontar_para_areas_existentes():
    for pergunta in PERGUNTAS:
        for opcao in pergunta["options"]:
            assert set(opcao["weights"]) <= set(AREAS)


def test_perguntas_enviadas_ao_front_nao_devem_ter_os_pesos():
    perguntas = listar_perguntas()

    assert len(perguntas) == len(PERGUNTAS)
    assert all("weights" not in opcao for pergunta in perguntas for opcao in pergunta["options"])


def test_ranking_deve_ser_porcentagem_do_total_em_ordem_decrescente():
    pontos = {**dict.fromkeys(AREAS, 0), "backend": 6, "dados_ia": 3, "qa": 1}

    resultado = ranking(pontos)

    assert [item["key"] for item in resultado[:3]] == ["backend", "dados_ia", "qa"]
    assert [item["percent"] for item in resultado[:3]] == [60, 30, 10]
    assert len(resultado) == len(AREAS)


def test_empate_deve_respeitar_a_ordem_das_areas():
    pontos = {**dict.fromkeys(AREAS, 0), "qa": 4, "frontend": 4}

    assert area_recomendada(pontos) == "frontend"


def test_deve_recusar_questionario_incompleto():
    respostas = _respostas_para("backend")
    respostas.pop(PERGUNTAS[0]["id"])

    with pytest.raises(RespostasInvalidas, match="todas as perguntas"):
        calcular_pontos(respostas)


def test_deve_recusar_alternativa_inexistente():
    respostas = {**_respostas_para("backend"), PERGUNTAS[0]["id"]: "z"}

    with pytest.raises(RespostasInvalidas, match="Alternativa inválida"):
        calcular_pontos(respostas)
