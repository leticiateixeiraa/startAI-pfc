# Evidências de desenvolvimento

Registro visual do que foi desenvolvido no StartAI, organizado pelas 10
funcionalidades da Ficha de Caracterização (veja a tabela no
[README principal](../../README.md#funcionalidades)).

**Como as evidências foram geradas (14/11/2026):**

- Prints tirados do sistema rodando localmente (front-end em
  `localhost:5173`, API em `localhost:8000`, PostgreSQL local), com dados
  reais do banco de desenvolvimento. Nenhuma tela foi montada ou editada.
- Telas de aluno: conta de teste `TESTE_DEV_LEO`. Telas de administração:
  conta com papel `admin`.
- Por privacidade, as listas do painel administrativo foram filtradas para
  mostrar só contas de teste (`@example.com`).
- Resolução 1366×768. Páginas longas aparecem em recortes do tamanho da tela.

## Índice

| # | Funcionalidade | Situação | Evidências |
|---|---|---|---|
| 1 | Cadastro, login e autenticação | ✅ | [Prints 01 a 03](#1-cadastro-login-e-autenticação) |
| 2 | Perguntas geradas por IA | ✅ | [Prints 08 e 09](#2-seleção-da-vaga-e-perguntas-geradas-por-ia) |
| 3 | Entrevistador dinâmico | ✅ | [Print 10b](#3-entrevistador-dinâmico) |
| 4 | Captura de áudio e transcrição | ✅ | [Print 09](#4-captura-de-áudio-e-transcrição) |
| 5 | Analisador de oratória | ⏳ | [Em andamento](#5-analisador-de-oratória) |
| 6 | Histórico e painel de evolução | ✅ | [Prints 06 e 11](#6-histórico-de-entrevistas) |
| 7 | Recomendação de vagas | ✅ | [Print pendente](#7-recomendação-de-vagas) |
| 8 | Trilhas de estudo | ✅ | [Prints 10c e 11](#8-trilhas-de-estudo-personalizadas) |
| 9 | Avaliação das respostas por IA | ✅ | [Prints 10a e 10b](#9-avaliação-das-respostas-por-ia) |
| 10 | Painel administrativo | ✅ | [Prints 15 a 17](#10-painel-administrativo) |
| — | Questionário de área (onboarding) | ✅ | [Print 07](#questionário-de-área-onboarding) |
| — | Análise de currículo | ✅ | [Print 11](#análise-de-currículo) |
| — | LGPD | ✅ | [Prints 04, 05 e 14](#lgpd-e-privacidade) |
| — | Auditoria e logs | ✅ | [Prints 13 e 17](#auditoria-e-logs) |
| — | API REST documentada | ✅ | [Print 18](#api-rest) |
| — | Testes automatizados | ✅ | [Print 19](#testes-automatizados-e-qualidade) |

---

## 1. Cadastro, login e autenticação

Login com e-mail e senha, cadastro com aceite dos termos e recuperação de
senha por e-mail. A API emite um token JWT e guarda as senhas com bcrypt.
Detalhes em [seguranca-login.md](../seguranca-login.md) e
[recuperacao-senha.md](../recuperacao-senha.md).

**01. Login**
![Tela de login](img/01-login.png)

**02. Cadastro**
![Tela de cadastro](img/02-cadastro.png)

**03. Esqueci minha senha**
![Tela de recuperação de senha](img/03-esqueci-senha.png)

## 2. Seleção da vaga e perguntas geradas por IA

O aluno informa o cargo, o nível, o tipo de entrevista e a descrição da vaga.
O Gemini gera 5 perguntas específicas para essa vaga.

**08. Configuração da entrevista**
![Configuração da entrevista](img/08-entrevista-configuracao.png)

**09. Pergunta gerada pela IA durante a entrevista**
![Pergunta da entrevista](img/09-entrevista-pergunta.png)

## 3. Entrevistador dinâmico

Depois de cada resposta, a próxima pergunta é adaptada ao que o aluno disse.
No print, a pergunta 2 começa com "Você comentou que valida as
inconsistências com a área responsável…", retomando a resposta da pergunta 1.

**10b. Perguntas adaptadas às respostas anteriores**
![Feedback por resposta, com pergunta adaptada](img/10b-feedback.png)

## 4. Captura de áudio e transcrição

O botão **Responder por voz** (print 09) grava o áudio no navegador. O
Gemini transcreve a gravação, e o texto entra na caixa de resposta para o
aluno revisar antes de enviar. O áudio é descartado logo após a transcrição.

## 5. Analisador de oratória

⏳ Em andamento. A transcrição já guarda o texto literal e a duração de cada
resposta, que são a base das métricas (vícios de linguagem, repetições,
palavras por minuto).

## 6. Histórico de entrevistas

A tela inicial lista as entrevistas do aluno, com situação, nível, número de
respostas e nota da IA, e permite continuar uma entrevista em andamento.

**06. Tela inicial com o histórico**
![Tela inicial com histórico de entrevistas](img/06-home.png)

## 7. Recomendação de vagas

Busca vagas reais pela API da Jooble, usando o cargo treinado e o desempenho
nas entrevistas. Mais detalhes em
[integracao-api-externa.md](../integracao-api-externa.md).

> **Print pendente (12-vagas):** no ambiente em que os prints foram tirados,
> a variável `JOOBLE_API_KEY` não estava configurada. Configure a chave e
> tire o print da página **Vagas**.

## 8. Trilhas de estudo personalizadas

A partir dos pontos fracos da avaliação, a IA monta uma trilha com etapas,
dicas, exercícios e links para estudo. O aluno marca as etapas concluídas.

**10c. Trilha gerada a partir da entrevista**
![Trilha de estudos](img/10c-trilha.png)

## 9. Avaliação das respostas por IA

Ao final da entrevista, cada resposta recebe uma nota de 0 a 10 em
relevância, coerência, completude e adequação, com pontos fortes, o que
melhorar e um exemplo de resposta.

**10a. Resumo da avaliação**
![Resumo da avaliação](img/10a-entrevista-resultado.png)

**10b. Feedback de cada resposta**
![Feedback de cada resposta](img/10b-feedback.png)

## 10. Painel administrativo

Disponível só para contas com papel `admin`, verificado pelo back-end em
toda requisição. O administrador não vê o conteúdo das respostas
(minimização de dados, LGPD).

**15. Painel com métricas da plataforma**
![Painel administrativo](img/15-admin-painel.png)

**16. Gestão de usuários (desativar e excluir contas)**
![Lista de usuários](img/16-admin-usuarios.png)

**17. Auditoria geral, com filtros por usuário, ação e período**
![Auditoria geral](img/17-admin-auditoria.png)

---

## Questionário de área (onboarding)

Oito perguntas que indicam a área da tecnologia com mais afinidade e sugerem
cargos e por onde começar a estudar.

**07. Resultado do questionário**
![Resultado do onboarding](img/07-onboarding.png)

## Análise de currículo

Na página **Meu perfil**, o aluno envia o currículo (PDF ou DOCX) e a IA
devolve uma nota, os pontos fortes e o que melhorar. O arquivo não fica
guardado; só o resultado é salvo.

**11. Meu perfil: área de interesse, envio de currículo e trilhas**
![Meu perfil](img/11-perfil.png)

## LGPD e privacidade

Termo de Uso e Política de Privacidade públicos, aceite registrado no
cadastro e exclusão definitiva da conta pelo próprio usuário.

**04. Termo de Uso**
![Termo de Uso](img/04-termos-de-uso.png)

**05. Política de Privacidade**
![Política de Privacidade](img/05-politica-privacidade.png)

**14. Minha conta: dados do usuário e exclusão da conta**
![Minha conta](img/14-minha-conta-lgpd.png)

## Auditoria e logs

Os eventos relevantes (login, entrevistas, avaliações, trilhas, LGPD) ficam
registrados na tabela `audit_logs`, sem senhas nem conteúdo das respostas.
O aluno vê só os próprios eventos; o admin vê os de todos (print 17).

**13. Auditoria da conta do aluno**
![Auditoria do usuário](img/13-auditoria-usuario.png)

## API REST

Documentação interativa da API gerada pelo FastAPI (Swagger), em
`http://localhost:8000/docs`.

**18. Swagger da API**
![Swagger](img/18-api-swagger.png)

## Testes automatizados e qualidade

| Verificação | Resultado |
|---|---|
| Testes do back-end (`pytest`) | **364 testes passando** (unitários e de integração) |
| Cobertura do back-end (`pytest --cov=app`) | **96%** (meta do cronograma: 50%) |
| Lint do front-end (`npm run lint`) | 0 erros, 53 avisos |
| Build do front-end (`npm run build`) | Concluído com checagem de tipos |

Os testes usam SQLite em memória e o Gemini e o SMTP simulados, então não
dependem de internet nem consomem a cota da API. O relatório completo por
arquivo está em [testes/cobertura-backend.txt](testes/cobertura-backend.txt).

**19. Relatório de cobertura dos testes do back-end**
![Cobertura dos testes](img/19-testes-cobertura.png)

Para reproduzir, na pasta `backend/`:

```bash
pip install pytest-cov
pytest --cov=app --cov-report=term
```
