import { createFileRoute, Link } from "@tanstack/react-router";

export const Route = createFileRoute("/privacidade")({
  head: () => ({
    meta: [{ title: "Política de Privacidade — StartAI" }],
  }),
  component: PrivacyPage,
});

const dataTable = [
  {
    category: "Dados de cadastro",
    data: "Nome, e-mail, senha (armazenada como hash bcrypt)",
    origin: "Fornecidos pelo usuário no cadastro",
  },
  {
    category: "Dados de uso da entrevista",
    data: "Cargo/vaga, tipo de apresentação, descrição da vaga, perguntas e respostas em texto",
    origin: "Gerados durante o uso do Serviço",
  },
  {
    category: "Dados de áudio",
    data: "Gravações de voz e sua transcrição textual",
    origin: "Fornecidos pelo usuário durante a simulação",
  },
  {
    category: "Métricas de oratória",
    data: "Duração da fala, palavras por minuto, repetições, vícios de linguagem",
    origin: "Calculados a partir do áudio/transcrição",
  },
  {
    category: "Dados técnicos e de auditoria",
    data: "Endereço IP, data/hora, tipo de ação (login, cadastro, início de entrevista)",
    origin: "Coletados automaticamente pelo sistema de log/auditoria",
  },
];

const thirdParties = [
  {
    name: "Google (Gemini API)",
    shared: "Cargo/vaga, descrição da vaga, perguntas e respostas em texto",
    purpose: "Geração e adaptação de perguntas de entrevista por IA",
  },
  {
    name: "Serviço de Speech-to-Text",
    shared: "Áudio da resposta do usuário",
    purpose: "Transcrição da fala em texto",
  },
  {
    name: "Provedor de hospedagem",
    shared: "Todos os dados trafegados pela aplicação",
    purpose: "Hospedagem da infraestrutura (front-end e back-end)",
  },
];

