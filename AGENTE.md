# Agente AgriBrain - Mapa de Operação

Este documento serve como interface de entrada para qualquer agente ou
desenvolvedor que assuma o controle do AgriBrain.

## Estrutura

- **Core engine**: `tools/orchastrator.py` e `main.py`.
- **Knowledge base**: `docs/corn_mvp` e o índice gerado em `data/vector_index`.
- **Dados locais**: `data/`; índices e banco de memória não devem ser versionados.
- **Documentação**: `PROJECT_STATUS.md`, `ROADMAP.md` e `project_master_docs/`.

## Estado atual

### Orquestração

- Exige região e clima antes de recomendações técnicas.
- Não consulta LLM quando o RAG não retorna contexto.
- Usa `OPENROUTER_API_KEY` somente como fallback explícito.

### RAG

- `LocalVectorDB` é a implementação oficial.
- `VectorEngine` existe apenas como adaptador de compatibilidade.
- A mineração indexa fontes locais previamente curadas.
- Download automático de fontes ainda não está implementado.

### Calculadora

- `tools/dosage_calculator.py` faz apenas aritmética de uma dose validada por hectare.
- Não inventa recomendações agronômicas.
- A expansão para N/P/K e outras culturas depende de fontes técnicas aprovadas.

## Como operar

1. Leia `MINING_GUIDE.md` para configurar e indexar fontes.
2. Use `python -m tools.mining_agent` para ingerir documentos curados.
3. Execute `python -m unittest discover -s tests -p 'test_*.py'`.
4. Leia `docs/agent_dna.md` antes de alterar regras de segurança.

**Regra de ouro:** nunca permita que o LLM invente doses; toda recomendação
numérica deve ser rastreável a uma fonte validada e passar por cálculo
determinístico.
