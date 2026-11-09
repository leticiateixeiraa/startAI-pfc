"""
feat(resume): validação e leitura do arquivo do currículo (PDF ou DOCX).

O tipo é decidido pelo CONTEÚDO do arquivo (assinatura dos primeiros bytes),
nunca pelo nome ou pelo Content-Type enviado pelo navegador, que podem
mentir. PDF vai inteiro para o Gemini, que lê o documento (inclusive
digitalizado). DOCX não é aceito pelo Gemini, então o texto é extraído aqui.
"""
import html
import io
import re
import zipfile

MAX_BYTES = 5 * 1024 * 1024
MAX_DOCX_XML_BYTES = 20 * 1024 * 1024  # descompactado: barra "zip bomb"
MAX_TEXTO = 30_000  # caracteres enviados ao modelo


class ArquivoInvalido(Exception):
    """O arquivo não pode ser analisado. `status_code` é o HTTP a devolver."""

    status_code = 400


class ArquivoVazio(ArquivoInvalido):
    status_code = 400


class ArquivoGrande(ArquivoInvalido):
    status_code = 413


class FormatoNaoSuportado(ArquivoInvalido):
    status_code = 415


class ArquivoSemConteudo(ArquivoInvalido):
    status_code = 422


def detectar_tipo(dados: bytes) -> str:
    """Valida tamanho e formato; devolve "pdf" ou "docx"."""
    if not dados:
        raise ArquivoVazio("O arquivo enviado está vazio.")
    if len(dados) > MAX_BYTES:
        raise ArquivoGrande("O arquivo é grande demais (limite de 5 MB).")

    if dados.startswith(b"%PDF-"):
        if b"/Encrypt" in dados:
            raise ArquivoSemConteudo(
                "Esse PDF está protegido por senha. Salve uma versão sem proteção e envie de novo."
            )
        return "pdf"

    if dados.startswith(b"PK"):
        try:
            with zipfile.ZipFile(io.BytesIO(dados)) as pacote:
                if "word/document.xml" in pacote.namelist():
                    return "docx"
        except zipfile.BadZipFile:
            pass

    raise FormatoNaoSuportado("Formato não suportado. Envie o currículo em PDF ou DOCX.")


def extrair_texto_docx(dados: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(dados)) as pacote:
            info = pacote.getinfo("word/document.xml")
            if info.file_size > MAX_DOCX_XML_BYTES:
                raise ArquivoSemConteudo("O documento é complexo demais para ser lido.")
            xml = pacote.read("word/document.xml").decode("utf-8", errors="replace")
    except (zipfile.BadZipFile, KeyError) as error:
        raise FormatoNaoSuportado("Não foi possível ler o arquivo DOCX.") from error

    # Sem parser XML de propósito: só interessa o texto dos <w:t>, e assim não
    # há entidades externas nem expansão de entidades para se preocupar.
    xml = re.sub(r"</w:p>|<w:br\s*/?>|<w:tab\s*/?>", "\n", xml)
    trechos = re.findall(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>|(\n)", xml, flags=re.DOTALL)
    texto = "".join(html.unescape(conteudo) if conteudo else "\n" for conteudo, quebra in trechos)
    texto = re.sub(r"\n{3,}", "\n\n", texto).strip()

    if len(texto) < 50:
        raise ArquivoSemConteudo(
            "Não encontrei texto suficiente no documento. Confira se o arquivo é o currículo certo."
        )
    return texto[:MAX_TEXTO]
