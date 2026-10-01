# Agentes de revisão agronômica baseada em evidências oficiais

O **Especialista de Evidências Agronômicas** é um agente de IA com foco em
fontes para milho no Brasil. Ele
decompõe respostas em alegações verificáveis, pesquisa fontes oficiais e registra
o suporte, o escopo e as limitações de cada alegação. O **Verificador** repete a
pesquisa de forma independente e tenta refutar o primeiro parecer. Nenhum dos
dois é uma pessoa ou profissional licenciado: a conclusão significa apenas
“revisado por agentes contra as fontes citadas”, não certificação profissional.

Não há gate obrigatório de validação por agrônomo humano. Quando as fontes não
resolvem uma pergunta ou os agentes divergem, o resultado é concluído como
`unverifiable`, `unsupported`, `contested` ou `critical_risk`; o produto deve se
abster/bloquear aquela resposta, e não inventar uma aprovação.

## Fluxo

1. Congele o pacote de casos ou relatório de execução; calcule SHA-256 para
   vincular os dois pareceres à mesma entrada e versão do produto.
2. O Especialista enumera alegações atômicas e consulta fontes oficiais
   primárias relevantes, buscando a edição vigente e a aplicação exata ao caso.
3. O Verificador primeiro forma seu próprio parecer sem ler o do Mestre; depois
   recebe esse parecer e procura ressalvas, contradições, incompatibilidade de
   contexto e fontes oficiais mais atuais.
4. Compare os JSONs com `tests/verify_agronomist_reviews.py`. O comparador checa
   julgamento, base da evidência e consistência. Como as buscas são independentes,
   fontes/localizadores diferentes são listados em `source_variations`; diferença
   de citação sozinha não é conflito de julgamento. Cada agente ainda deve provar
   separadamente suas próprias fontes e localizadores.
5. Concordância com evidência oficial localizada permite concluir
   `agent_agreement_official_sources`; divergência, falta de fonte ou risco
   crítico conclui a execução como `contested_or_insufficient_evidence`. Não há
   etapa obrigatória de aprovação humana.
6. Mantenha separado o resultado de simulação (`behavioral_only`) da análise de
   respostas substantivas baseada em fontes. Personas e fixtures sintéticas não
   validam fatos sobre a lavoura.

## Hierarquia e registro das fontes

Priorize, conforme a pergunta: atos e bases regulatórias atuais do MAPA/DOU;
bases oficiais específicas como ZARC e AGROFIT; publicações técnicas da Embrapa
e de órgãos estaduais de pesquisa/extensão; e, como complemento quando as fontes
oficiais não cobrirem a questão, literatura científica identificada como tal.
Busca na web serve para localizar a fonte; páginas secundárias não substituem o
documento primário. Não trate uma publicação antiga como vigente sem conferir
atualização, safra e revogações.

Para cada fonte registrar: URL HTTPS oficial, título, entidade, tipo de fonte,
edição/ato/safra e datas de publicação/atualização/consulta; para PDFs, SHA-256;
para bases dinâmicas, parâmetros e data da consulta. Para cada alegação, guardar
`claim_id`, trecho ou paráfrase de suporte, página/seção/tabela/registro exato,
escopo (cultura, estado/município, safra/época, sequeiro/irrigado, solo, cultivar
e estádio conforme pertinência) e relação da evidência (`supports`, `contradicts`,
`qualifies` ou `not_found`). Citação à página inicial de um sistema, sem o registro
específico consultado, não valida uma dose ou indicação de produto.

Para defensivos, conferir o produto comercial, cultura, alvo, dose, condições e
restrições na consulta atual do AGROFIT/registro e na bula aplicável; presença no
cadastro não valida uma indicação fora desse escopo. Para ZARC, a safra, estado,
município, época, grupo de cultivar, classe de água disponível no solo e nível de
risco fazem parte da alegação — não há janela universal de plantio.

### Exemplo de fonte oficial já consultada

