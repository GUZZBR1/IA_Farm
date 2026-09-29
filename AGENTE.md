# 🤖 Agente AgriBrain - Mapa de Operação

Este documento serve como a interface de entrada para qualquer agente ou desenvolvedor que assuma o controle do AgriBrain.

## 📍 Endereços e Estrutura
Todo o projeto está centralizado no servidor em: `/home/guzzbr/meus-projetos/IA_Farm`

### 📂 Componentes Principais
- **Core Engine**: `/src` (no GitHub) $ightarrow$ Lógica de orquestração e tomada de decisão.
- **Knowledge Vault**: `/home/guzzbr/ObsidianVault` $ightarrow$ Memória de longo prazo e DNAs do projeto.
- **Data Store**: `/home/guzzbr/meus-projetos/IA_Farm/data` (Sincronizado com `/var/tmp/ia_farm_data`) $ightarrow$ Índices vetoriais do FAISS.
- **Master Docs**: `/home/guzzbr/meus-projetos/IA_Farm/project_master_docs` $ightarrow$ Registros de status e mapa do sistema.

---

## 🛠️ Status de Implementação e Etapas

O projeto segue a filosofia de **Engenharia de Precisão**. Abaixo, o estado real de cada pilar:

### 1. Cérebro e Orquestração (CONCLUÍDO ✅)
- **Orquestrador**: Implementado. Faz o desvio automático de cálculos para a calculadora determinística.
- **Memória**: Implementada via SQLite.

### 2. Motor de Conhecimento / RAG (EM ANDAMENTO ⏳)
- **Estrutura**: Implementada (VectorEngine).
- **Mineração**: Ativa. O sistema consegue minerar e indexar fontes como EMBRAPA e CIMMYT.
- **Falta**: Validar a precisão do retrieval com métricas objetivas (Recall/Hit Rate).

### 3. Calculadora de Dosagem (CONCLUÍDO ✅)
- **Lógica**: Implementada para Milho e Nitrogênio.
- **Segurança**: Bloqueio total de alucinações matemáticas (0% de erro em cálculos).

### 4. Versão Mobile / Android (PLANEJADO 🚩)
- **Hardware**: Alvo de 4GB RAM.
- **Técnica**: Planejado uso de Phi-3 Mini quantizado e `mmap` para estabilidade.
- **Falta**: Testes em aparelho físico e implementação final via MLC LLM.

---

## 🚀 Como Operar este Agente
1. **Para configurar o ambiente**: Leia o `MINING_GUIDE.md`.
2. **Para alterar a lógica de dose**: Edite `tools/calculator.py`.
3. **Para expandir o conhecimento**: Execute o `scripts/miner.py`.
4. **Para consultar o DNA**: Acesse o Obsidian Vault em `/dnas/ia-farm.md`.

**Regra de Ouro:** Nunca permita que a IA calcule doses. Sempre force a passagem pelo `DosageCalculator`.
