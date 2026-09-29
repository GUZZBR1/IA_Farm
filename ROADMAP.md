# 🗺️ Roadmap de Evolução - AgriBrain

Este plano define a trajetória técnica para transformar o motor atual em um produto funcional no campo.

## 📍 Fase 1: Consolidação do Motor (Atual)
**Objetivo**: Garantir que a inteligência no servidor seja infalível.
- [x] Implementação do Orquestrador.
- [x] Calculadora Determinística (Milho/N).
- [ ] **Próximo Passo**: Validar a precisão do RAG com o Golden Set (Métricas de Recall).
- [ ] **Próximo Passo**: Expandir a calculadora para outros nutrientes (P, K) e culturas.

## 📍 Fase 2: Laboratório de Estresse (Red Teaming)
**Objetivo**: Tentar quebrar o sistema antes que o usuário tente.
- [ ] Implementar bateria de testes com o "Agricultor Cético" e "Auditor EMBRAPA".
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
