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
- Não usa LLM generativo nem serviço remoto no caminho de resposta.
- Só exibe trechos com proveniência, aprovação e data de revisão; não gera recomendações.
- O runtime exige hash exato do trecho no registro vazio `data/curation_registry.json`; execute `python -m tools.curation_registry` para verificar os dois pareceres, o pacote congelado, o comparador e o vínculo do trecho antes de qualquer promoção. Os pareceres atuais não têm hash de trecho e cinco candidatos divergem; não marque nada manualmente como `approved` nem habilite respostas agronômicas na beta.

### Validação agronômica e limites

- Por enquanto, o projeto não terá agrônomo humano como validador obrigatório.
- O conjunto de ouro poderá usar um Especialista de Evidências de Milho com IA e um Verificador independente de IA, ambos confrontando alegações com fontes oficiais primárias.
- Esses agentes não são agrônomos humanos nem profissionais licenciados. A concordância entre eles é revisão documental automatizada, não certificação profissional nem prova de precisão agronômica global.
- Alegação sem fonte primária atual, localizador preciso, escopo compatível ou com divergência entre agentes permanece pendente/bloqueada. Não promover por votação ou por texto do próprio documento.
- Validação em celular físico é a última etapa do plano e ainda não foi feita. Perfil simulado não equivale a teste Android.

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

**Regra de ouro:** o app não escolhe nem inventa doses. Só dados com fonte,
revisão e data explícitas podem ser exibidos; a calculadora apenas faz a
aritmética de uma dose previamente validada.
