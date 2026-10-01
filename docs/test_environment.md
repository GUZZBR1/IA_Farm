# Ambiente de simulação do agrônomo e dos usuários

## Validação do RAG/FAISS real (fora da simulação)

O runner `tests/validate_real_vector_db.py` carrega o índice local com FAISS e
Sentence-Transformers reais; não usa o retriever sintético da simulação. Ele
confere contagem vetor/metadados, busca semântica, filtros, abstenção do runtime
para registros não aprovados e um round-trip de gravação/leitura num índice
temporário. O índice existente é lido sem escrita e seus hashes são comparados
antes/depois.

Execução, com as dependências instaladas e o modelo `all-MiniLM-L6-v2` em cache:

```bash
HF_HUB_OFFLINE=1 HF_HOME=/path/to/huggingface-cache \
  python tests/validate_real_vector_db.py
```

Em 2026-09-30 foi executado no WSL Python 3.12.3, em venv temporário, usando
wheels Linux transferidos pelo host Windows porque o resolvedor DNS Tailscale
do WSL retornava `SERVFAIL`. Nenhuma configuração global de DNS foi alterada.
Isso valida execução técnica de recuperação, não qualidade agronômica: o índice
de produto ainda contém 9 trechos legados e nenhum passa pela curadoria. Os
resultados estão em `tests/validation_report.md`.

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
- **Operador por voz no campo:** simula ditado em português sem acentos, comum
  em ambientes móveis e transcrições simples.

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

## As 165 baterias

Cada bateria roda com as quatro personas (660 execuções por suíte):

1. 20 pedidos técnicos sem metadados suficientes.
2. 20 combinações de aliases de região/clima e filtros canônicos.
3. 20 consultas que verificam a exibição literal de fontes revisadas.
4. 20 documentos sem aprovação, proveniência, conteúdo ou data suficientes.
5. 10 tentativas adversariais para induzir dose inventada ou revelar conteúdo.
6. 10 conversas de múltiplos turnos que verificam persistência de contexto.
7. 10 correções de região/clima durante a conversa, conferindo atualização dos filtros.
8. 10 consultas cuja única referência aprovada pertence a outra região, que devem falhar de forma segura.
9. 10 tentativas de pressionar o app a confirmar uma dose numérica sem respaldo.
10. 10 correções de região/clima dentro da mesma mensagem.
11. 10 menções negadas que limpam contexto contradito e exigem confirmação.
12. 10 formas comuns de perguntar sobre adubação, pragas, sintomas e plantio,
    que devem acionar coleta de contexto em vez de consulta sem filtros.
13. 5 mensagens com regiões alternativas, que devem pedir esclarecimento mesmo
    se a sessão já tiver uma região anterior.

Todas as fontes e textos desta suíte são sintéticos, não são orientação de
campo e não validam doses. Cada bateria produz uma avaliação por persona e o
relatório opcional guarda transcrição, resultado e filtros consultados.

## Precisão agronômica

As baterias comportamentais não são o benchmark de precisão agronômica. Para
revisar os casos candidatos, use o Especialista de Evidências Agronômicas de IA
e o Verificador independente, conforme `docs/agronomy_evidence_specialist.md` e
`docs/agronomist_verifier.md`. Não há agrônomo humano validador obrigatório por
enquanto. Os dois agentes pesquisam fontes oficiais, registram localizadores e
escopo; divergências e lacunas ficam bloqueadas. A concordância é evidência
documental automatizada, não certificação nem precisão agronômica global.

Depois de haver casos promovidos ao conjunto de ouro, gere transcrições do
caminho RAG local:

```bash
python tests/run_agronomic_gold.py --output test-results/agronomic-run.json
```

O benchmark descrito abaixo compara as respostas do app com o conjunto de ouro;
ele só pode rodar após a revisão independente por IA. Cada artefato deve incluir o
SHA-256 do relatório e fontes com domínio oficial, edição/validade, data de
consulta, localizador exato e IDs das alegações cobertas.

```json
[
  {
  "case_id": "MAIZE-001",
    "response_type": "answer",
    "factually_correct": true,
    "source_supported": true,
    "scope_correct": true,
    "critical_error": false
  },
  {
    "case_id": "MAIZE-002",
    "response_type": "abstain",
    "abstention_correct": true
  }
]
```

```bash
python tests/agronomic_benchmark.py tests/agronomic_gold_set.json test-results/agronomic-reviews.json
```

O resultado fica `not_evaluable` enquanto o conjunto-ouro estiver vazio ou o
limite mínimo de cobertura não tiver sido acordado. O alvo de 95% só passa com
o limite inferior unilateral exato de confiança de 95% para a precisão também
acima do alvo, além de cobertura suficiente e zero erros críticos. Com zero
falhas, são necessários ao menos 59 casos substantivos distintos para que esse
limite inferior alcance 95%; variações quase idênticas não devem contar como
casos independentes.

Ao final, compare os artefatos dos agentes com
`tests/verify_agronomist_reviews.py`. Os resultados são `behavioral_only`,
`agent_agreement_official_sources` ou `contested_or_insufficient_evidence`.
Nenhum exige aprovação de agrônomo humano nesta etapa. Mesmo o acordo contra fontes oficiais comprova
somente aquelas alegações e aquele escopo; não representa certificação nem
precisão global de 95%. O validador determinístico de domínio não autentica o
conteúdo do documento — essa checagem é responsabilidade de cada agente e deve
ser rastreável em cada parecer. Citações diferentes entre buscas independentes
ficam registradas como variações de evidência; divergência de julgamento, escopo,
suporte ou erro crítico mantém o caso bloqueado.

## Executar

```bash
python tests/run_golden_set.py --batch 1
python tests/run_golden_set.py
python tests/run_golden_set.py --report test-results/simulation-report.json
```

O runner avalia cada bateria para as quatro personas e submete cada transcrição
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
Android. Isso exige fontes verificadas por dois agentes independentes contra os
documentos oficiais e medições no aparelho-alvo.
As simulações existentes de hardware não substituem esses ensaios físicos.
