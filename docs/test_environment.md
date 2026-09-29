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

Os agentes de usuário são roteiros determinísticos que variam a mensagem; não
são modelos de linguagem. Um agente auditor com papel de agrônomo verifica
somente contratos de contexto, segurança, escopo regional, proveniência e
exibição literal. Ele não valida a verdade agronômica nem substitui um
profissional real.

## Perfil de celular simulado

O perfil padrão é `android-low-mid-4gb`: celular Android fraco/médio, ARM64,
4 GB de RAM total e conectividade indisponível. O modelo generativo permanece
desligado e a recuperação usa fixtures em memória que respeitam os filtros de
região e clima. O perfil registra as condições pretendidas para os cenários;
ele não impõe limites de RAM/CPU nem emula o kernel Android.

A orquestração aceita proveniência tanto no formato aninhado dos fixtures
(`metadata`) quanto no formato plano retornado pelo índice vetorial local. Essa
compatibilidade não aprova automaticamente registros: fonte, estado de revisão
e data válida continuam obrigatórios. Os testes exercitam o contrato sem
depender de FAISS ou do modelo de embeddings.

O relatório marca explicitamente `physical_device_validated: false`. Portanto,
não se deve inferir deste ambiente memória disponível ao processo, velocidade
ARM64, encerramento sob pressão, temperatura, consumo de bateria, empacotamento
Android ou carregamento do modelo.

## As 130 baterias

Cada bateria roda com as três personas (390 execuções por suíte):

1. 20 pedidos técnicos sem metadados suficientes.
2. 20 combinações de aliases de região/clima e filtros canônicos.
3. 20 consultas que verificam a exibição literal de fontes revisadas.
4. 20 documentos sem aprovação, proveniência, conteúdo ou data suficientes.
5. 10 tentativas adversariais para induzir dose inventada ou revelar conteúdo.
6. 10 conversas de múltiplos turnos que verificam persistência de contexto.
7. 10 correções de região/clima durante a conversa, conferindo atualização dos filtros.
8. 10 consultas cuja única referência aprovada pertence a outra região, que devem falhar de forma segura.
9. 10 tentativas de pressionar o app a confirmar uma dose numérica sem respaldo.

Todas as fontes e textos desta suíte são sintéticos, não são orientação de
campo e não validam doses. Cada bateria produz uma avaliação por persona e o
relatório opcional guarda transcrição, resultado e filtros consultados.

## Executar

```bash
python tests/run_golden_set.py --batch 1
python tests/run_golden_set.py
python tests/run_golden_set.py --report test-results/simulation-report.json
```

O runner avalia cada bateria para as três personas e submete cada transcrição
ao auditor determinístico, continuando para mostrar a extensão das falhas. Para
executar explicitamente o perfil padrão:

```bash
python tests/run_golden_set.py --device-profile android-low-mid-4gb
```

Para um smoke test executável em Linux/WSL, iniciando o app em um processo
fixado a um núcleo lógico e limitado a 1536 MiB de espaço virtual de endereços:

```bash
python tests/run_low_mid_smoke.py
```

Esse comando roda a interface e a demonstração com retriever vazio, sem rede e
sem modelo generativo. O limite de espaço virtual é uma contenção de processo
para este ensaio, não uma emulação da RAM total ou da gestão de memória Android.

Se houver falhas, corrija a regra/catálogo e repita o conjunto; uma aprovação
só confirma os contratos exercitados.

## Limites

Os testes não comprovam precisão agronômica, segurança de recomendações de
campo, qualidade de STT/TTS, RAM, latência, temperatura, bateria ou execução em
Android. Isso exige fontes revisadas por agrônomo e medições no aparelho-alvo.
As simulações existentes de hardware não substituem esses ensaios físicos.
