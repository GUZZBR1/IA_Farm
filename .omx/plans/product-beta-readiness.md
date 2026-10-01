# Plano de execução — prontidão para beta do IA_Farm

## Objetivo e limites

Preparar e auditar o protótipo para decidir com evidência se está apto a um beta restrito. Não exigir aprovação de agrônomo humano nesta fase; agentes de IA podem revisar fontes oficiais, mas devem ser identificados como sistemas automatizados e podem produzir evidência incompleta. Não prometer precisão agronômica nem uso seguro no campo com base apenas nessa revisão. A validação em celular fica para a última fase.

## Agentes planejados

| Agente | Momento | Escopo e saída | Limite |
|---|---|---|---|
| Planner (padrão) | Planejamento | Revisar a ordem de fases, gates, agentes e riscos deste plano. | Somente leitura; nenhum arquivo alterado. |
| Especialista de evidências de milho (IA) | Curadoria | Revisar cada caso candidato contra fontes oficiais primárias; devolver alegações, evidências, localizadores, escopo, atualidade, ressalvas e veredito em JSON. | Não é agrônomo humano/licenciado; não se autoprova, não inventa fatos e não promove sozinho casos sem fonte. |
| Verificador independente de evidências (IA) | Após o especialista | Pesquisar independentemente e tentar refutar o parecer, usando os mesmos IDs de casos e evidências rastreáveis. | Sem ler o parecer do especialista antes de registrar a análise inicial; divergências permanecem bloqueadas. |
| Executor técnico | Correções | Corrigir marcadores do smoke test, suporte de plataforma/documentação e inconsistências de status, preservando as mudanças locais existentes. | Alterações em escopo delimitado, sem mexer em dados agronômicos aprovados. |
| Test engineer | Verificação técnica | Revisar testes de regressão e sugerir/implementar cobertura para o smoke e o contrato dos relatórios. | Não altera conteúdo técnico de agronomia. |
| Auditor final (IA) | Encerramento | Revisar evidências, documentação, diff e resultados das baterias; listar o que bloqueia ou limita beta. | Leitura crítica independente; não converter concordância de IA em validação profissional. |

Não usar o papel genérico `planner` até resolver a incompatibilidade de modelo observada nesta sessão; consultar o agente padrão disponível. Durante o planejamento, um agente padrão foi iniciado, mas ainda não retornou conclusão no momento em que este plano foi escrito. Nenhuma implementação depende da resposta pendente.

## Fases e gates

### 0 — Congelar o escopo e o estado atual

- Preservar as alterações locais preexistentes.
- Registrar resultados de baseline: 49 testes, 165 baterias/660 execuções, compilação e scanner aprovados; smoke atual falha no WSL por marcadores desatualizados; conjunto-ouro vazio; dependências vetoriais ausentes no WSL.
- Não executar rewrite de histórico nem revogar credenciais sem acesso/autoridade do provedor; preparar checklist e evidência para o mantenedor.

**Gate:** estado e limitações atuais documentados sem alegar Android ou precisão agronômica.

### 1 — Política de beta e transparência

- Atualizar `AGENTE.md` e os guias relevantes para declarar: não haverá agrônomo humano validador obrigatório por enquanto; revisões por agentes de IA são evidência assistiva, não certificação.
- Registrar explicitamente que validação física em celular é a última etapa; o protótipo continua restrito enquanto não for concluída.
- Corrigir divergências entre `PROJECT_STATUS.md`, `ROADMAP.md`, `README.md`, `docs/product_readiness_plan.md`, `docs/test_environment.md` e `tests/validation_report.md`.

**Gate:** todos os documentos apresentam as mesmas capacidades e limitações; nenhum apresenta 49 testes/660 cenários como validação agronômica.

### 2 — Correções técnicas imediatas

- Corrigir `tests/run_low_mid_smoke.py` para aceitar mensagens reais em português e testar o comportamento atual da CLI no WSL; manter claro que `resource`/afinidade são específicos a Linux/WSL.
- Fazer o runner detectar Windows e encerrar como não suportado de forma explícita, ou evitar que uma limitação de plataforma pareça falha funcional. A escolha final deve seguir as convenções do projeto.
- Verificar estado do índice e dependências; não ingerir dataset sintético ou material pendente como conteúdo do produto.
- Corrigir chamadas documentadas para o benchmark vazio, que hoje terminam com erro por arquivo de parecer ausente, para retornar `not_evaluable` com saída reproduzível e clara.

**Gate:** smoke WSL aprovado; testes unitários e compilação aprovados; caminhos não suportados reportados claramente; nenhuma dependência nova sem necessidade comprovada.

### 3 — Criar e executar o especialista de evidências

