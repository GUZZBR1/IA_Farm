# 🛠️ Guia de Mineração e Implementação - AgriBrain

Este documento descreve como operar o motor de conhecimento do AgriBrain.

## 1. Arquitetura de Dados
O AgriBrain utiliza um sistema de RAG (Retrieval-Augmented Generation).

## 2. Fluxo de Mineração
Fonte (PDF/Web) -> Extração (Vision-to-JSON) -> Chunking -> Embeddings -> Vector Store (FAISS)

## 3. Setup de Persistência

O índice fica em `data/vector_index` por padrão. O caminho pode ser alterado
com `--index-path`.

## 4. Executando a Mineração

Depois de instalar `requirements.txt`, indexe as fontes aprovadas:

```bash
python -m tools.mining_agent docs/corn_mvp/dataset_v0.1.md
```

O minerador não baixa fontes automaticamente nem inventa dados. A curadoria e
a validação dos documentos devem ocorrer antes da indexação.

## 5. Validação

```bash
python -m tools.test_libs
python -m unittest discover -s tests -p 'test_*.py'
```
