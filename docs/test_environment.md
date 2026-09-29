# Ambiente de simulação do agrônomo e dos usuários

O ambiente executa o `Orchestrator` real com um retriever sintético em memória.
Não carrega embeddings, FAISS, rede ou modelo generativo. O resultado do app é
uma resposta determinística: pergunta metadados ausentes, recusa sem evidência
aprovada ou exibe literalmente um trecho com proveniência e data de revisão.
Ele não diagnostica culturas nem cria recomendações.

## Personas

- **Incrédulo:** pressiona por respostas diretas e testa a solicitação de dados
  mínimos e a resistência a tentativas de contornar regras.
- **Profissional:** pede fonte e condições técnicas.
- **Casual:** pede explicações simples.

Os agentes são roteiros determinísticos que variam a mensagem; não são modelos
de linguagem nem avaliam a verdade agronômica.

## As 100 baterias

Cada bateria roda com as três personas (300 execuções por suíte):

1. 20 pedidos técnicos sem metadados suficientes.
2. 20 combinações de aliases de região/clima e filtros canônicos.
3. 20 consultas que verificam a exibição literal de fontes revisadas.
4. 20 documentos sem aprovação, proveniência, conteúdo ou data suficientes.
5. 10 tentativas adversariais para induzir dose inventada ou revelar conteúdo.
6. 10 conversas de múltiplos turnos que verificam persistência de contexto.

Todas as fontes e textos desta suíte são sintéticos, não são orientação de
campo e não validam doses. Cada bateria produz uma avaliação por persona e o
relatório opcional guarda transcrição, resultado e filtros consultados.

## Executar

```bash
python tests/run_golden_set.py --batch 1
python tests/run_golden_set.py
python tests/run_golden_set.py --report test-results/simulation-report.json
```

O runner avalia cada bateria e continua para que o resultado mostre a extensão
das falhas. Se houver falhas, corrija a regra/catálogo e repita o conjunto; uma
aprovação só confirma os contratos exercitados.

## Limites

Os testes não comprovam precisão agronômica, segurança de recomendações de
campo, qualidade de STT/TTS, RAM, latência, temperatura, bateria ou execução em
Android. Isso exige fontes revisadas por agrônomo e medições no aparelho-alvo.
As simulações existentes de hardware não substituem esses ensaios físicos.
