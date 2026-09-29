# 🗺️ Roadmap de Evolução - AgriBrain

Este plano define a trajetória técnica para transformar o motor atual em um produto funcional no campo.

## Fase 1: Consolidação do Motor (baseline atual)
**Objetivo**: Garantir que a inteligência no servidor seja infalível.
- [x] Implementação do orquestrador.
- [x] Calculadora determinística de aritmética por área.
- [x] Criar dez baterias de simulação determinística com três personas e guardrails sem doses inventadas.
- [ ] Expandir a calculadora para outros nutrientes (P, K) e culturas.
- [x] Adicionar CI, compilação e varredura de segredos.
- [ ] Fazer validação agronômica dos casos com fontes e especialistas.

## Stage 2: The "Corn" MVP
- [ ] Curate high-quality Corn manuals (EMBRAPA/Industry).
- [ ] Implement the Vision-to-JSON pipeline for dosage tables.
- [x] Create the metadata tagging system (Region/Climate) — baseline tagger and canonical filters.
- [x] Build the Local Vector DB for the Corn dataset — local index generated and checked for vector/metadata parity.
- [ ] Review every agronomic document and attach provenance, date and agronomist approval.

## Fase 2: Laboratório de Estresse (Red Teaming)
**Objetivo**: Tentar quebrar o sistema antes que o usuário tente.
- [x] Implementar bateria inicial de guardrails com o "Agricultor Cético".
- [ ] Implementar revisão com o "Auditor EMBRAPA" usando casos citados.
- [ ] Testar a resiliência do Extrator Híbrido com dados reais e ruidosos.
- [ ] Certificar que 100% dos cálculos de dose sejam desviados para a calculadora.

## 📍 Fase 3: Mobile Hardening (O Desafio do Hardware)
**Objetivo**: Fazer a IA rodar em Androids de 4GB RAM.
- [ ] **Quantização**: Testar Phi-3 Mini em 4-bit via GGUF.
- [ ] **Integração**: Implementar via MLC LLM ou Llama.cpp para Android.
- [ ] **Otimização**: Validar a implementação de `mmap` para evitar crashes de memória (OOM).
- [ ] **Benchmarks**: Medir tokens/s e consumo de bateria no aparelho físico.

## 📍 Fase 4: Beta Field Test (Validação de Campo)
**Objetivo**: Validar a utilidade real com produtores.
- [ ] Lançar versão Alpha para grupo restrito de testes.
- [ ] Coletar feedback sobre a interface de voz (STT/TTS).
- [ ] Comparar recomendações da IA vs. Recomendações de Agrônomos Reais.

## 🏁 Meta Final: MVP Autónomo
Um app que funciona 100% offline, não alucina em cálculos e entrega precisão técnica de nível EMBRAPA no bolso do agricultor.

## Baseline implementation status

The repository now has a dependency manifest, portable project paths, an explicit
mock mode, fail-closed retrieval when no context is found, Markdown ingestion,
canonical metadata matching, deterministic area-dose arithmetic, and automated
core tests. External validation remains pending for the real Ollama model, the
FAISS index build, field users, and Android hardware.

## Stage 5: Deployment & Scaling
- [ ] Beta test with real corn farmers.
- [ ] Implement Delta Updates for knowledge base.
- [ ] Expand to other cultures.

## Segurança e operação

- [x] Remover credenciais e caminhos específicos do estado atual.
- [x] Documentar rotação e resposta a credenciais em `SECURITY.md`.
- [ ] Revogar credenciais que permanecem em commits históricos.
- [ ] Executar rewrite coordenado do histórico, se o mantenedor autorizar.
