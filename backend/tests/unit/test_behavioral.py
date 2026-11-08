"""Testes unitários do perfil comportamental (app/behavioral)."""
from app.behavioral.competencias import (
    COMPETENCIAS,
    competencia_mais_forte,
    competencia_mais_fraca,
    definir_arquetipo,
)


def _notas(**alteradas):
    return {**dict.fromkeys(COMPETENCIAS, 5), **alteradas}


def test_arquetipo_deve_ser_a_competencia_com_maior_nota():
    arquetipo = definir_arquetipo(_notas(lideranca=9))

    assert arquetipo["key"] == "lideranca"
    assert arquetipo["name"] == "Perfil de Liderança"


def test_empate_deve_respeitar_a_ordem_das_competencias():
    notas = _notas(trabalho_em_equipe=8, adaptabilidade=8)

    assert competencia_mais_forte(notas) == "trabalho_em_equipe"
    assert competencia_mais_fraca(_notas(lideranca=2, inteligencia_emocional=2)) == "lideranca"
