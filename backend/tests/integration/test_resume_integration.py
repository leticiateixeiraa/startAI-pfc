"""
Testes de integração da análise de currículo (app/resume/router.py).

Endpoints: POST /resume/analyze (multipart), GET /resume/me, DELETE /resume/me.
O Gemini é simulado por ser serviço externo. Os arquivos são montados em
memória e a exclusão de conta (LGPD) é conferida no banco.
"""
import io
import uuid
import zipfile

from app.audit.models import AuditLog
from app.resume.models import ResumeAnalysis
from tests.integration.apoio import SENHA, usuario_autenticado

PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"


def _docx(texto: str) -> bytes:
    xml = f'<w:document xmlns:w="x"><w:body><w:p><w:r><w:t>{texto}</w:t></w:r></w:p></w:body></w:document>'
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as pacote:
        pacote.writestr("word/document.xml", xml)
    return buffer.getvalue()


def _analise(**extra) -> dict:
    return {
        "is_resume": True,
        "overall_score": 7.2,
        "summary": "Bom currículo de quem está começando.",
        "criteria": {"structure": 8, "clarity": 7, "impact": 6, "relevance": 7},
        "strengths": ["Projetos práticos"],
        "improvements": [{"title": "Quantifique", "suggestion": "Inclua números nos resultados."}],
        "skills_found": ["Python"],
        "skills_missing": ["Docker"],
        "suggested_job_title": "Desenvolvedor Back-end Júnior",
        **extra,
    }


def _enviar(api, headers, conteudo=PDF, nome="curriculo.pdf", tipo="application/pdf", **form):
    return api.post(
        "/resume/analyze",
        files={"file": (nome, conteudo, tipo)},
        data=form,
        headers=headers,
    )


def test_analyze_de_pdf_deve_retornar_200_com_a_analise_e_registrar_auditoria(api, db, gemini_falso):
    usuario, headers = usuario_autenticado(api, "cv")
    gemini_falso.responder(_analise())

    resposta = _enviar(api, headers, target_role="Desenvolvedor Back-end")

    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert corpo["overall_score"] == 7.2
    assert corpo["file_type"] == "pdf"
    assert corpo["file_name"] == "curriculo.pdf"
    assert corpo["target_role"] == "Desenvolvedor Back-end"
    assert [c["key"] for c in corpo["criteria"]][0] == "structure"
    evento = (
        db.query(AuditLog)
        .filter(AuditLog.action == "resume.analyzed")
        .order_by(AuditLog.created_at.desc())
        .first()
    )
    # A auditoria guarda só metadados, nunca o conteúdo nem o nome do arquivo.
    assert "curriculo.pdf" not in (evento.details or "")
    assert "pdf" in evento.details


def test_analyze_de_docx_deve_enviar_o_texto_do_documento_ao_gemini(api, gemini_falso):
    _, headers = usuario_autenticado(api, "cv_docx")
    gemini_falso.responder(_analise())
    texto = "Desenvolvedora Python com projetos em FastAPI e PostgreSQL, atuação em equipe."

    resposta = _enviar(api, headers, conteudo=_docx(texto), nome="cv.docx", tipo="application/octet-stream")

    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["file_type"] == "docx"
    assert texto in gemini_falso.prompts[0]


def test_get_me_antes_de_enviar_deve_retornar_null_e_depois_a_ultima_analise(api, gemini_falso):
    _, headers = usuario_autenticado(api, "cv_get")
    assert api.get("/resume/me", headers=headers).json() is None

    gemini_falso.responder(_analise())
    _enviar(api, headers)

    salva = api.get("/resume/me", headers=headers).json()
    assert salva["summary"] == "Bom currículo de quem está começando."


def test_novo_envio_deve_substituir_a_analise_anterior(api, db, gemini_falso):
    usuario, headers = usuario_autenticado(api, "cv_troca")
    gemini_falso.responder(_analise(overall_score=5, summary="Primeira versão."))
    gemini_falso.responder(_analise(overall_score=8, summary="Segunda versão."))

    _enviar(api, headers, nome="v1.pdf")
    _enviar(api, headers, nome="v2.pdf")

    atual = api.get("/resume/me", headers=headers).json()
    assert (atual["summary"], atual["file_name"]) == ("Segunda versão.", "v2.pdf")
    db.expire_all()
    assert db.query(ResumeAnalysis).filter(ResumeAnalysis.user_id == uuid.UUID(usuario["id"])).count() == 1