- Criar artefato de agente dedicado (prompt/instruções e schema) em `docs/` para perguntas de milho no Brasil, com foco em fontes oficiais, IDs de alegação, escopo, safra, datas, localizadores e abstenção.
- Ajustar o pacote candidato atual de 18 casos para não sugerir que hipótese ou URL já equivalem a aprovação.
- Executar o especialista de IA nos candidatos usando fontes primárias atuais; pesquisar cada fonte no documento original. Registrar JSON e hash do relatório de casos.
- Executar um verificador IA independente contra os mesmos casos; registrar seu próprio JSON e comparar.
- Sem agrônomo humano por enquanto. Um caso só entra no conjunto de avaliação baseado em fontes se ambos os pareceres satisfizerem a política automatizada de evidência; divergências, fontes antigas sem confirmação, licenças não esclarecidas ou falta de localizador ficam pendentes/bloqueadas.
- Não criar ou estimar dose de insumo; qualquer recomendação operacional de defensivo ou dose permanece fora do escopo sem registro regulatório, bula e contexto completos.

**Gate:** relatórios são válidos no schema, ligados ao mesmo hash, com evidências primárias e localizadores; casos sem evidência suficiente permanecem fora do ouro. Registrar quantidade promovida e não promovida, sem chamar isso de precisão global.

### 4 — Benchmark e baterias do ambiente simulado

- Executar testes unitários, suíte completa de 165 baterias e smoke depois das mudanças.
- Expandir baterias somente onde a auditoria encontrar lacuna reproduzível: mensagens em português/voz, ausência e contradição de contexto, proveniência, fonte desatualizada, abstenção e pressão por dose; manter fixtures claramente sintéticas.
- Executar o benchmark agronômico somente se houver casos elegíveis no conjunto e pareceres presentes; caso contrário exigir saída `not_evaluable` em vez de erro.
- Auditar relatórios legados sob `test-results/`; artefatos não rastreados são dados locais do usuário, não apagar nem sobrescrever. Criar novos nomes/versionamento para novas execuções.

**Gate:** todas as baterias ativas passam; falhas são corrigidas e repetidas; relatório deixa clara a diferença entre comportamento e sustentação agronômica.

### 5 — Auditoria de prontidão para beta restrito

- Auditor IA revisa código, docs, testes, segurança, proveniência, fluxo de dados, licença, UX de abstenção, dependências e resultados do benchmark.
- Classificar cada pendência como bloqueadora, necessária antes do beta ou posterior; registrar dono/evidência de fechamento.
- Verificar estado/histórico de credenciais e documentar a ação requerida ao mantenedor; manter segredo histórico como bloqueio até rotação/verificação com o provedor.
- Emitir decisão recomendada de beta restrito; não declarar produção ou precisão se evidências não sustentarem.

**Gate:** checklist de beta rastreável e nenhum bloqueador oculto; não há aprovação automática por mero sucesso de testes.

### 6 — Validação em celular (última fase)

- Só iniciar após gates anteriores; conseguir aparelho Android alvo; validar empacotamento/offline e medir memória, latência, armazenamento, bateria, temperatura e recuperação após pressão.
- Documentar modelo do aparelho, versão do SO, build, metodologia e limites aceitos.

**Gate:** relatório físico reproduzível. Se aparelho/dispositivo não estiver disponível, registrar pendência; não simular como validação.

## Critérios de aceitação

- `AGENTE.md` descreve claramente a ausência temporária de validação humana agronômica e o uso limitado de especialistas IA.
- A sequência oficial mantém celular por último.
- Smoke test passa no WSL e não apresenta incompatibilidade Windows como falha do produto.
- Testes unitários, compilação, scanner e baterias completas passam no código final.
- O fluxo agronômico tem especialista de IA, revisão independente, saídas estruturadas rastreáveis e bloqueio de casos inconclusivos; zero casos inconclusivos são promovidos.
- Documentos/status correspondem aos resultados executados na mesma revisão.
- A auditoria final declara o que ainda impede um beta restrito.

## Riscos

- Agentes podem compartilhar erro ou interpretar mal documento técnico; reduzir risco com pesquisa independente, citações localizáveis e bloqueio de divergências; ainda assim, explicitar que não há validação humana.
- Fontes antigas/dinâmicas podem não sustentar recomendações atuais; não promover alegações operacionais sem confirmar vigência.
- Relatórios locais existentes podem ser evidência divergente de outra revisão; não sobrescrevê-los.
- Scanner da árvore atual não resolve exposição em commits históricos; rotação e eventual reescrita dependem de acesso/coordenação do mantenedor.
- Android físico não está disponível como gate técnico agora e permanece por último.

## Registro do plano

- Planejamento executado antes da implementação, conforme pedido do usuário.
- Próximo passo local: criar artefato do especialista de milho e corrigir o smoke test, mantendo mudanças pequenas e reversíveis.
