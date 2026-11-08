"""Testes unitários da recomendação de vagas (funcionalidade 7).
Responsável pelo módulo: Letícia Teixeira da Rocha Batista."""
from types import SimpleNamespace

import httpx
import pytest

from app.jobs import jooble
from app.jobs.service import (
    calcular_compatibilidade,
    cargo_sem_nivel,
    habilidades_no_texto,
    nivel_do_titulo,
    nivel_recomendado,
    termo_de_busca,
)

PERFIL = {
    "job_title": "Analista de Dados",
    "recommended_seniority": "junior",
    "skills": ["SQL", "Python", "Power BI"],
}


def _vaga(titulo, descricao=""):
    return {"title": titulo, "description": descricao}


# --- Perfil -----------------------------------------------------------------


@pytest.mark.parametrize(
    "cargo, esperado",
    [
        ("Analista de Dados Júnior", "Analista de Dados"),
        ("Desenvolvedor Back-end Jr.", "Desenvolvedor Back-end"),
        ("Estágio em Desenvolvimento Web", "Desenvolvimento Web"),
        ("Desenvolvedor(a) Front-end", "Desenvolvedor Front-end"),
        ("Especialista em Dados Sênior", "Especialista em Dados"),
    ],
)
def test_deve_tirar_o_nivel_do_cargo_e_manter_o_resto(cargo, esperado):
    assert cargo_sem_nivel(cargo) == esperado


@pytest.mark.parametrize(
    "titulo, nivel",
    [
        ("Analista de Dados Júnior", "junior"),
        ("Desenvolvedor Python Jr", "junior"),
        ("Estagiário de TI", "estagio"),
        ("Engenheiro de Dados Sênior", "senior"),
        ("Analista de BI Pleno", "pleno"),
        ("Analista de Dados", None),
    ],
)
def test_deve_reconhecer_o_nivel_pelo_titulo_da_vaga(titulo, nivel):
    assert nivel_do_titulo(titulo) == nivel


def test_deve_encontrar_habilidades_sem_confundir_java_com_javascript():
    encontradas = habilidades_no_texto("Experiência com JavaScript, PostgreSQL e Power BI")

    assert {"JavaScript", "SQL", "Power BI"} <= set(encontradas)
    assert "Java" not in encontradas


# --- RN02: nível compatível com o desempenho ----------------------------------


@pytest.mark.parametrize(
    "treinado, media, esperado",
    [
        ("junior", 8.2, "junior"),  # >= 7: mantém
        ("junior", 5.0, "junior"),  # entre 4 e 7: mantém, sugere treinar
        ("junior", 3.1, "estagio"),  # < 4: um nível abaixo
        ("pleno", 2.0, "junior"),
        ("estagio", 1.0, "estagio"),  # não existe nível abaixo de estágio
        ("senior", None, "senior"),  # sem nota: o nível treinado
    ],
)
def test_nivel_recomendado_deve_seguir_a_media_das_notas(treinado, media, esperado):
    nivel, explicacao = nivel_recomendado(treinado, media)

    assert nivel == esperado
    assert explicacao


def test_busca_de_estagio_deve_incluir_a_palavra_estagio():
    assert termo_de_busca({**PERFIL, "recommended_seniority": "estagio"}) == "Estágio Analista de Dados"
    assert termo_de_busca(PERFIL) == "Analista de Dados"


# --- RN03: compatibilidade -----------------------------------------------------


def test_vaga_ideal_deve_ter_100_de_compatibilidade_e_explicar_o_motivo():
    vaga = _vaga("Analista de Dados Júnior", "Buscamos pessoa com SQL, Python e Power BI.")

    pontos, motivos = calcular_compatibilidade(vaga, PERFIL)

    assert pontos == 100
    assert any("bate com o cargo" in motivo for motivo in motivos)
    assert any("nível Júnior" in motivo for motivo in motivos)
    assert any("SQL, Python, Power BI" in motivo for motivo in motivos)


def test_vaga_de_nivel_muito_acima_deve_ficar_atras_de_uma_vaga_do_nivel_certo():
    certa, _ = calcular_compatibilidade(_vaga("Analista de Dados Júnior", "SQL"), PERFIL)
    acima, _ = calcular_compatibilidade(_vaga("Analista de Dados Sênior", "SQL"), PERFIL)
    sem_nivel, _ = calcular_compatibilidade(_vaga("Analista de Dados", "SQL"), PERFIL)

    assert certa > sem_nivel > acima


