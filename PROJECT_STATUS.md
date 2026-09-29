# Status de evolução — IA Farm

| Componente | Estado | Etapa Atual | Próximo Passo |
| :--- | :--- | :--- | :--- |
| Orquestrador | ✅ Baseline determinístico | Regras locais, exibição literal de referências revisadas, sem geração de texto | Ampliar cobertura e validar fontes |
| Calculadora | ✅ Determinística | Aritmética sobre dose validada | Ampliar somente com fontes agronômicas |
| RAG / Vetores | 🟡 Busca local disponível | Embeddings locais + FAISS; não gera respostas | Medir viabilidade/offline no Android |
| Memória | ✅ Portável | SQLite com conexões fechadas | Definir política de retenção |
| Mobile | 🚩 Planejado | Ainda sem validação em hardware | Protótipo Android |
| Simulação de personas | ✅ 100 baterias determinísticas | 3 personas por bateria; fixtures sintéticas, sem geração ou rede | Adicionar casos agronômicos só após aprovação profissional |
| Golden Set agronômico | 🚩 Pendente | Sem dose aprovada por fonte/especialista | Revisão agronômica com fontes |
| CI / Segurança | ✅ Baseline | Testes, compileall, scan e dependency review no GitHub Actions | Adicionar SAST avançado se necessário |

## Verificação mais recente

- `unittest`: 8 testes passando.
- `compileall`: concluído sem erros após as alterações.
- Dependências de runtime: disponíveis no ambiente de validação.
- Índice FAISS: `ntotal=9`, `metadata=9`.
- Busca vazia: falha fechada com resposta segura.
- Credenciais ativas: nenhuma encontrada no conteúdo atual.
- Simulação: 100 baterias × 3 personas (300/300 aprovações), fixtures sintéticas, sem modelo generativo, embeddings ou rede.
- Varredura de segurança: sem credenciais ativas ou caminhos obsoletos nos arquivos rastreados.

Embeddings ainda precisam de validação de empacotamento offline e desempenho em aparelho Android; as baterias não substituem essa validação.

Credenciais expostas em commits históricos ainda precisam ser revogadas no
provedor e removidas do histórico público por um mantenedor com acesso ao
GitHub; isso não é substituído pela limpeza do estado atual.
