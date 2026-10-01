# Registro de validação legado — não usar como benchmark

Este arquivo substitui um relatório antigo que anunciava “15% de precisão”
com 20 exemplos. Aquele percentual foi removido: os exemplos não tinham fontes
verificáveis, revisão agronômica, execução reproduzível nem um método de
comparação válido. Algumas doses citadas eram conflitantes com o dataset local.

Portanto, o relatório legado não prova nem reprova a precisão agronômica do app.
Não reutilize seus exemplos numéricos como recomendações ou gabarito. O status
atual do alvo de 95% está documentado em [`golden_set_policy.md`](../docs/golden_set_policy.md):
precisão agronômica permanece **não medida**, pois falta um conjunto de referência
avaliado com evidência oficial e relatórios independentes dos dois agentes.

As baterias sintéticas de `run_golden_set.py` verificam contratos determinísticos
de segurança, metadados, proveniência e exibição literal. Elas não medem verdade
agronômica.

## Execução atual — 2026-09-29

- 165 cenários × 4 personas: 660/660 execuções aprovadas pelo auditor
  comportamental determinístico.
- Testes unitários: 54 passaram após incluir smoke multiplataforma, comparação de pareceres, validação
  de fontes oficiais e verificação do hash do relatório congelado.
- Smoke em Windows e WSL/Linux, offline e sem modelo generativo: inicialização,
  demonstração e encerramento aprovados. No WSL, uma CPU lógica e 1536 MiB de
  espaço virtual; no Windows, sem envelope de recursos Unix. Isso não é validação
  em Android/ARM64.
- Verificações estáticas: `compileall` e scanner de segurança aprovados.
- Precisão agronômica: `not_measured`; o conjunto-ouro permanece vazio. Os
  660 testes são somente comportamentais. Os 18 rascunhos receberam revisão do
  Especialista de Evidências de IA e do Verificador independente, ambos ligados
  ao SHA-256 do arquivo candidato. O comparador encontrou 13 julgamentos iguais,
  5 divergências de julgamento/escopo e variações de citações em todos os casos.
  Casos parcialmente corretos, divergentes ou com evidência insuficiente não
  foram promovidos; nenhum agente é validador humano ou profissional licenciado.
- Pesquisa atual ampliou o registro para 18 casos candidatos pendentes, em
  manejo do solo, ZARC, adubação, irrigação, pragas/doenças, fenologia,
  estresse hídrico, colheita e armazenamento. Nenhum candidato foi contado como
  acerto, incorporado à base offline ou usado para alegar 95%.
- O índice FAISS local contém 9 trechos do dataset MVP, mas 0/9 passam pela
  validação de fonte aprovada do orquestrador. Todos carecem de `crop`,
  `review_status` e data de revisão; 6/9 contêm termos de dose/controle químico.
  Um ensaio do filtro do orquestrador com retriever de leitura devolvendo esses
  9 registros retornou ausência segura de evidência aprovada. O FAISS real não
  inicializou no ambiente WSL porque `faiss-cpu` não está instalado; portanto,
  recuperação por embeddings e execução fim a fim sobre o índice não foram
  validadas nesta rodada. O gate evita conteúdo não revisado, mas deixa zero
  trechos elegíveis para respostas agronômicas.
- A instalação de `requirements.txt` em ambiente temporário do WSL falhou porque
  o DNS não resolveu o índice de pacotes. `numpy`, `faiss-cpu` e
  `sentence-transformers` continuam ausentes; carregamento e busca no índice real
  não puderam ser validados. `requirements.txt` não foi alterado.
- Relatórios rastreáveis dos agentes: `agronomic_gold_specialist_review.json`,
  `agronomic_gold_independent_review.json` e
  `agronomic_gold_review_comparison.json`. O relatório do comparador não autentica
  as fontes; as citações distintas estão listadas para inspeção e os julgamentos
  divergentes permanecem bloqueados.
- Validação de aparelho Android foi adiada para a última fase, conforme o plano.

## Revalidação do gate de curadoria — 2026-09-30

- O runtime deixou de confiar em `review_status=approved` isoladamente. Exige
  identificador de registro, SHA-256 do trecho exato e correspondência de fonte,
  cultura e data no registro `data/curation_registry.json`.
- `python -m tools.curation_registry`: válido, zero trechos aprovados. A
  validação de entradas não vazias verifica hashes dos arquivos vinculados,
  pacote candidato congelado, os dois papéis de revisão, hash do trecho presente
  em ambos os pareceres, fonte/cultura e ausência de divergência para o caso.
- Testes unitários: 58 passaram, incluindo aprovação vinculada a pareceres
  sintéticos de teste, bloqueio de aprovação só por
  metadados e de alteração do texto após curadoria.
- Simulação final: 165 baterias × 4 personas, 660/660 passagens. As permissões
  sintéticas são injetadas exclusivamente pelo harness de testes e não gravadas
  no registro de produto.
- O conjunto-ouro e o registro de produção continuam vazios; precisão
  agronômica permanece não medida. As 18 revisões existentes não têm hashes de
  trechos exatos e cinco casos divergem. Não são promovíveis sem nova rodada de
  revisão por IA vinculada ao trecho literal.
- Permanecem pendentes: política de privacidade/retenção da memória, direitos de
  redistribuição das fontes e rotação de credenciais históricas. Celular físico
  continua deliberadamente por último.

## RAG/FAISS real validado — 2026-09-30

- A falha de DNS foi contornada sem alterar rede global: o host Windows baixou
  wheels Linux compatíveis para Python 3.12 e estes foram instalados offline em
  venv temporário no WSL. O modelo `all-MiniLM-L6-v2` já estava no cache do host
  e foi carregado em modo offline.
- Versões: `faiss-cpu 1.9.0.post1`, `numpy 2.5.3`,
  `sentence-transformers 6.1.0`, `torch 2.6.0+cpu`.
- `tests/validate_real_vector_db.py` passou: carregou 9 vetores de dimensão 384,
  recuperou o trecho sobre *Spodoptera frugiperda* no topo, validou 5 resultados
  com filtro regional e zero com filtro inexistente, testou gravação/leitura e
  filtros num índice temporário, verificou abstenção do gate de curadoria e
  confirmou hashes inalterados no índice original.
- Os 58 testes unitários passaram também com esse ambiente real no WSL.
- A causa local do DNS foi rastreada até o resolvedor Tailscale configurado em
  `100.100.100.100`, que retorna `SERVFAIL`; resolvedores externos responderam,
  mas não substituímos a configuração do tailnet. Para novas instalações online,
  um administrador do tailnet ainda precisa corrigir upstream/split DNS. A
  dependência de teste foi resolvida usando wheelhouse offline.
