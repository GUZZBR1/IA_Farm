# Plano do tópico — gate de curadoria rastreável

## Estado

Implementado e revalidado em 2026-09-30. O registro continua vazio, de forma
intencional; nenhum dos 18 candidatos foi promovido.

## Objetivo

Impedir que um registro seja exibido só porque o índice declara `review_status: approved`. A exibição deve depender de uma entrada controlada que vincule o texto exato, sua proveniência e os dois pareceres de IA. Nenhuma aprovação humana agronômica será adicionada. Nenhum dos 18 casos atuais será promovido, pois os relatórios divergem e não vinculam hashes de trechos exatos.

## Agentes nesta etapa

- Executor/integração: agente líder desta conversa, dono das alterações no registro, runtime, CLI e testes.
- Não serão iniciados subagentes nesta etapa; o schema atual e o diff estão no contexto e o corte de arquivos é pequeno e sequencial.
- Depois da implementação, usar as verificações automatizadas e fazer nova auditoria de prontidão antes de encerrar.

## Implementação planejada

1. Mapear `Orchestrator._is_reviewed`, `Orchestrator.__init__`, `tools/ingest.py`, `tools/vector_db.py` e os fixtures aprovados em `tests/test_core.py`, `tests/run_golden_set.py` e `tests/battery_catalog.py`.
2. Definir schema versionado para registro de curadoria com `record_id`, SHA-256 do texto exibido, `source_id`, cultura, data, URLs/fontes, papéis de revisão, paths e hashes dos dois pareceres e hash do pacote de entrada congelado.
3. Criar validador/CLI de curadoria sem dependências novas. A aprovação será recusada se artefatos não existirem, seus hashes divergirem, comparador não der acordo de fontes oficiais, o escopo não corresponder ou o texto revisado não corresponder ao SHA-256.
4. Fazer o runtime exigir uma entrada válida do registro e correspondência exata do hash do trecho; status manual no vetor não será suficiente. Registro ausente/inválido resulta em abstenção.
5. Iniciar com registro vazio. Relatórios atuais não incluem o hash de cada excerto e têm 5 divergências; não preencher entradas até que existam revisões ligadas ao conteúdo exato.
6. Atualizar fixtures sintéticas de testes para usar registro de teste injetado; fixtures nunca entram no registro do produto.
7. Atualizar documentação e roadmap; executar suite unitária, 165 baterias, smoke Windows/WSL, compilação, scanner e auditoria final. **Concluído:** 58 testes, 660/660 personas, smoke nos dois ambientes, compileall, scanner e validador do registro passaram.

## Critérios de aceitação

- Documento `approved` sem registro válido é recusado.
- Documento cujo texto, fonte, cultura, data, report hash ou input hash não correspondem ao registro é recusado.
- Registro só é aceito quando ambos os pareceres foram carregados, verificados contra seus arquivos e o comparador concluiu `agent_agreement_official_sources` para o mesmo caso.
- Trechos sintéticos continuam limitados aos testes.
- Registro de produção permanece vazio; nada dos 18 candidatos atuais é promovido.
- Nenhuma dependência externa nova.

## Limites

O registro é controle de integridade e proveniência do build, não assinatura criptográfica contra um mantenedor que possa alterar simultaneamente código, manifest e conteúdo. Relatórios de IA não autenticam a verdade agronômica; continuam sendo revisão documental assistiva.
