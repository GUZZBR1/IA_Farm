"""Safe orchestration between metadata, retrieval and local/remote LLMs."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from tools.metadata import canonicalize
from tools.vector_db import LocalVectorDB


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NO_CONTEXT_RESPONSE = (
    "I do not have validated technical data for this query and context. "
    "Please provide the region, climate and crop details."
)
LLM_UNAVAILABLE_RESPONSE = (
    "The language model is unavailable. Start Ollama or configure "
    "OPENROUTER_API_KEY before retrying."
)
TECHNICAL_KEYWORDS = (
    "dosage", "dose", "amount", "how much", "quanto", "quantidade", "kg/ha",
    "l/ha", "apply", "aplicar", "treatment", "tratamento", "fertilizer", "adubo",
    "fertilizante", "pesticide", "pesticida", "fungicide", "fungicida", "npk",
)
REGION_ALIASES = (
    "mato grosso", "mt", "cerrado", "minas gerais", "mg", "parana", "pr",
    "sao paulo", "sp", "bahia", "ba",
)
CLIMATE_ALIASES = (
    "tropical", "equatorial", "semiarido", "semi-arido", "subtropical",
    "temperate", "temperado", "arid", "arido",
)


class Orchestrator:
    def __init__(self, vector_db_path: Optional[str] = None, db=None):
        default_index_path = PROJECT_ROOT / "data" / "vector_index"
        self.db = db if db is not None else LocalVectorDB(
            index_path=str(vector_db_path or default_index_path)
        )
        self.ollama_url = "http://localhost:11434/api/generate"
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.required_metadata = ["region", "climate"]

    def _call_llm(self, prompt: str, model: str = "llama3") -> str:
        """Call Ollama first and use OpenRouter only as an explicit fallback."""

        try:
            import requests
        except ImportError:
            return "Error: requests is not installed; install requirements.txt first."

        try:
            response = requests.post(
                self.ollama_url,
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=15,
            )
            if response.status_code == 200:
                return response.json().get("response", "")
        except Exception as exc:
            print(f"[Log] Ollama unavailable: {exc}")

        if not self.openrouter_api_key:
            return LLM_UNAVAILABLE_RESPONSE

        try:
            response = requests.post(
                self.openrouter_url,
                headers={"Authorization": f"Bearer {self.openrouter_api_key}"},
                json={
                    "model": "google/gemini-pro-1.5",
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30,
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
        except Exception as exc:
            print(f"[Log] OpenRouter unavailable: {exc}")

        return LLM_UNAVAILABLE_RESPONSE

    def _extract_metadata(self, user_input: str) -> Dict[str, str]:
        """Extract only explicit, deterministic region/climate mentions."""

        normalized = user_input.casefold()
        extracted: Dict[str, str] = {}
        for alias in REGION_ALIASES:
            if alias in normalized:
                extracted["region"] = canonicalize("region", alias)
                break
        for alias in CLIMATE_ALIASES:
            if alias in normalized:
                extracted["climate"] = canonicalize("climate", alias)
                break
        return extracted

    def rag_query(self, query: str, context_filters: Optional[Dict[str, Any]] = None) -> str:
        """Retrieve validated context before constructing an LLM prompt."""

        dna_path = PROJECT_ROOT / "docs" / "agent_dna.md"
        system_dna = dna_path.read_text(encoding="utf-8") if dna_path.exists() else ""
        docs = self.db.query(query, filters=context_filters)
        if not docs:
            return NO_CONTEXT_RESPONSE

        context_text = "\n".join(document.get("text", "") for document in docs)
        if not context_text.strip():
            return NO_CONTEXT_RESPONSE

        prompt = f"""{system_dna}

Use the following technical context to answer the user's query.
If the answer is not in the context, say you don't have enough technical data.

Context:
{context_text}

User Query: {query}
Answer:"""
        return self._call_llm(prompt)

    def handle_request(self, user_input: str, session_state: Dict[str, Any]) -> str:
        """Require region and climate before technical recommendations."""

        session_state.update(self._extract_metadata(user_input))
        normalized_input = user_input.casefold()
        is_technical_request = any(keyword in normalized_input for keyword in TECHNICAL_KEYWORDS)

        if not is_technical_request:
            return self.rag_query(user_input)

        normalized_state = {
            key: canonicalize(key, value)
            for key, value in session_state.items()
        }
        missing = [key for key in self.required_metadata if not normalized_state.get(key)]
        if missing:
            return (
                "To provide an accurate dosage, I need more information. "
                f"Please tell me your {', '.join(missing)}."
            )

        filters = {key: normalized_state[key] for key in self.required_metadata}
        return self.rag_query(user_input, context_filters=filters)


def main() -> None:
    orch = Orchestrator()
    session_state: Dict[str, Any] = {}
    print("--- IA_Farm Guided Interface ---")
    print("Type 'exit' to quit.")

    while True:
        try:
            user_input = input("\nUser: ")
        except EOFError:
            break

        if user_input.casefold() in {"exit", "quit"}:
            break

        response = orch.handle_request(user_input, session_state)
        print(f"AI: {response}")


if __name__ == "__main__":
    main()
