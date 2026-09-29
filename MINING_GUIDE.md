# 🛠️ Guia de Mineração e Implementação - AgriBrain

Este documento descreve como operar o motor de conhecimento do AgriBrain.

## 1. Arquitetura de Dados
O AgriBrain utiliza um sistema de RAG (Retrieval-Augmented Generation).

## 2. Fluxo de Mineração
Fonte (PDF/Web) -> Extração (Vision-to-JSON) -> Chunking -> Embeddings -> Vector Store (FAISS)

## 3. Setup de Persistência (Bypass de Quota)
Caminho Lógico: /home/guzzbr/meus-projetos/IA_Farm/data
Caminho Físico: /var/tmp/ia_farm_data

## 4. Executando a Mineração
python scripts/miner.py --source <url_ou_pasta> --crop milho

## 5. Validação
python tools/vector_engine.py --check-index