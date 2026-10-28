"""
Testes unitários da regra de SENHA FORTE (app/auth/schemas.py).

Regra (docs/seguranca-login.md):
  - mínimo de 8 caracteres;
  - pelo menos uma letra e um número;
  - pelo menos um caractere especial;
  - máximo de 72 bytes (limite do bcrypt).

São testes unitários puros: não usam banco, rede nem a aplicação FastAPI.
"""
import pytest
from pydantic import ValidationError

from app.auth.schemas import ResetPasswordRequest, UserCreate

SENHA_FORTE = "Entrevista#2026"


def _cadastro_com_senha(senha: str) -> dict:
    return {"email": "aluna@umc.br", "password": senha, "terms_accepted": True}


def _senha_de_tamanho(tamanho: int) -> str:
    """Senha que cumpre todas as regras (letra, número e especial) e tem
    exatamente `tamanho` caracteres — assim só o tamanho decide o resultado."""
    return "a1!" + "x" * (tamanho - 3)


def test_deve_aceitar_cadastro_quando_senha_cumpre_todas_as_regras():
    # Arrange
    dados = _cadastro_com_senha(SENHA_FORTE)

    # Act
    usuario = UserCreate(**dados)

    # Assert
    assert usuario.password == SENHA_FORTE


@pytest.mark.parametrize(
    "senha_fraca, trecho_da_mensagem",
    [
        ("SenhaSemNumero!", "A senha precisa conter letras e números"),
        ("1234567890!", "A senha precisa conter letras e números"),
        ("SemEspecial2026", "A senha precisa conter também um caractere especial"),
    ],
    ids=["sem_numero", "sem_letra", "sem_caractere_especial"],
)
def test_deve_rejeitar_cadastro_quando_senha_viola_regra_de_composicao(
    senha_fraca, trecho_da_mensagem
):
    # Arrange
    dados = _cadastro_com_senha(senha_fraca)

    # Act
    with pytest.raises(ValidationError) as erro:
        UserCreate(**dados)

    # Assert
    assert trecho_da_mensagem in erro.value.errors()[0]["msg"]


def test_deve_rejeitar_senha_com_7_caracteres():
    # Arrange — 7 é o último tamanho ainda proibido
    dados = _cadastro_com_senha(_senha_de_tamanho(7))

    # Act
    with pytest.raises(ValidationError) as erro:
        UserCreate(**dados)

    # Assert
    assert "A senha precisa ter pelo menos 8 caracteres" in erro.value.errors()[0]["msg"]


@pytest.mark.parametrize(
    "senha_no_limite",
    [_senha_de_tamanho(8), _senha_de_tamanho(72)],
    ids=["exatamente_8_caracteres", "exatamente_72_bytes"],
)
def test_deve_aceitar_senha_exatamente_na_fronteira_de_tamanho(senha_no_limite):
    # Arrange
    dados = _cadastro_com_senha(senha_no_limite)

    # Act
    usuario = UserCreate(**dados)

    # Assert
    assert usuario.password == senha_no_limite


@pytest.mark.parametrize(
    "senha_longa_demais",
    [
        _senha_de_tamanho(73),
        # 38 caracteres, mas 73 bytes: cada "ç" ocupa 2 bytes em UTF-8.
        # Mostra que o teto é contado em BYTES (o que o bcrypt enxerga).
        "a1!" + "ç" * 35,
    ],
    ids=["73_caracteres_ascii", "38_caracteres_acentuados_que_somam_73_bytes"],
)
def test_deve_rejeitar_senha_que_ultrapassa_72_bytes(senha_longa_demais):
    # Arrange
    dados = _cadastro_com_senha(senha_longa_demais)

    # Act
    with pytest.raises(ValidationError) as erro:
        UserCreate(**dados)

    # Assert
    assert "A senha pode ter no máximo 72 caracteres" in erro.value.errors()[0]["msg"]


def test_deve_aplicar_a_mesma_regra_de_senha_forte_na_redefinicao_de_senha():
    # Arrange — a redefinição não pode ser uma porta dos fundos para senha fraca
    senha_sem_especial = "SemEspecial2026"

    # Act
    with pytest.raises(ValidationError) as erro:
        ResetPasswordRequest(token="qualquer-token", new_password=senha_sem_especial)

    # Assert
    assert "caractere especial" in erro.value.errors()[0]["msg"]


# --- Validação do nome no cadastro -------------------------------------------


def test_deve_aceitar_cadastro_sem_nome():
    assert UserCreate(**_cadastro_com_senha(SENHA_FORTE)).name is None


def test_deve_remover_espacos_extras_do_nome():
    dados = {**_cadastro_com_senha(SENHA_FORTE), "name": "  Letícia   Teixeira "}
    assert UserCreate(**dados).name == "Letícia Teixeira"


@pytest.mark.parametrize(
    ("nome", "mensagem"),
    [
        ("   ", "pelo menos 2 caracteres"),
        ("A", "pelo menos 2 caracteres"),
        ("x" * 101, "no máximo 100 caracteres"),
        ("12345", "precisa conter letras"),
    ],
)
def test_deve_recusar_nome_invalido(nome, mensagem):
    dados = {**_cadastro_com_senha(SENHA_FORTE), "name": nome}
    with pytest.raises(ValidationError, match=mensagem):
        UserCreate(**dados)
