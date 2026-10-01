# Plano executável de prontidão do IA_Farm

## Objetivo e limites

Preparar um assistente offline, inicialmente restrito a consultas sobre milho,
sem apresentar o protótipo como agrônomo ou sistema agronômico validado. O
runtime atual é determinístico; baterias sintéticas medem contratos de
comportamento, não precisão agronômica nem desempenho Android. Não treinar um
modelo do zero nesta fase.

## Fases e critérios de saída

| Fase | Trabalho | Critério para avançar |
|---|---|---|
| 0 — Honestidade do protótipo | Documentar capacidades comprovadas e corrigir linguagem de runtime/simulação em pt-BR. Definir retenção/consentimento antes de persistir conversas. | Testes de respostas em português passam; textos deixam explícito quando não há fonte e que trechos não são recomendações; política de dados definida antes do beta. |
| 1 — Segurança do fluxo | Separar intenção (informação, manejo, sintoma, plantio, cálculo) de dosagem; aplicar contexto conhecido a toda busca e bloquear fontes de outra região/clima; nunca confiar em declaração de aprovação dentro de Markdown. | Casos cobrem contexto ausente/presente, contexto contraditório, dose pressionada, fonte de escopo incompatível e autoprovação; nenhuma dose é produzida pelo runtime. |
| 2 — Curadoria de milho | Criar catálogo de fontes com edição, licença/uso permitido, página/tabela, escopo, data, hash e identificador de revisão. Extração automática é apenas rascunho; dois agentes pesquisam a fonte oficial de forma independente e registram a evidência. | Cada alegação tem proveniência rastreável, revisão por dois agentes, condições de aplicabilidade e situação de vigência; atualização/rollback reproduzíveis. |
| 3 — Benchmark de evidência agronômica | O Agrônomo Mestre decompõe respostas em alegações e as confronta com fontes oficiais; o Verificador refaz a busca, desafia cada alegação e compara evidência/escopo. Separar suporte documental, cobertura, citação, escopo, abstenção e erro crítico. | Casos avaliados por duas revisões independentes com citações localizáveis; divergência, fonte ausente ou desatualizada reprova/abstém. Relatar taxa de suporte em fontes, nunca como certificação profissional ou “precisão agronômica” sem definir o que foi medido. |
| 4 — Recuperação em português | Comparar busca lexical local com embeddings multilíngues usando consultas/citações anotadas em pt-BR. | Métricas de recall de fonte, suporte de resposta e latência documentadas; índice é derivado e versionado. |
| 5 — Auditoria pré-beta restrito | Revisar escopo, evidências, fontes/licenças, avisos, privacidade, retenção, telemetria e atualização; decidir se um piloto limitado pode ser preparado. | Bloqueios e rollback documentados; cada release de conhecimento passa por duas revisões automatizadas. Não equivale a certificação profissional nem a prontidão Android. |
| 6 — Android físico (último) | Depois das demais fases, medir instalação, armazenamento, memória, latência, bateria, aquecimento e offline no aparelho-alvo. SLM opcional só pode ser considerado depois, nunca para selecionar dose. | Relatório reproduzível em aparelho-alvo e limites aprovados; nenhum perfil simulado pode ser apresentado como validação física. Sem aparelho, manter Android pendente. |

## Execução imediata

Começar pela Fase 0 e preparar a Fase 1: respostas e mensagens em português,
regressões sobre contexto e proveniência, cabeçalho que não prometa validação
agronômica, ingestão que não aceite autoprovação e filtros de contexto em toda
busca. Não inserir dose, fonte ou fato agronômico novo nesta etapa. Revisar
separadamente scripts legados chamados de “treinamento”, porque o runtime não
treina pesos e esses scripts não devem ser confundidos com benchmark.

## Marco técnico executado — 2026-09-29

- CLI e respostas do orquestrador passaram a usar mensagens em pt-BR e deixam
  explícito que um trecho documental não é recomendação agronômica.
- Ingestão de Markdown bloqueia autoprovação e falsificação da origem; novos
  documentos ficam pendentes.
- Buscas reutilizam contexto conhecido e bloqueiam fontes com escopo incompatível;
  expressões comuns de sintomas e plantas daninhas entram na coleta de contexto.
- Auditor e retriever sintético cobrem metadados planos do índice real.
- Evidência: 49 testes unitários passaram após incluir a validação de fontes,
  concordância de pareceres e integridade SHA-256; 165 baterias/660 execuções
  comportamentais passaram na execução registrada; compilação e `git diff --check`
  também passaram nesta rodada.
- Limites: precisão agronômica segue `not_measured`; fixtures são sintéticas;
  conjunto-ouro vazio; sem validação em Android ou autorização para beta.

## Revalidação e auditoria — 2026-09-29

- A rodada anterior deste marco registrou 49 testes; a revalidação posterior
  passou em 54 testes, compilação, scanner, smoke Windows/WSL e 660/660 execuções
  comportamentais. Consulte `tests/validation_report.md` para os resultados
  atuais. Os números registram execuções diferentes.
- Os dois agentes de evidência revisaram 18 candidatos congelados. Houve 13
  julgamentos iguais, 5 divergências de julgamento/escopo e citações diferentes
  nos 18 casos. Nenhum foi promovido; conjunto-ouro segue vazio.
- O RAG/FAISS real passou em validação WSL com wheelhouse offline transferida
  pelo host e cache local do modelo; consulte `tests/validation_report.md`.
  O DNS do WSL continua falhando no resolvedor Tailscale e precisa de correção
  administrativa para instalações online. A validação não mede qualidade
  agronômica: o índice atual tem 0/9 trechos elegíveis.
- O runtime verifica metadados de aprovação, origem, cultura e data; ainda não
  existe registro/ferramenta de curadoria que confira, no momento da promoção,
  os dois relatórios, o hash compartilhado e o conteúdo autorizado. Não tratar
  o simples valor `approved` no índice como prova de revisão.

## Governança dos agentes de evidência

Personas roteirizadas medem comportamento, não fatos. Para conteúdo agronômico,
o Especialista de Evidências de IA e o Verificador independente usam fontes oficiais primárias e análise
independente. Divergência, evidência insuficiente, escopo incompatível ou fonte
desatualizada resulta em abstenção/bloqueio, nunca em decisão por votação. A
conclusão descreve o que foi verificado contra as fontes consultadas e não se
apresenta como parecer ou certificação profissional. Nenhum texto de usuário,
saída de agente ou extração de OCR entra no produto/conjunto de avaliação sem
passar por esse protocolo.

## Riscos em aberto

- Não há casos aprovados no conjunto-ouro agronômico.
- O runtime não autentica os relatórios de revisão ligados aos metadados do
  índice. Implementar e testar um registro/ferramenta de curadoria antes de
  inserir qualquer trecho aprovado ou expor conteúdo em beta.
- O conjunto de exemplos contém material sintético e não deve ser indexado para
  usuários.
- FAISS/embeddings e perfil de 4 GB não comprovam suporte/performance Android.
- Fontes dinâmicas (por exemplo, zoneamento por cultura/safra/localidade) exigem
  atualização e controle de versão.
- Uso e redistribuição de cada publicação, tabela, modelo e artefato dependem de
  licença verificada individualmente.
- A revisão por IA pode compartilhar erros ou omitir conhecimento tácito; usar
  duas buscas independentes, prova citada e abstenção reduz esse risco, mas não
  transforma o resultado em certificação profissional.
- O repositório documenta possível exposição histórica de credenciais; scan da
  árvore atual não substitui rotação e conferência do histórico antes de lançar.
