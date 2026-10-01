# Plano de recuperação e validação do RAG/FAISS real

## Estado — concluído em 2026-09-30

- Dois agentes read-only foram acionados: debugger e dependency-expert. Um
  primeiro par de agentes falhou na inicialização por incompatibilidade de
  modelo; foram reabertos herdando o modelo do líder e concluíram.
- O DNS Tailscale do WSL (`100.100.100.100`) retorna `SERVFAIL`. Para concluir
  sem mudar configuração global, o host baixou wheels Linux compatíveis e o
  WSL as instalou offline num venv descartável.
- Validação real passou: 9 vetores/384 dims, recuperação, filtros, fail-closed,
  round-trip de escrita/leitura num índice temporário e integridade do índice
  original. Também passaram 58 testes unitários no venv real do WSL.
- O DNS em si não foi reconfigurado; novas instalações online ainda dependem
  de correção do upstream/split DNS do tailnet.

## Objetivo

Instalar/usar as dependências do RAG num ambiente isolado e reproduzível,
diagnosticar o DNS do WSL sem alterar configuração global de rede e validar
carregamento, paridade índice/metadados e consultas reais com FAISS/embeddings.

## Equipe definida antes da execução

- Líder (executor): inspeciona o projeto e o WSL local, testa conectividade,
  prepara ambiente virtual descartável, integra recomendações e executa testes.
- Agente `debugger` (somente leitura): identifica causa provável do DNS/PyPI no
  WSL e recomenda verificações/alternativas seguras, sem alterar a rede.
- Agente `dependency-expert` (somente leitura): confere requisitos e
  compatibilidade Python/Windows/WSL das dependências FAISS e recomenda uma
  instalação isolada/offline viável, sem instalar pacotes.

Não delegar alterações simultâneas; configuração de rede e instalação ficam
sob controle do líder no ambiente isolado.

## Sequência

1. Inspecionar `requirements.txt`, `tools/vector_db.py`, índice atual e estado
   do WSL; registrar hipóteses e teste mínimo.
2. Em paralelo, obter os dois pareceres independentes e executar localmente
   diagnóstico de DNS/HTTP, pip e alternativas host/WSL sem tocar no ambiente
   global.
3. Criar venv temporário; instalar dependências compatíveis, resolver
   bloqueios com alternativa suportada se possível.
4. Construir teste real em índice temporário e conferir carregamento,
   consistência FAISS/metadados, busca top-k/filtros e resultado fail-closed.
5. Reexecutar testes, smoke e scanner; documentar ambiente, comandos,
   resultados e limites. Não validar Android nesta etapa.

## Critério de conclusão

`LocalVectorDB` inicia com dependências reais, indexa e recupera texto com
metadados consistentes, filtros são aplicados, consultas vazias retornam vazio,
e os testes do projeto seguem verdes. Se o DNS continuar bloqueado, tentar
cache/índices locais ou instalação no host somente em ambiente virtual; não
alterar resolvers do sistema nem afirmar validação real sem os testes.
