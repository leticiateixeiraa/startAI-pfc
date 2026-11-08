"""
Cria o .env da raiz a partir do .env.example, sem precisar editar nada à mão
para o projeto subir.

Uso (na raiz do repositório):
    python scripts/configurar_env.py

O que ele faz:
- copia o .env.example para .env (se o .env ainda não existir);
- gera uma JWT_SECRET_KEY forte quando ela estiver vazia;
- pergunta a senha do PostgreSQL e as chaves do Gemini e da Jooble (Enter pula);
- aproveita os valores de um backend/.env antigo, se existir.

Rodar de novo é seguro: o que já está preenchido no .env não é apagado.
Só usa a biblioteca padrão do Python, então funciona antes do pip install.
"""
import secrets
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
EXEMPLO = RAIZ / ".env.example"
DESTINO = RAIZ / ".env"
ENV_ANTIGO = RAIZ / "backend" / ".env"

VALORES_DE_EXEMPLO = {"", "troque-por-uma-chave-secreta-forte", "cole-aqui-a-chave-do-aistudio"}


def ler_variaveis(caminho: Path) -> dict[str, str]:
    variaveis = {}
    if not caminho.exists():
        return variaveis
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        variaveis[chave.strip()] = valor.strip()
    return variaveis


def perguntar(texto: str) -> str:
    # Sem terminal (ex.: rodando em CI), não trava esperando resposta.
    if not sys.stdin.isatty():
        return ""
    try:
        return input(texto).strip()
    except EOFError:
        return ""


def main() -> None:
    if not EXEMPLO.exists():
        sys.exit("Não encontrei o .env.example na raiz do projeto.")

    atuais = ler_variaveis(ENV_ANTIGO)
    atuais.update({k: v for k, v in ler_variaveis(DESTINO).items() if v})
    novos = {}

    if atuais.get("JWT_SECRET_KEY", "") in VALORES_DE_EXEMPLO:
        novos["JWT_SECRET_KEY"] = secrets.token_urlsafe(48)
        print("JWT_SECRET_KEY gerada automaticamente.")

    url_banco = atuais.get("DATABASE_URL", ler_variaveis(EXEMPLO)["DATABASE_URL"])
    if "SUA_SENHA" in url_banco:
        senha = perguntar("Senha do seu PostgreSQL local (Enter para preencher depois): ")
        if senha:
            novos["DATABASE_URL"] = url_banco.replace("SUA_SENHA", senha)

    if atuais.get("GEMINI_API_KEY", "") in VALORES_DE_EXEMPLO:
        chave = perguntar("Chave do Gemini (Enter para preencher depois): ")
        if chave:
            novos["GEMINI_API_KEY"] = chave

    # Vagas (Jooble): opcional, só a página Vagas depende dela.
    if atuais.get("JOOBLE_API_KEY", "") in VALORES_DE_EXEMPLO:
        chave_vagas = perguntar("Chave da Jooble (Enter para preencher depois): ")
        if chave_vagas:
            novos["JOOBLE_API_KEY"] = chave_vagas

    # Reescreve o .env seguindo a ordem e os comentários do .env.example.
    linhas = []
    for linha in EXEMPLO.read_text(encoding="utf-8").splitlines():
        if "=" in linha and not linha.lstrip().startswith("#"):
            chave = linha.split("=", 1)[0].strip()
            if chave in novos:
                linha = f"{chave}={novos[chave]}"
            elif atuais.get(chave):
                linha = f"{chave}={atuais[chave]}"
        linhas.append(linha)
    DESTINO.write_text("\n".join(linhas) + "\n", encoding="utf-8")

    print(f".env salvo em {DESTINO}")
    final = ler_variaveis(DESTINO)
    pendentes = [
        nome for nome in ("GEMINI_API_KEY", "JOOBLE_API_KEY")
        if final.get(nome, "") in VALORES_DE_EXEMPLO
    ]
    if "SUA_SENHA" in final.get("DATABASE_URL", ""):
        pendentes.append("DATABASE_URL (senha do PostgreSQL)")
    if pendentes:
        print("Ainda falta preencher no .env: " + ", ".join(pendentes))


if __name__ == "__main__":
    main()
