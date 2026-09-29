# Status de evolução — IA Farm

| Componente | Estado | Etapa Atual | Próximo Passo |
| :--- | :--- | :--- | :--- |
| Orquestrador | ✅ Baseline seguro | RAG local-first, sem contexto inventado | Validar chamadas reais de LLM |
| Calculadora | ✅ Determinística | Aritmética sobre dose validada | Ampliar somente com fontes agronômicas |
| RAG / Vetores | ✅ Índice local validado | 9 vetores para 5 documentos | Medir precisão agronômica com fontes |
| Memória | ✅ Portável | SQLite com conexões fechadas | Definir política de retenção |
| Mobile | 🚩 Planejado | Ainda sem validação em hardware | Protótipo Android |
| Golden Set | ✅ Guardrails validados | 5 casos sem doses inventadas | Revisão agronômica com fontes |
| CI / Segurança | ✅ Baseline | Testes, compileall, scan e dependency review no GitHub Actions | Adicionar SAST avançado se necessário |

## Verificação mais recente

- `unittest`: 6 testes passando.
- `compileall`: concluído sem erros.
- Dependências de runtime: disponíveis no ambiente de validação.
- Índice FAISS: `ntotal=9`, `metadata=9`.
- Busca vazia: falha fechada com resposta segura.
- Credenciais ativas: nenhuma encontrada no conteúdo atual.
- Golden Set de guardrails: 5/5 casos passando.

Credenciais expostas em commits históricos ainda precisam ser revogadas no
provedor e removidas do histórico público por um mantenedor com acesso ao
GitHub; isso não é substituído pela limpeza do estado atual.