function PrivacyPage() {
  return (
    <main className="flex-1 bg-background px-4 py-12">
      <article className="mx-auto max-w-2xl rounded-2xl border border-border bg-card p-7 shadow-sm sm:p-9">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Política de Privacidade</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Última atualização: [25/09/2025] — Versão 1.0
        </p>
        <p className="mt-4 text-sm leading-relaxed text-card-foreground">
          Esta Política descreve como o StartAI coleta, usa, armazena e protege os dados
          pessoais dos usuários, em conformidade com a Lei Geral de Proteção de Dados Pessoais
          (Lei nº 13.709/2018 — LGPD).
        </p>

        <div className="mt-8 flex flex-col gap-6 text-sm leading-relaxed text-card-foreground">
          <section>
            <h2 className="text-base font-semibold text-foreground">1. Controlador dos dados</h2>
            <p className="mt-2">
              O tratamento é de responsabilidade da equipe desenvolvedora do StartAI, no contexto
              do TCC de Engenharia de Software da UMC. Contato: [e-mail de contato do projeto].
            </p>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">2. Dados pessoais coletados</h2>
            <div className="mt-2 overflow-x-auto">
              <table className="w-full border-collapse text-left text-xs">
                <thead>
                  <tr className="border-b border-border">
                    <th className="py-2 pr-3 font-semibold text-foreground">Categoria</th>
                    <th className="py-2 pr-3 font-semibold text-foreground">Dados</th>
                    <th className="py-2 font-semibold text-foreground">Origem</th>
                  </tr>
                </thead>
                <tbody>
                  {dataTable.map((row) => (
                    <tr key={row.category} className="border-b border-border/60 align-top">
                      <td className="py-2 pr-3 font-medium">{row.category}</td>
                      <td className="py-2 pr-3 text-muted-foreground">{row.data}</td>
                      <td className="py-2 text-muted-foreground">{row.origin}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-2">
              Não coletamos dados sensíveis (Art. 5º, II, LGPD) de forma intencional. Evite
              incluir dados sensíveis (saúde, origem racial, convicção religiosa etc.) em suas
              respostas de entrevista.
            </p>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">3. Finalidade do tratamento</h2>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              <li>criar e autenticar a conta do usuário;</li>
              <li>gerar perguntas de entrevista personalizadas via Inteligência Artificial;</li>
              <li>transcrever e analisar a fala, fornecendo feedback de oratória;</li>
              <li>manter histórico de sessões para acompanhamento de evolução;</li>
              <li>registrar logs de auditoria, para segurança e rastreabilidade de acesso.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">4. Base legal (Art. 7º, LGPD)</h2>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              <li><strong>Execução de contrato:</strong> processamento necessário às funcionalidades solicitadas pelo usuário.</li>
              <li><strong>Consentimento:</strong> para o tratamento de áudio e conteúdo das respostas, coletado no aceite deste documento e do Termo de Uso.</li>
              <li><strong>Legítimo interesse:</strong> para logs de auditoria e segurança do sistema.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">5. Compartilhamento com terceiros</h2>
            <div className="mt-2 overflow-x-auto">
              <table className="w-full border-collapse text-left text-xs">
                <thead>
                  <tr className="border-b border-border">
                    <th className="py-2 pr-3 font-semibold text-foreground">Terceiro</th>
                    <th className="py-2 pr-3 font-semibold text-foreground">Dado compartilhado</th>
                    <th className="py-2 font-semibold text-foreground">Finalidade</th>
                  </tr>
                </thead>
                <tbody>
                  {thirdParties.map((row) => (
                    <tr key={row.name} className="border-b border-border/60 align-top">
                      <td className="py-2 pr-3 font-medium">{row.name}</td>
                      <td className="py-2 pr-3 text-muted-foreground">{row.shared}</td>
                      <td className="py-2 text-muted-foreground">{row.purpose}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-2">
              Esses terceiros processam os dados sob suas próprias políticas e não são
              autorizados a utilizá-los para finalidades diversas das aqui descritas. Não
              vendemos nem compartilhamos dados pessoais para fins de marketing de terceiros.
            </p>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">6. Armazenamento e retenção</h2>
            <p className="mt-2">
              Dados de cadastro e histórico são mantidos enquanto a conta estiver ativa. Logs de
              auditoria são mantidos pelo prazo necessário à segurança. Após a exclusão da conta,
              os dados pessoais são removidos ou anonimizados em prazo razoável, ressalvadas
              hipóteses de guarda obrigatória por lei.
            </p>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">7. Seus direitos (Art. 18, LGPD)</h2>
            <p className="mt-2">Você pode, mediante solicitação ao nosso contato, exercer os direitos de:</p>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              <li>confirmação e acesso aos dados tratados;</li>
              <li>correção de dados incompletos, inexatos ou desatualizados;</li>
              <li>anonimização, bloqueio ou eliminação de dados desnecessários;</li>
              <li>portabilidade a outro fornecedor de serviço;</li>
              <li>eliminação dos dados tratados com base no consentimento;</li>
              <li>revogação do consentimento a qualquer momento;</li>
              <li>informação sobre com quem os dados foram compartilhados.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">8. Segurança da informação</h2>
            <p className="mt-2">
              Senhas são armazenadas exclusivamente como hash (bcrypt), a autenticação usa token
              JWT com expiração, a comunicação é criptografada (HTTPS/TLS) e mantemos logs de
              auditoria para rastreabilidade de acessos e ações sensíveis. Em caso de incidente
              de segurança relevante, notificaremos os usuários afetados e a ANPD, conforme a
              LGPD.
            </p>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">9. Cookies e armazenamento local</h2>
            <p className="mt-2">
              Utilizamos <code>localStorage</code> no navegador para armazenar o token de acesso
              (JWT) necessário para manter você autenticado. Esse dado é local ao seu dispositivo
              e é removido ao efetuar logout ou limpar os dados do navegador.
            </p>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">10. Menores de idade</h2>
            <p className="mt-2">
              O Serviço não é direcionado a menores de 18 anos. Caso identifiquemos cadastro de
              menor sem consentimento de responsável legal, a conta poderá ser suspensa e os
              dados eliminados.
            </p>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">11. Alterações nesta Política</h2>
            <p className="mt-2">
              Esta Política pode ser atualizada periodicamente. A versão vigente estará sempre
              disponível na Plataforma, com indicação da data da última atualização.
            </p>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">12. Contato / Encarregado de Dados</h2>
            <p className="mt-2">E-mail: [gb.santanna2@gmail.com]</p>
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
