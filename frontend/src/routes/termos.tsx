import { createFileRoute, Link } from "@tanstack/react-router";

export const Route = createFileRoute("/termos")({
  head: () => ({
    meta: [{ title: "Termo de Uso — StartAI" }],
  }),
  component: TermsPage,
});

function TermsPage() {
  return (
    <main className="flex-1 bg-background px-4 py-12">
      <article className="mx-auto max-w-2xl rounded-2xl border border-border bg-card p-7 shadow-sm sm:p-9">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Termo de Uso</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Última atualização: 29/10/2026 — Versão 1.0
        </p>

        <div className="mt-8 flex flex-col gap-6 text-sm leading-relaxed text-card-foreground">
          <section>
            <h2 className="text-base font-semibold text-foreground">1. Aceitação dos termos</h2>
            <p className="mt-2">
              Ao criar uma conta ou utilizar a plataforma StartAI ("Plataforma", "Serviço"), você
              concorda integralmente com este Termo de Uso e com a{" "}
              <Link to="/privacidade" className="text-primary hover:underline">
                Política de Privacidade
              </Link>
              . Caso não concorde com qualquer disposição aqui prevista, não utilize o Serviço.
            </p>
            <p className="mt-2">
              O StartAI é um projeto acadêmico desenvolvido no âmbito do Trabalho de Conclusão de
              Curso (PFC) de Engenharia de Software da Universidade de Mogi das Cruzes (UMC), com
              fins educacionais e de demonstração técnica.
            </p>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">2. Descrição do serviço</h2>
            <p className="mt-2">O StartAI é uma plataforma web de simulação de entrevistas e apresentações que:</p>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              <li>gera perguntas de entrevista por meio de Inteligência Artificial, adaptadas à vaga ou ao tipo de apresentação escolhido;</li>
              <li>captura e transcreve respostas faladas (Speech-to-Text);</li>
              <li>analisa a oratória do usuário (vícios de linguagem, repetições, duração, palavras por minuto);</li>
              <li>avalia o conteúdo das respostas quanto à relevância, coerência e completude;</li>
              <li>mantém um histórico de sessões para acompanhamento da evolução do usuário.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">3. Cadastro e conta do usuário</h2>
            <p className="mt-2">
              O usuário é responsável por manter a confidencialidade de suas credenciais e por
              todas as atividades realizadas em sua conta, e declara que as informações
              fornecidas no cadastro são verdadeiras, completas e atualizadas. É vedado o
              cadastro por menores de 18 anos sem consentimento e supervisão de responsável legal.
            </p>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">4. Uso aceitável</h2>
            <p className="mt-2">Ao utilizar o StartAI, o usuário compromete-se a não:</p>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              <li>utilizar a Plataforma para fins ilícitos, ofensivos, discriminatórios ou que violem direitos de terceiros;</li>
              <li>tentar acessar dados de outros usuários, código-fonte ou infraestrutura de forma não autorizada;</li>
              <li>utilizar meios automatizados (bots, scraping) para extrair dados ou sobrecarregar o Serviço;</li>
              <li>enviar, via áudio ou texto, conteúdo ilegal, discurso de ódio ou material protegido por direitos autorais de terceiros.</li>
            </ul>
            <p className="mt-2">
              O descumprimento destas regras pode resultar em suspensão ou encerramento da conta.
            </p>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">
              5. Inteligência Artificial e limitação de responsabilidade
            </h2>
            <p className="mt-2">
              As perguntas de entrevista e a avaliação de conteúdo são geradas por modelos de IA
              de terceiros (atualmente, Google Gemini) e a transcrição de áudio por serviços de
              reconhecimento de fala. Essas saídas são automáticas e podem conter imprecisões.
            </p>
            <p className="mt-2">
              O feedback fornecido tem finalidade <strong>exclusivamente educacional e de
              treinamento</strong>, não constituindo aconselhamento profissional, psicológico, de
              carreira ou garantia de aprovação em processos seletivos reais. O StartAI não se
              responsabiliza por decisões tomadas pelo usuário com base nas análises geradas.
            </p>
            <p className="mt-2">
              O Serviço é fornecido "como está", sem garantias de disponibilidade contínua ou
              ausência de erros, tratando-se de projeto acadêmico em desenvolvimento.
            </p>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">6. Propriedade intelectual</h2>
            <p className="mt-2">
              O código-fonte, design, marca e demais elementos da Plataforma são de propriedade
              da equipe desenvolvedora do StartAI, salvo bibliotecas e serviços de terceiros
              utilizados sob suas respectivas licenças. O conteúdo gerado pelo usuário (respostas,
              áudios) permanece de sua titularidade, sendo licenciado ao StartAI apenas para os
              fins de processamento necessários à prestação do Serviço.
            </p>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">7. Suspensão e encerramento</h2>
            <p className="mt-2">
              O usuário pode solicitar a exclusão de sua conta e de seus dados a qualquer momento.
              O StartAI pode suspender ou encerrar contas que violem este Termo, mediante
              notificação prévia sempre que razoavelmente possível.
            </p>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">8. Alterações neste Termo</h2>
            <p className="mt-2">
              Este Termo pode ser atualizado periodicamente. Alterações relevantes serão
              comunicadas por e-mail ou aviso na Plataforma, com indicação da nova data de
              vigência.
            </p>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">9. Legislação aplicável</h2>
            <p className="mt-2">
              Este Termo é regido pelas leis da República Federativa do Brasil, incluindo a Lei
              Geral de Proteção de Dados (Lei nº 13.709/2018) e o Marco Civil da Internet (Lei
              nº 12.965/2014). Fica eleito o foro da comarca de [São Paulo/SP] para dirimir eventuais
              controvérsias.
            </p>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">10. Contato</h2>
            <p className="mt-2">
              Dúvidas sobre este Termo podem ser enviadas para: [gb.santanna2@gmail.com]
            </p>
          </section>
        </div>

        <div className="mt-8">
          <Link to="/register" className="text-sm font-medium text-primary hover:underline">
            ← Voltar ao cadastro
          </Link>
        </div>
      </article>
    </main>
  );
}
