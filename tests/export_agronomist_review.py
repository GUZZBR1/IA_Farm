"""Create an evidence packet for the independent maize-review agents."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def render_packet(candidate_set: dict[str, Any]) -> str:
    if candidate_set.get("status") != "draft_not_for_scoring":
        raise ValueError("refusing to export a candidate set not marked draft_not_for_scoring")

    sources = {source["id"]: source for source in candidate_set.get("sources", [])}
    cases = candidate_set.get("cases", [])
    if not cases:
        raise ValueError("candidate set has no cases")

    lines = [
        "# Revisão agronômica — candidatos de benchmark de milho",
        "",
        "> Material de pesquisa para os dois agentes de revisão; não é recomendação nem conjunto-ouro.",
        "> Cada agente deve abrir a fonte primária, conferir escopo/vigência e registrar evidências separadamente.",
        "",
        f"Casos: {len(cases)} | Consultado em: {candidate_set.get('retrieved_at', 'não informado')}",
        "",
        "## Procedimento dos agentes",
        "",
        "Para cada caso, o Agrônomo Mestre e o Verificador devem trabalhar independentemente.",
        "Abram a fonte original, confiram versão/vigência, contexto, suporte de cada alegação,",
        "ressalvas e evidência contrária. Registrem URLs oficiais, localizadores precisos,",
        "datas e IDs de alegação nos JSONs. Divergência ou evidência insuficiente bloqueia",
        "o caso; não há aprovação humana obrigatória nem promoção por consenso sem evidência.",
        "Identifiquem conceitos dependentes; não contem paráfrases do mesmo fato como",
        "amostras independentes.",
        "",
        "Este pacote não aprova casos nem altera a base de conhecimento. O status de cada",
        "caso é decidido pelo fluxo de curadoria controlado, com ambos os relatórios e",
        "evidências rastreáveis; os candidatos não são automaticamente gabaritos de verdade.",
        "",
    ]

    for case in cases:
        lines.extend([
            f"## {case['id']}",
            "",
            f"**Pergunta:** {case['question']}",
            "",
            f"**Contexto:** `{json.dumps(case.get('context', {}), ensure_ascii=False, sort_keys=True)}`",
            "",
            f"**Respondível (hipótese):** {case.get('answerable_candidate', 'não informado')}",
            "",
            "**Alegações candidatas — conferir individualmente:**",
            "",
        ])
        claims = case.get("candidate_claims", [])
        lines.extend([f"- [ ] {claim}" for claim in claims] or ["- (nenhuma; candidato a abstenção)"])
        lines.extend(["", "**Ressalvas candidatas:**", ""])
        lines.extend([f"- [ ] {item}" for item in case.get("required_caveats", [])] or ["- (nenhuma registrada)"])
        lines.extend(["", "**Fontes primárias:**", ""])
        for source_id in case.get("source_ids", []):
            source = sources.get(source_id)
            if not source:
                lines.append(f"- ERRO: fonte sem cadastro `{source_id}`")
                continue
            published = source.get("published_at") or source.get("publication_date") or "data não estabelecida"
            if source.get("updated_at"):
                published += f"; atualização {source['updated_at']}"
            lines.extend([
                f"- **{source.get('publisher', 'Editora não informada')} — {source.get('title', source_id)}** ({published})",
                f"  - URL: {source.get('url', 'não informada')}",
                f"  - Evidência/localização indicada: {source.get('evidence_locations', 'não informada')}",
            ])
            if source.get("source_age_review_required"):
                lines.append("  - [ ] Confirmar atualidade e aplicabilidade antes de aprovar.")
            if source.get("license_note"):
                lines.append(f"  - Nota de licença: {source['license_note']}")
        lines.extend([
            "",
            "**Saída esperada de cada agente (no respectivo JSON):**",
            "",
            "- Veredito e base da evidência para cada alegação:",
            "  -",
            "- URLs oficiais, edição/validade, data de consulta e hash do documento quando aplicável:",
            "  -",
            "- Localizador exato (página/seção/tabela/registro) e relação com a alegação:",
            "  -",
            "- Escopo, limitações, evidência contrária e motivo para abstenção/bloqueio:",
            "  -",
            "- Casos dependentes (mesmo fato, fonte ou variação superficial):",
            "  -",
            "- Grupo independente sugerido (único por conceito avaliado): ____________________",
            "- Justificativa/observações de cada agente:",
            "  -",
            "- Data de cada revisão (AAAA-MM-DD): ____________________",
            "",
            "---",
            "",
        ])

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidates",
        type=Path,
        default=Path(__file__).with_name("agronomic_gold_candidates.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("agronomist_review_packet.md"),
    )
    args = parser.parse_args()
    candidates = json.loads(args.candidates.read_text(encoding="utf-8"))
    packet = render_packet(candidates)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(packet, encoding="utf-8")
    print(f"Wrote {len(candidates['cases'])} pending review cases to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