Na consulta de 29/09/2026, a página vigente do MAPA para Mato Grosso listava a
Portaria SPA/MAPA nº 326, de 28/07/2026, para milho de 2ª safra no ano-safra
2026/2027. O próprio art. 1º limita a vigência à safra indicada; o anexo define
grupos de ciclo, classes de água disponível e períodos de semeadura. Portanto,
essa portaria pode embasar alegações do seu escopo específico, mas não uma
recomendação geral para outro estado, safra ou modalidade. [Portaria oficial
(PDF)](https://www.gov.br/agricultura/pt-br/assuntos/riscos-seguro/programa-nacional-de-zoneamento-agricola-de-risco-climatico/portarias/safra-vigente/mato-grosso/POC4001.PDF).

A página oficial do [AGROFIT](https://www.gov.br/agricultura/pt-br/assuntos/insumos-agropecuarios/insumos-agricolas/agrotoxicos/agrofit)
descreve a base de produtos registrados e dá acesso à consulta pública; uma
alegação sobre dose ou indicação ainda exige o registro/bula do produto,
cultura e alvo específicos. A [Embrapa, em sua referência sobre relações do
milho com o solo](https://www.embrapa.br/web/agencia-de-informacao-tecnologica/cultivos/milho/pre-producao/caracteristicas-da-especie-e-relacoes-com-o-ambiente/relacoes-com-o-solo),
destaca o contexto solo-clima; isso reforça que a validação precisa carregar o
contexto, não apenas comparar uma resposta a um texto genérico. As páginas de
entrada são exemplos de descoberta: para fechar qualquer caso, os agentes devem
registrar o documento/consulta e o localizador que efetivamente sustenta a
alegação.

O comparador exige cobertura idêntica e SHA-256 igual do relatório congelado,
classificações explícitas, fontes em domínios oficiais permitidos e localização
precisa vinculada a `claim_ids`. Avaliações puramente comportamentais podem usar
`behavioral_contract` sem citação agronômica, e casos sem base suficiente devem
usar `unavailable`. O comparador verifica estrutura, domínio e consistência; não
baixa nem autentica o documento e não substitui a leitura crítica feita pelos
dois agentes. Concordância entre agentes é evidência documental auditada, não
certificação profissional nem prova estatística da precisão global.

## Instrução para o agente Agrônomo Mestre

> Você é o agente Agrônomo Mestre do IA_Farm, especializado em milho no Brasil.
> Leia o relatório fixado e avalie cada resposta, recusa e alegação material.
> Quebre respostas compostas em `claim_id`s. Pesquise na web, priorizando MAPA,
> DOU, Embrapa e órgãos oficiais competentes; abra o ato/documento/base original,
> confira versão e vigência e registre URL, entidade, título, data e localizador
> exato (página, seção, tabela ou parâmetros/registro). Para cada alegação,
> classifique suporte, contradição, ressalva ou ausência de evidência e confirme
> cultura, região, safra e condições aplicáveis. Não extrapole nem complete uma
> dose por conhecimento geral. Marque como `unsupported`/`unverifiable` quando
> a evidência não sustentar a resposta, e `critical_risk` para orientação
> potencialmente danosa. Diferencie fatos sustentados de sua própria inferência.
> Não declare certificação profissional. Retorne JSON; inclua hash do relatório.

## Instrução para o agente Verificador independente

> Seja independente: primeiro examine o mesmo relatório fixado e forme seus
> próprios julgamentos, consultando as fontes oficiais sem ler o parecer do
> Mestre. Em seguida, compare com as alegações e fontes do Mestre e tente
> refutá-las: confira versão/vigência, localizador, unidade, população/contexto,
> ressalvas e fontes oficiais contrárias ou mais atuais. Gere a mesma lista de
> IDs e o mesmo hash de relatório. Não ajuste resultado para concordar nem use
> consenso como prova. Registre `contested`, `unsupported`, `unverifiable` ou
> `critical_risk` quando aplicável; essa é uma conclusão fechada de bloqueio ou
> abstenção, sem dependência de validador humano. Retorne JSON.

## Formato de cada avaliação

```json
{
  "reviewer_role": "maize_evidence_specialist",
  "run_report": "test-results/latest-simulation-report.json",
  "run_report_sha256": "<64 caracteres hexadecimais do arquivo congelado>",
  "reviews": [
    {
      "review_id": "battery-001:professional",
      "verdict": "correct",
      "evidence_basis": "primary_source",
      "source_supported": true,
      "scope_correct": true,
      "critical_error": false,
      "rationale": "Resumo curto comparando a resposta ao contexto e à evidência.",
      "sources": [
        {
          "url": "https://www.gov.br/agricultura/pt-br/assuntos",
          "title": "Título do documento",
          "publisher": "Órgão oficial",
          "source_type": "official_research",
          "edition_or_validity": "Edição/ato/safra aplicável",
          "accessed_at": "AAAA-MM-DD",
          "locator": "Seção 2, página 14, tabela 3",
          "evidence": "Paráfrase curta de como a passagem sustenta claim-001",
          "claim_ids": ["claim-001"]
        }
      ]
    }
  ]
}
```

Valores de `verdict`: `correct`, `partially_correct`, `incorrect`, `unsupported`,
`unsafe`, `appropriate_abstention`, `inappropriate_abstention` ou
`unverifiable`. A função de papel do Verificador é `independent_verifier`;
`evidence_basis` aceita `primary_source`, `behavioral_contract` ou `unavailable`.
Só uma alegação substantiva sustentada por fonte com localizador oficial preciso
pode ser marcada como validada por evidência. O comparador checa formato e
concordância, não acessa nem autentica a fonte; a leitura e interpretação ficam
com os dois agentes. Não chame uma taxa de concordância ou suporte documental de
“precisão agronômica” ou certificação.

```bash
python tests/verify_agronomist_reviews.py \
  test-results/agronomist-master-agent-review.json \
  test-results/agronomist-independent-verifier-review.json \
  --output test-results/agronomist-review-comparison.json
```
