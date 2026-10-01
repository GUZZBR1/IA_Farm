# Context requirements (design input)

Status: **DESIGN ONLY**. This matrix describes fields observed in the 18 frozen maize candidate records and identifies gaps. It does not establish agronomic rules, required operating context, or approved answers. Every row still needs an explicit intent definition and qualified review before a Context Engine treats fields as required.

## Initial taxonomy

| Dimension | Present in current candidate records | Notes |
|---|---|---|
| `crop` | All 18 say `maize` | Frozen candidate metadata, not a user-confirmed value. |
| `region` / `state` / `municipality` | Region is `Brazil-MatoGrosso` throughout; state/municipality absent | Do not infer municipality from state. |
| `climate` | `Tropical` throughout | Unverified candidate metadata; not a current observation. |
| `season` | ZARC-001 has a placeholder; ZARC-002 lacks a season value | Exact planting window references require current season-specific source review. |
| `soil_analysis` | FERT-001 contains null | No analysis attached. |
| `soil_water_data`, `weather_data` | IRR-002 contains null | Inputs are absent; no irrigation calculation should be inferred. |
| `growth_stage` | Not explicitly supplied; phenology and water stress topics refer to stages | Current source hints do not establish a stage requirement. |
| `production_system` | PEST-005 says `monoculture` | Conflicts with the cited integrated-braquiaria source scope. |
| `symptoms`, `photo` | PEST-003 has `photo: null`; symptom text is in the question | An observation/photo is absent; no diagnosis may be inferred. |
| `area` | Not present | No area-based calculation is represented by the reviewed candidates. |
| `irrigation` | Topic signal in IRR-001/002; no current system value | Capture only if the reviewed intent needs it. |
| `previous_crop`, `analysis_data`, `cultivar`, `soil_type`, `expected_yield`, `grain_moisture`, `forecast` | Some appear as absent/null hints; otherwise absent | Collect only after a reviewed intent-specific requirement exists. |

## Candidate-to-context signals

The `candidate_fields` below reproduce current candidate context signals. `review_needed` means the product must ask a qualified reviewer to decide whether a field is required for the intent. It is not a request for the user to supply every listed field.

| Intent family (candidate ID) | Candidate fields/signals | Review-needed dimensions and gaps |
|---|---|---|
| Soil management (`SOIL-001`, `SOIL-002`) | crop, region, climate | applicability scope; field history/soil attributes only if source-backed intent requires them |
| Sowing/ZARC (`ZARC-001`, `ZARC-002`) | crop, region; season missing/placeholder | municipality, season, soil type, cultivar group: requirements must be resolved from the exact current ordinance and approved intent |
| Fertility (`FERT-001`) | crop, region, climate; `soil_analysis: null` | whether to abstain or request analysis; no rate/calculation label is supplied |
| Irrigation (`IRR-001`, `IRR-002`) | crop, region, climate; water/weather data absent | reviewed intent-specific weather, soil-water, system, stage, and area needs |
| Pest/disease evidence (`PEST-001..006`) | crop, region, climate; PEST-003 photo absent; PEST-005 system scope mismatch | observation details, stage, system, and regional applicability need human definition; do not infer diagnosis or product/dose |
| Phenology (`PHENOLOGY-001`) | crop, region, climate | requested stage/term and source scope; no stage-specific context requirement has been approved |
| Water sensitivity (`WATER-003`) | crop, region, climate | stage context and source identity remain disputed |
| Harvest (`HARVEST-001`, `HARVEST-002`) | crop, region, climate; forecast absent in 002 | intended question scope and relevant time context need review |
| Storage (`STORAGE-001`) | crop, region, climate; grain moisture absent | storage conditions and moisture context are unresolved, along with the candidate evidence itself |

## Context Engine contract for the next phase

For each reviewed intent, define `required_context`, `optional_context`, `freshness`, and `correction_behavior` independently. The engine should return `available_context`, `missing_context`, and a minimal clarification request. A later user correction replaces the same scoped fact and records provenance; stale memory is never treated as current automatically.

No generic form is defined. Current candidates do not justify making all taxonomy fields mandatory. Source acquisition and qualified review must first clarify the intent and its source-specific scope.
