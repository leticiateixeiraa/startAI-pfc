# Recuperação de senha

## Fluxo

1. O usuário clica em "Esqueci minha senha" na tela de login e informa o e-mail.
2. `POST /auth/forgot-password` gera um token aleatório de 32 bytes
   (`secrets.token_urlsafe`), guarda apenas o **hash SHA-256** desse token no
   banco (nunca o token em texto puro) com validade de 30 minutos, e envia
   por e-mail um link contendo o token: `/reset-password?token=...`.
3. A resposta da API é **idêntica**, com ou sem e-mail cadastrado — mesma
   proteção contra enumeração de usuários já usada no login.
4. O usuário abre o link, define a nova senha (mesmas regras de força do
   cadastro), e `POST /auth/reset-password` valida o token: precisa existir,
   não ter expirado e não ter sido usado antes.
5. Após o uso, o token é marcado como usado (`used_at`) e não pode ser
   reaproveitado, mesmo dentro da janela de 30 minutos.

## Envio de e-mail

O envio usa `smtplib` (biblioteca padrão do Python, sem dependência extra)
via SMTP, configurado por variáveis de ambiente:

| Variável | Descrição |
|---|---|
| `SMTP_HOST`, `SMTP_PORT` | Servidor SMTP (ex.: `smtp.gmail.com`, porta `587`) |
| `SMTP_USER`, `SMTP_PASSWORD` | Credenciais — no caso do Gmail, uma "senha de app" |
| `FRONTEND_URL` | Base usada para montar o link de redefinição |

Se essas variáveis não estiverem configuradas, o endpoint responde
**502 Bad Gateway**, deixando claro que a falha é no serviço externo de
e-mail, e não um erro da própria API.

## Testes

`backend/tests/integration/test_reset_password.py` cobre: token válido, token
inexistente, token expirado, token já usado, e a não revelação de quais
e-mails têm conta cadastrada.