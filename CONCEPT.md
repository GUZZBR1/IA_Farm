# 🌾 Conceito e Visão - AgriBrain

O AgriBrain não é apenas um chatbot agrícola; é um **Sistema Especialista Autônomo** desenhado para democratizar a agricultura de precisão, levando o conhecimento de agrônomos de elite para o bolso do produtor.

## 🎯 A Grande Ideia
Criar uma IA capaz de rodar em hardware limitado (celulares Android de 4GB RAM), funcionando de forma **offline-first**, para que o agricultor no campo tenha respostas precisas sem depender de internet.

## 🧠 Filosofia de Projeto (The DNA)

### 1. Determinismo vs. Probabilidade
A maior falha das LLMs é a alucinação matemática. O AgriBrain resolve isso com a **Regra de Ouro**:
- **A IA nunca calcula**. Ela extrai a necessidade (ex: "solo arenoso, produtividade 12t") e a entrega para um **Calculador Determinístico** (código puro).
- **Resultado**: Erro zero em dosagens químicas.

### 2. Conhecimento Estruturado (RAG)
Em vez de confiar no treinamento geral da IA, o sistema usa **RAG (Retrieval-Augmented Generation)**:
- **Fontes**: Manuais da EMBRAPA, CIMMYT e universidades.
- **Processo**: A IA busca o trecho exato do manual técnico $ightarrow$ valida os metadados $ightarrow$ formula a resposta.

### 3. Eficiência Extrema (Mobile Hardening)
Para rodar em celulares simples, o sistema utiliza:
- **Quantização 4-bit**: Redução do peso do modelo sem perda significativa de inteligência.
- **mmap (Memory Mapping)**: Para evitar que o Android encerre o app por consumo de RAM.
- **Delta Updates**: Atualizações leves de conhecimento sem precisar baixar o modelo inteiro.

## 🛠️ Pilares Técnicos
- **Visão $ightarrow$ JSON**: Transformação de tabelas de PDF em dados estruturados.
- **Extrator Híbrido**: Combinação de busca por palavras-chave e LLM para garantir que a região e o clima sejam detectados corretamente.
- **Red Teaming**: Testes rigorosos com personas (Agricultor Cético, Auditor da EMBRAPA) para garantir a segurança do sistema.

---
*Este projeto nasceu da visão de transformar a agricultura através da tecnologia local, segura e acessível.*