def test_vaga_de_outro_cargo_deve_ter_compatibilidade_baixa():
    pontos, _ = calcular_compatibilidade(_vaga("Vendedor Externo", "Atendimento ao cliente."), PERFIL)

    assert pontos < 30


# --- Cliente da Jooble ---------------------------------------------------------


def _resposta(corpo, status=200):
    requisicao = httpx.Request("POST", jooble.URL_PADRAO)
    return httpx.Response(status, json=corpo, request=requisicao)


@pytest.fixture
def com_chave(monkeypatch):
    monkeypatch.setenv("JOOBLE_API_KEY", "chave-de-teste")


def test_deve_normalizar_vagas_e_descartar_links_que_nao_sao_http(monkeypatch, com_chave):
    resultados = [
        {
            "id": 123,
            "title": "<b>Analista</b> de Dados",
            "snippet": "Vaga com &amp; SQL " + "x " * 400,
            "link": "https://br.jooble.org/desc/123",
            "company": "Empresa X",
            "location": "São Paulo, SP",
            "salary": "R$ 3.500,00 - R$ 4.200,00",
            "updated": "2026-11-01T10:00:00.0000000",
        },
        {"title": "Golpe", "link": "javascript:alert(1)"},
        {"title": "", "link": "https://exemplo.com"},
    ]
    chamada = {}

    def post_falso(url, json, timeout):
        chamada.update(url=url, corpo=json)
        return _resposta({"totalCount": 3, "jobs": resultados})

    monkeypatch.setattr(jooble.httpx, "post", post_falso)

    vagas = jooble.buscar_vagas("Analista de Dados")

    assert len(vagas) == 1
    vaga = vagas[0]
    assert vaga["title"] == "Analista de Dados"
    assert vaga["company"] == "Empresa X"
    assert (vaga["salary_min"], vaga["salary_max"]) == (3500.0, 4200.0)
    assert vaga["description"].startswith("Vaga com & SQL")
    assert len(vaga["description"]) <= jooble.TAMANHO_DESCRICAO + 1
    assert vaga["posted_at"].year == 2026 and vaga["posted_at"].tzinfo is not None
    assert chamada["corpo"]["keywords"] == "Analista de Dados"
    assert chamada["url"] == "https://br.jooble.org/api/chave-de-teste"


def test_endereco_da_api_pode_ser_trocado_pelo_env(monkeypatch, com_chave):
    monkeypatch.setenv("JOOBLE_API_URL", "https://jooble.org/api/")
    chamada = {}
    monkeypatch.setattr(
        jooble.httpx, "post", lambda url, json, timeout: chamada.update(url=url) or _resposta({"jobs": []})
    )

    jooble.buscar_vagas("Analista")

    assert chamada["url"] == "https://jooble.org/api/chave-de-teste"


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("R$ 3.000 - R$ 4.500", (3000.0, 4500.0)),
        ("R$ 2.800,50", (2800.5, None)),
        ("A combinar", (None, None)),
        ("", (None, None)),
        (None, (None, None)),
        ("Escala 6x1, R$ 1.900", (1900.0, None)),
    ],
)
def test_deve_ler_o_salario_que_vem_como_texto(texto, esperado):
    assert jooble._salario(texto) == esperado


def test_sem_chave_da_jooble_deve_avisar_sem_chamar_a_api():
    with pytest.raises(jooble.VagasIndisponiveis, match="JOOBLE_API_KEY"):
        jooble.buscar_vagas("Analista de Dados")


@pytest.mark.parametrize("falha", ["chave_recusada", "fora_do_ar", "rede", "formato"])
def test_falha_da_jooble_deve_virar_vagas_indisponiveis(monkeypatch, com_chave, falha):
    def post_falso(url, json, timeout):
        if falha == "rede":
            raise httpx.ConnectTimeout("demorou")
        if falha == "chave_recusada":
            return _resposta({}, status=403)
        if falha == "fora_do_ar":
            return _resposta({}, status=500)
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {"vagas": "?"})

    monkeypatch.setattr(jooble.httpx, "post", post_falso)

    with pytest.raises(jooble.VagasIndisponiveis) as erro:
        jooble.buscar_vagas("Analista de Dados")
    if falha == "chave_recusada":
        assert "chave" in str(erro.value)
