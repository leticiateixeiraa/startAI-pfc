"""
Testes unitários do entrevistador dinâmico (app/interview/service.py).

Cobrem as regras que decidem a PRÓXIMA PERGUNTA da entrevista:
  - palavras-chave ("desafio", "equipe", "prazo") geram pergunta de aprofundamento;
  - resposta muito curta pede mais detalhes;
  - fluxo normal segue o roteiro; a última resposta finaliza a entrevista.

Isolamento: nenhum teste sobe o FastAPI, acessa banco ou rede.
  - `_adapt_next_question` é uma função pura (não precisa de mock).
  - `register_answer_and_get_next` recebe um `db` falso (MagicMock) e uma
    sessão simples (SimpleNamespace); o LLM (`generate_adapted_question`) é
    substituído por mock.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.interview import service
from app.interview.models import InterviewAnswer
from app.interview.service import (
    FOLLOWUP_TRIGGERS,
    MIN_WORDS_FOR_DETAILED_ANSWER,
    QUESTION_BANK,
    _adapt_next_question,
    register_answer_and_get_next,
)
from app.questions.llm_service import LLMGenerationError

CATEGORIA = "entrevista_de_emprego"
BANCO = QUESTION_BANK[CATEGORIA]
PERGUNTA_DETALHAR = "Pode detalhar um pouco mais sua resposta anterior, com um exemplo concreto?"

# Resposta longa (>= 8 palavras) e sem nenhuma palavra-chave de aprofundamento.
RESPOSTA_LONGA_NEUTRA = (
    "Trabalho há cinco anos com desenvolvimento de software "
    "e gosto muito de aprender tecnologias novas"
)


def _followup_de(palavra: str) -> str:
    """Pergunta de aprofundamento configurada para uma palavra-chave."""
    for palavras, pergunta in FOLLOWUP_TRIGGERS:
        if palavra in palavras:
            return pergunta
    raise AssertionError(f"palavra-chave {palavra!r} não existe em FOLLOWUP_TRIGGERS")


def _sessao(index: int = 0, finished: bool = False, texto: str | None = "usar-banco"):
    """Sessão simples. `texto='usar-banco'` -> pergunta atual = a do banco no index."""
    if texto == "usar-banco":
        texto = BANCO[index] if index < len(BANCO) else None
    return SimpleNamespace(
        id="sessao-1",
        category=CATEGORIA,
        presentation_type=CATEGORIA,
        seniority=None,
        current_index=index,
        current_question_text=texto,
        finished=finished,
    )


def _db_falso(perguntas_geradas: int = 0) -> MagicMock:
    """Banco falso: sem perguntas geradas pelo LLM, nenhuma pergunta salva na sessão."""
    db = MagicMock()
    db.query.return_value.filter.return_value.count.return_value = perguntas_geradas
    db.query.return_value.filter.return_value.first.return_value = None
    return db


# --- Regra 1: palavras-chave geram pergunta de aprofundamento ----------------


@pytest.mark.parametrize(
    "resposta, palavra",
    [
        ("O maior desafio foi migrar o sistema legado sem parar a operação da empresa", "desafio"),
        ("Eu trabalhei junto com a equipe de produto durante todo o projeto de lançamento", "equipe"),
        ("Tivemos um prazo muito curto para entregar a primeira versão do módulo de pagamentos", "prazo"),
    ],
)
def test_deve_aprofundar_quando_resposta_contem_palavra_chave(resposta, palavra):
    # Act
    pergunta, adaptada = _adapt_next_question(CATEGORIA, resposta, next_index=1)

    # Assert
    assert adaptada is True
    assert pergunta == _followup_de(palavra)


def test_deve_reconhecer_palavra_chave_independente_de_maiusculas():
    # Arrange
    resposta = "O DESAFIO mais complicado foi conciliar as entregas com os testes automatizados"

    # Act
    pergunta, adaptada = _adapt_next_question(CATEGORIA, resposta, next_index=1)

    # Assert
    assert adaptada is True
    assert pergunta == _followup_de("desafio")


# --- Regra 2: resposta curta pede mais detalhes ------------------------------


def test_deve_pedir_detalhes_quando_resposta_e_curta():
    # Act
    pergunta, adaptada = _adapt_next_question(CATEGORIA, "Sim, gosto bastante", next_index=1)

    # Assert
    assert adaptada is True
    assert pergunta == PERGUNTA_DETALHAR


@pytest.mark.parametrize(
    "quantidade_de_palavras, deve_pedir_detalhes",
    [
        (0, True),  # vazio
        (1, True),
        (MIN_WORDS_FOR_DETAILED_ANSWER - 1, True),  # logo abaixo do limite
        (MIN_WORDS_FOR_DETAILED_ANSWER, False),  # exatamente no limite
        (MIN_WORDS_FOR_DETAILED_ANSWER + 1, False),
    ],
)
def test_deve_aplicar_limite_minimo_de_palavras_na_fronteira(quantidade_de_palavras, deve_pedir_detalhes):
    # Arrange — palavras neutras, sem nenhuma palavra-chave
    resposta = " ".join(["casa"] * quantidade_de_palavras)

    # Act
    pergunta, adaptada = _adapt_next_question(CATEGORIA, resposta, next_index=1)

    # Assert
    assert adaptada is deve_pedir_detalhes
    if deve_pedir_detalhes:
        assert pergunta == PERGUNTA_DETALHAR
    else:
        assert pergunta == BANCO[1]


def test_palavra_chave_deve_ter_prioridade_sobre_resposta_curta():
    # Arrange — curta (2 palavras) E com palavra-chave
    resposta = "Foi um desafio"

    # Act
    pergunta, adaptada = _adapt_next_question(CATEGORIA, resposta, next_index=1)

    # Assert — vale o aprofundamento, não o pedido genérico de detalhes
    assert adaptada is True
    assert pergunta == _followup_de("desafio")
    assert pergunta != PERGUNTA_DETALHAR


# --- Regra 3: fluxo normal segue o roteiro -----------------------------------


def test_deve_seguir_roteiro_quando_resposta_e_boa_e_sem_palavra_chave():
    # Act
    pergunta, adaptada = _adapt_next_question(CATEGORIA, RESPOSTA_LONGA_NEUTRA, next_index=1)

    # Assert
    assert adaptada is False
    assert pergunta == BANCO[1]


def test_deve_devolver_none_quando_acabou_o_roteiro():
    # Act — índice além da última pergunta do banco
    pergunta, adaptada = _adapt_next_question(CATEGORIA, RESPOSTA_LONGA_NEUTRA, next_index=len(BANCO))

    # Assert
    assert pergunta is None
    assert adaptada is False


# --- Finalização da entrevista (register_answer_and_get_next) ----------------


def test_deve_finalizar_entrevista_ao_responder_a_ultima_pergunta():
    # Arrange
    ultimo = len(BANCO) - 1
    sessao = _sessao(index=ultimo)
    db = _db_falso()

    # Act
    proxima, adaptada, finalizada = register_answer_and_get_next(db, sessao, RESPOSTA_LONGA_NEUTRA)

    # Assert
    assert (proxima, adaptada, finalizada) == (None, False, True)
    assert sessao.finished is True
    assert sessao.current_question_text is None
    db.commit.assert_called_once()


def test_deve_salvar_a_resposta_ao_finalizar_a_entrevista():
    # Arrange
    sessao = _sessao(index=len(BANCO) - 1)
    db = _db_falso()

    # Act
    register_answer_and_get_next(db, sessao, RESPOSTA_LONGA_NEUTRA)

    # Assert — a última resposta não pode ser perdida
    db.add.assert_called_once()
    resposta_salva = db.add.call_args.args[0]
    assert isinstance(resposta_salva, InterviewAnswer)
    assert resposta_salva.answer_text == RESPOSTA_LONGA_NEUTRA
    assert resposta_salva.question_text == BANCO[-1]


def test_nao_deve_salvar_resposta_quando_sessao_ja_estava_finalizada():
    # Arrange
    sessao = _sessao(index=len(BANCO), finished=True, texto=None)
    db = _db_falso()

    # Act
    proxima, adaptada, finalizada = register_answer_and_get_next(db, sessao, "qualquer resposta")

    # Assert
    assert (proxima, adaptada, finalizada) == (None, False, True)
    db.add.assert_not_called()  # never(): nada é gravado numa sessão encerrada
    db.commit.assert_called_once()


# --- Fluxo: persistência + adaptação -----------------------------------------


def test_deve_salvar_resposta_e_avancar_para_a_proxima_pergunta():
    # Arrange
    sessao = _sessao(index=0)
    db = _db_falso()

    # Act
    proxima, adaptada, finalizada = register_answer_and_get_next(db, sessao, RESPOSTA_LONGA_NEUTRA)

    # Assert
    assert (proxima, adaptada, finalizada) == (BANCO[1], False, False)
    assert sessao.current_index == 1
    assert sessao.current_question_text == BANCO[1]
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_deve_inserir_pergunta_adaptada_quando_resposta_menciona_prazo():
    # Arrange
    sessao = _sessao(index=0)
    db = _db_falso()
    resposta = "No último projeto trabalhei sob um prazo bem apertado e entreguei no dia combinado"

    # Act
    proxima, adaptada, finalizada = register_answer_and_get_next(db, sessao, resposta)

    # Assert
    assert adaptada is True
    assert finalizada is False
    assert proxima == _followup_de("prazo")
    assert sessao.current_question_text == _followup_de("prazo")


# --- LLM mockado --------------------------------------------------------------


def test_deve_usar_pergunta_do_llm_quando_sessao_tem_perguntas_geradas(monkeypatch):
    # Arrange
    gerador = MagicMock(return_value="Pergunta personalizada gerada pelo LLM")
    monkeypatch.setattr(service, "generate_adapted_question", gerador)
    sessao = _sessao(index=0)
    db = _db_falso(perguntas_geradas=3)
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    # Act
    proxima, adaptada, finalizada = register_answer_and_get_next(db, sessao, RESPOSTA_LONGA_NEUTRA)

    # Assert
    assert (proxima, adaptada, finalizada) == ("Pergunta personalizada gerada pelo LLM", True, False)
    gerador.assert_called_once()


def test_deve_cair_para_regras_locais_quando_llm_falha(monkeypatch):
    # Arrange — o LLM está fora do ar
    gerador = MagicMock(side_effect=LLMGenerationError("serviço indisponível"))
    monkeypatch.setattr(service, "generate_adapted_question", gerador)
    sessao = _sessao(index=0)
    db = _db_falso(perguntas_geradas=3)
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    resposta = "Enfrentei um grande desafio ao integrar dois sistemas que não conversavam entre si"

    # Act
    proxima, adaptada, finalizada = register_answer_and_get_next(db, sessao, resposta)

    # Assert — a entrevista continua usando a regra de palavra-chave
    assert finalizada is False
    assert adaptada is True
    assert proxima == _followup_de("desafio")


def test_nao_deve_chamar_llm_quando_nao_ha_perguntas_geradas(monkeypatch):
    # Arrange
    gerador = MagicMock()
    monkeypatch.setattr(service, "generate_adapted_question", gerador)
    sessao = _sessao(index=0)
    db = _db_falso(perguntas_geradas=0)

    # Act
    register_answer_and_get_next(db, sessao, RESPOSTA_LONGA_NEUTRA)

    # Assert
    gerador.assert_not_called()  # never()
