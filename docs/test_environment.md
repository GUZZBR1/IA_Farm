# Ambiente de simulação do agrônomo e dos usuários

O ambiente executa o `Orchestrator` real com duas dependências controladas:
um retriever de documentos de teste e um adaptador de agrônomo determinístico.
Ele não usa serviços externos, FAISS ou um modelo generativo real. Isso torna os
resultados reproduzíveis e permite verificar roteamento, filtros, perguntas de
esclarecimento e recusa sem contexto.

## Personas

- **Incrédulo:** pressiona por respostas diretas e testa a solicitação de dados
  mínimos.
- **Profissional:** pede fonte e condições técnicas.
- **Casual:** pede explicações simples.

São agentes de usuário baseados em roteiros determinísticos. A persona altera a
mensagem de entrada; o sistema sob teste continua sendo o orquestrador do app.
O adaptador de agrônomo devolve respostas fixas indicadas por cada cenário, não
faz avaliação agronômica.

## As dez baterias

1. Pedido inicial de dose sem região ou clima.
2. Região informada, clima ausente.
3. Clima informado, região ausente.
4. Extração de região e clima de uma frase natural e filtros canônicos.
5. Seleção de inseticida sem contexto.
6. Uso da forma portuguesa “dosagem”.
7. Tentativa de jailbreak antes de haver contexto.
8. Tentativa de jailbreak com metadados completos, mas sem evidência.
9. Auditoria profissional de uma dose sem fonte recuperada.
10. Conversa de dois turnos com persistência de região/clima e contexto de teste.

Cada bateria roda pelos três agentes, registra a entrada e resposta de cada
turno, os filtros do retriever e se o modelo simulado foi chamado. As regras
automáticas avaliam fragmentos esperados/proibidos e contagem de chamadas.

## Executar

No ambiente Python com as dependências de teste:

```bash
python tests/run_golden_set.py --batch 1
python tests/run_golden_set.py
python tests/run_golden_set.py --report test-results/simulation-report.json
```

O primeiro comando roda uma bateria para avaliação e ajuste incremental. O
segundo executa todas as baterias. O terceiro salva as transcrições e métricas em
JSON local; `test-results/` não deve ser versionado se contiver dados de usuário.

## Como interpretar

Uma aprovação comprova somente o contrato determinístico do orquestrador no
cenário testado. Não comprova qualidade de um LLM real, resistência semântica a
jailbreak quando o modelo é chamado, validade de uma dose agronômica, consumo de
RAM, latência ou funcionamento em Android. Casos agronômicos reais exigem fonte
rastreável e revisão de profissional qualificado; testes de modelo devem
registrar modelo, versão, runtime e critérios de revisão separadamente.
