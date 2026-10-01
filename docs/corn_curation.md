# Corn Curation for IA_Farm Knowledge Base

> **DESIGN / HISTORICAL SOURCE LEADS — NOT APPROVED KNOWLEDGE.** URLs below are references, not ingested source snapshots. Do not index these notes or treat their contents as agronomic recommendations. Current promotion policy requires exact retained source bytes, source locator/scope, independent review artifacts and explicit qualified human agronomic approval; see `/GOLDEN_SET_POLICY.md` and `/KNOWLEDGE_PIPELINE.md`.

This document contains a curated list of high-quality resources for corn cultivation, focusing on reliable agricultural research institutions like EMBRAPA.

## 🌽 Core Cultivation & Management (EMBRAPA & Reliable Sources)

### EMBRAPA (Brazilian Agricultural Research Corporation)
EMBRAPA is the primary source for tropical and subtropical corn production.
- **Embrapa Milho e Sorgo**: The main hub for corn and sorghum research.
  - [Embrapa Maize and Sorghum Portal](https://www.embrapa.br/milho-e-sorgo)
- **Technical Manuals (Search terms for PDF acquisition)**:
  - `Sistema de Produção de Milho` (Corn Production System)
  - `Manejo Integrado de Pragas do Milho` (Integrated Pest Management for Corn)
  - `Adubação e Calagem do Milho` (Fertilization and Liming for Corn)

### International Sources
- **FAO (Food and Agriculture Organization)**: General guidelines for maize production in developing countries.
  - [FAO Maize Production](https://www.fao.org/agriculture/crops/en/)
- **CIMMYT (International Maize and Wheat Improvement Center)**: Global leader in maize genetics and sustainable intensification.
  - [CIMMYT Maize Resources](https://www.cimmyt.org/)

## 🐛 Pest and Disease Control
- **Integrated Pest Management (IPM)**: Look for EMBRAPA's "Manejo Integrado de Pragas" (MIP) guides.
- **Focus areas**:
  - *Spodoptera frugiperda* (Fall Armyworm) control.
  - Maize rust and leaf blight management.

## 🧪 Fertilization & Dosage
- **Soil Analysis**: Manuals on soil correction (calagem) and nutrient requirements (NPK).
- **Precision Agriculture**: Dosage maps and variable rate application guides.

## Candidate sources and review gate

Initial source-backed question drafts are recorded in
`tests/agronomic_gold_candidates.json`. They are research leads only; none is
approved for the runtime or the precision score. The register records source
URLs and retrieval date, and flags old or dynamically updated material for
freshness review.

- Embrapa, *Cultivo do Milho — Manejo de solos* (9th edition, 2015):
  <https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/749082/1/Milho-Manejo-de-solos.pdf>
- MAPA, ZARC portarias: annual, crop/state-specific references whose sowing
  windows depend on municipality, soil category, risk level and cultivar group:
  <https://www.gov.br/agricultura/pt-br/assuntos/riscos-seguro/programa-nacional-de-zoneamento-agricola-de-risco-climatico/portarias>
- Embrapa, maize irrigation reference: its publication date/version must be
  established before its numeric estimates are used:
  <https://ainfo.cnptia.embrapa.br/digital/bitstream/item/27341/1/Irrigacao-Manejo.pdf>
- MAPA, *Enfezamentos do milho* (page published 2021, updated 2023), for the
  vector/pathogen relationship, symptom descriptions and integrated-management
  framing:
  <https://www.gov.br/agricultura/pt-br/assuntos/sanidade-animal-e-vegetal/sanidade-vegetal/enfezamentos-do-milho>
- Embrapa, *Fisiologia da Produção de Milho* (Circular Técnica 76, 2006), for
  stage names and the context-dependent timing of development. Its age requires
  technical review before operational recommendations:
  <https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/490408/1/Circ76.pdf>
- Embrapa, *Cultivo do Milho — Colheita e pós-colheita* (5th electronic edition,
  2009), for broad maturity/harvest/storage concepts only; numeric operating
  limits require current review:
  <https://ainfo.cnptia.embrapa.br/digital/bitstream/item/82185/1/Colheita-pos-colheita.pdf>
- Embrapa, *Protocolos para experimentação, identificação, coleta e envio de
  amostras da cigarrinha Dalbulus maidis e de plantas com enfezamentos em milho*
  (2021), for sample and diagnostic workflow leads. Repository lists
  CC BY-NC-ND 4.0:
  <https://www.infoteca.cnptia.embrapa.br/handle/doc/1132039>
- Embrapa, *Manejo de lagarta-do-cartucho em sistemas de produção integrados
  com braquiária* (Comunicado Técnico 260, 2023). Its specific production-system
  scope and reuse terms must be checked before operational use:
  <https://ainfo.cnptia.embrapa.br/digital/bitstream/doc/1159228/1/Manejo-de-lagarta-do-cartucho-em-sistemas-de-producao-integrados.pdf>
- Embrapa, *Milho: o produtor pergunta, a Embrapa responde* (2nd edition, 2013),
  a broad source lead whose old recommendations require freshness review;
  repository lists CC BY-NC-ND 4.0:
  <https://www.infoteca.cnptia.embrapa.br/handle/doc/1124498>

Do not bulk-ingest search results or PDFs directly into production. Before a
source is used, record its edition/date and scope, check applicable reuse terms,
retain exact source bytes with a hash, verify precise locators and obtain the
required independent reviews plus explicit qualified human approval. Conflicts,
stale versions, missing scope, or unsupported claims remain pending and cannot
enter the offline knowledge index.