def test_analise_de_um_usuario_nao_deve_aparecer_para_outro(api, gemini_falso):
    _, dono = usuario_autenticado(api, "cv_dono")
    _, outro = usuario_autenticado(api, "cv_outro")
    gemini_falso.responder(_analise())
    _enviar(api, dono)

    assert api.get("/resume/me", headers=outro).json() is None


def test_endpoints_sem_token_devem_retornar_401(api):
    assert api.post("/resume/analyze", files={"file": ("a.pdf", PDF, "application/pdf")}).status_code == 401
    assert api.get("/resume/me").status_code == 401
    assert api.delete("/resume/me").status_code == 401


def test_delete_me_deve_apagar_a_analise_e_ser_idempotente(api, gemini_falso):
    _, headers = usuario_autenticado(api, "cv_del")
    gemini_falso.responder(_analise())
    _enviar(api, headers)

    assert api.delete("/resume/me", headers=headers).status_code == 204
    assert api.get("/resume/me", headers=headers).json() is None
    assert api.delete("/resume/me", headers=headers).status_code == 204


def test_analyze_com_formato_nao_suportado_deve_retornar_415_sem_chamar_o_gemini(api, gemini_falso):
    _, headers = usuario_autenticado(api, "cv_415")
    resposta = _enviar(api, headers, conteudo=b"so um texto", nome="cv.txt", tipo="text/plain")
    assert resposta.status_code == 415
    assert gemini_falso.prompts == []


def test_analyze_nao_deve_confiar_no_nome_nem_no_content_type(api, gemini_falso):
    _, headers = usuario_autenticado(api, "cv_mentira")
    # Termina em .pdf e diz ser PDF, mas o conteúdo é outra coisa.
    resposta = _enviar(api, headers, conteudo=b"MZ\x90\x00 programa", nome="cv.pdf", tipo="application/pdf")
    assert resposta.status_code == 415
    assert gemini_falso.prompts == []


def test_analyze_com_arquivo_vazio_deve_retornar_400(api):
    _, headers = usuario_autenticado(api, "cv_vazio")
    assert _enviar(api, headers, conteudo=b"").status_code == 400


def test_analyze_com_arquivo_acima_de_5mb_deve_retornar_413(api, gemini_falso):
    _, headers = usuario_autenticado(api, "cv_grande")
    resposta = _enviar(api, headers, conteudo=b"%PDF-" + b"x" * (5 * 1024 * 1024))
    assert resposta.status_code == 413
    assert gemini_falso.prompts == []


def test_analyze_de_arquivo_que_nao_e_curriculo_deve_retornar_422_e_nao_salvar(api, gemini_falso):
    _, headers = usuario_autenticado(api, "cv_outro_doc")
    gemini_falso.responder({"is_resume": False})

    resposta = _enviar(api, headers)

    assert resposta.status_code == 422
    assert api.get("/resume/me", headers=headers).json() is None


def test_analyze_de_docx_sem_texto_deve_retornar_422(api, gemini_falso):
    _, headers = usuario_autenticado(api, "cv_docx_vazio")
    assert _enviar(api, headers, conteudo=_docx("oi"), nome="cv.docx").status_code == 422
    assert gemini_falso.prompts == []


def test_analyze_com_gemini_indisponivel_deve_retornar_502(api):
    # Sem a fixture gemini_falso não há GEMINI_API_KEY: o serviço recusa.
    _, headers = usuario_autenticado(api, "cv_502")
    assert _enviar(api, headers).status_code == 502


def test_excluir_a_conta_deve_apagar_a_analise_do_curriculo(api, db, gemini_falso):
    usuario, headers = usuario_autenticado(api, "cv_lgpd")
    gemini_falso.responder(_analise())
    _enviar(api, headers)
    id_usuario = uuid.UUID(usuario["id"])
    assert db.query(ResumeAnalysis).filter(ResumeAnalysis.user_id == id_usuario).count() == 1

    resposta = api.request("DELETE", "/auth/me", json={"password": SENHA}, headers=headers)

    assert resposta.status_code in (200, 204), resposta.text
    db.expire_all()
    assert db.query(ResumeAnalysis).filter(ResumeAnalysis.user_id == id_usuario).count() == 0
