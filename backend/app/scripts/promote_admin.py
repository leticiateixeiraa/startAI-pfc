"""
feat(admin): concede ou remove o papel de administrador.

O cadastro público NUNCA cria administradores. O primeiro admin (e os
seguintes) são definidos por quem tem acesso ao servidor, rodando na pasta
backend/:

    python -m app.scripts.promote_admin email@exemplo.com
    python -m app.scripts.promote_admin email@exemplo.com --revoke

A conta precisa já estar cadastrada. A mudança fica registrada na auditoria.
"""
import argparse
import sys

from sqlalchemy import func

from app.audit.service import record_event
from app.auth.models import User
from app.auth.schemas import ROLE_ADMIN, ROLE_USER
from app.models.base import SessionLocal


def alterar_papel(email: str, revogar: bool = False) -> str:
    db = SessionLocal()
    try:
        user = db.query(User).filter(func.lower(User.email) == email.strip().lower()).first()
        if not user:
            raise LookupError(f"Nenhuma conta cadastrada com o e-mail {email}")

        novo_papel = ROLE_USER if revogar else ROLE_ADMIN
        user.role = novo_papel
        record_event(
            db,
            "admin.role_revoked" if revogar else "admin.role_granted",
            None,
            "user",
            str(user.id),
            {"role": novo_papel, "origem": "script promote_admin"},
        )
        db.commit()
        return novo_papel
    finally:
        db.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Concede ou remove o papel de administrador.")
    parser.add_argument("email", help="E-mail de uma conta já cadastrada")
    parser.add_argument("--revoke", action="store_true", help="Remove o papel de administrador")
    args = parser.parse_args(argv)

    try:
        papel = alterar_papel(args.email, args.revoke)
    except LookupError as erro:
        print(erro, file=sys.stderr)
        return 1
    print(f"{args.email} agora tem o papel '{papel}'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
