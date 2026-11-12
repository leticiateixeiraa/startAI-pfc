# Login e segurança

## Autenticação

O usuário se cadastra em `POST /auth/register` e entra em `POST /auth/login` com
e-mail e senha. Em caso de sucesso, a API devolve um token JWT assinado com
HMAC-SHA256 (HS256), contendo o identificador do usuário (`sub`), a data de
emissão (`iat`) e a data de expiração (`exp`, 24 horas por padrão).

O front-end guarda o token no `localStorage` e o envia em todas as
requisições no cabeçalho `Authorization: Bearer <token>`. Quando a API
responde 401 (token expirado, inválido ou adulterado), um interceptor de
resposta do Axios (`frontend/src/services/api.ts`) apaga o token e leva o
usuário de volta ao login automaticamente.

Decisões de segurança:

- O e-mail é normalizado (minúsculas, sem espaços) no cadastro e no login.
- A mensagem de erro é a mesma para "e-mail não existe" e "senha errada", e o
  tempo de resposta também: o login compara a senha informada com um hash
  fictício quando o e-mail não existe, em vez de recusar de imediato. Assim
  não é possível descobrir, medindo a resposta, quais e-mails têm conta
  cadastrada (ataque de enumeração por *timing*).
- A chave de assinatura (`JWT_SECRET_KEY`) e a URL do banco (`DATABASE_URL`)
  ficam só no arquivo `.env`, fora do repositório. Sem elas configuradas, a
  API se recusa a iniciar.

## Autorização

A dependência `get_current_user` (`app/auth/dependencies.py`) é injetada em
todas as rotas protegidas. Ela valida o token e devolve o `user_id`; sem
token válido, a resposta é 401. As únicas rotas públicas são cadastro,
login e listagem de categorias de entrevista.

Além de exigir login, cada rota filtra os dados pelo `user_id` do token: o
usuário só vê o próprio histórico, os próprios logs de auditoria e os
próprios roadmaps, e recebe 403 ao tentar responder uma sessão de entrevista
de outra pessoa.

## Criptografia das senhas

As senhas são armazenadas com bcrypt (biblioteca passlib), um algoritmo de
hash lento e com "salt" aleatório: a mesma senha gera hashes diferentes a
cada vez, e o hash não pode ser revertido para o texto original. A senha em
texto puro nunca é salva, nunca é devolvida pela API, e nunca aparece nos
logs de auditoria — mesmo em tentativas de login que falham.

Regras de senha, validadas no backend (`app/auth/schemas.py`) e repetidas no
front-end apenas para dar retorno imediato ao usuário — quem garante a regra
de verdade é sempre a API:

- mínimo de 8 caracteres;
- pelo menos uma letra e um número;
- pelo menos um caractere especial (ex.: `! @ # $ % - _`);
- máximo de 72 bytes, limite físico do algoritmo bcrypt (acima disso, o
  restante da senha seria ignorado silenciosamente).

## Consentimento (LGPD) integrado ao cadastro

O cadastro exige o campo `terms_accepted`, validado antes de qualquer outra
regra: sem aceite explícito do Termo de Uso e da Política de Privacidade, a
conta não é criada. O aceite é registrado com data/hora (`terms_accepted_at`)
e a versão vigente dos documentos (`terms_version`), e gera um evento de
auditoria (`lgpd.consent_accepted`) — dando à equipe um registro verificável
do consentimento, conforme exigido pela LGPD (Art. 8º).

## Auditoria do login

Cadastro, login bem-sucedido e login com falha geram eventos na tabela
`audit_logs` (`auth.registered`, `auth.login`, `auth.login_failed`), com o IP
de origem. A senha digitada — certa ou errada — nunca é registrada.

## Testes

`backend/tests/integration/test_auth.py` cobre o fluxo de cadastro, login (sucesso e
falha) e a rota `/auth/me`; `backend/tests/integration/test_interview.py` cobre, entre
outras coisas, a autorização entre usuários diferentes (403 ao tentar
responder a sessão de outra pessoa).

Para rodar:

```bash
cd backend
pytest -v
```

## Limitações conhecidas (trabalhos futuros)

- O token fica no `localStorage`, que pode ser lido por um script malicioso
  em caso de falha de XSS. Uma alternativa mais segura é um cookie
  `HttpOnly`.
- Não há limite de tentativas de login (*rate limiting*) nem bloqueio
  temporário após várias falhas consecutivas.
- Não há renovação de token (*refresh token*): após 24h o usuário precisa
  fazer login de novo.
- Não há recuperação de senha ("esqueci minha senha") implementada ainda.