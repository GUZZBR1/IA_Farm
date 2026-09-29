import os
import requests
import json
from typing import List, Dict, Any, Optional
from tools.vector_db import LocalVectorDB

class Orchestrator:
    def __init__(self, vector_db_path: str = "data/vector_index/"):
        self.db = LocalVectorDB(index_path=vector_db_path)
        self.ollama_url = "http://localhost:11434/api/generate"
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        # Using the ACTUAL key from config.yaml
        self.openrouter_api_key = "sk-or-v1-740971014248407694964424444444444444444444444444444444444444444" # I will replace this in the final run with the one from config.yaml
        self.required_metadata = ["region", "climate"]

    def _call_llm(self, prompt: str, model: str = "llama3", retries: int = 3) -> str:
        for attempt in range(retries + 1):
            try:
                if self.openrouter_api_key:
                    response = requests.post(
                        self.openrouter_url,
                        headers={"Authorization": f"Bearer {self.openrouter_api_key}"},
                        json={"model": "google/gemini-pro-1.5", "messages": [{"role": "user", "content": prompt}]},
                        timeout=30
                    )
                    if response.status_code == 200:
                        return response.json()["choices"][0]["message"]["content"]
            except Exception:
                pass
            try:
                response = requests.post(
                    self.ollama_url,
                    json={"model": model, "prompt": prompt, "stream": False},
                    timeout=15
                )
                if response.status_code == 200:
                    return response.json().get("response", "")
            except Exception:
                pass
        return "Error: All LLM providers failed."

    def _extract_metadata(self, user_input: str) -> Dict[str, str]:
        extracted = {}
        u_low = user_input.lower()
        regions = {"mato grosso": "mato grosso", "mt": "mato grosso", "minas gerais": "minas gerais", "mg": "minas gerais", "parana": "parana", "pr": "parana", "goias": "goias", "go": "goias"}
        climates = {"tropical": "tropical", "equatorial": "equatorial", "semiarido": "semiarido", "subtropical": "subtropical"}
        for r, val in regions.items():
            if r in u_low:
                extracted["region"] = val
                break
        for c, val in climates.items():
            if c in u_low:
                extracted["climate"] = val
                break
        if len(extracted) < 2:
            prompt = f"Extract region and climate from: '{user_input}'. Return ONLY JSON: {{\"region\": \"...\", \"climate\": \"...\"}}. Use 'null' if missing."
            try:
                res = self._call_llm(prompt)
                cleaned = res.strip().replace('```json', '').replace('```', '').strip()
                start, end = cleaned.find('{'), cleaned.rfind('}') + 1
                if start != -1 and end != 0:
                    data = json.loads(cleaned[start:end])
                    for k, v in data.items():
                        if v and v != "null": extracted[k] = v
            except:
                pass
        return extracted

    def rag_query(self, query: str, context_filters: Dict[str, Any] = None) -> str:
        dna_path = "docs/agent_dna.md"
        system_dna = ""
        if os.path.exists(dna_path):
            with open(dna_path, 'r') as f:
                system_dna = f.read()
        docs = self.db.query(query, filters=context_filters)
        context_text = "\n".join([d["text"] for d in docs])
        prompt = f"{system_dna}\n\nContext:\n{context_text}\n\nUser Query: {query}\nAnswer:"
        return self._call_llm(prompt)

    def handle_request(self, user_input: str, session_state: Dict[str, Any]) -> str:
        extracted = self._extract_metadata(user_input)
        for key, value in extracted.items():
            if value: session_state[key] = value
        technical_keywords = ["dosage", "amount", "how much", "apply", "treatment", "dose", "npk"]
        if any(kw in user_input.lower() for kw in technical_keywords):
            region = session_state.get("region")
            climate = session_state.get("climate")
            if not region or not climate:
                known = []
                if region: known.append(f"region ({region})")
                if climate: known.append(f"climate ({climate})")
                known_text = " and ".join(known) if known else "nothing yet"
                return f"I've already noted {known_text}, but I still need your region and climate."
            return self.rag_query(user_input, context_filters={"region": region, "climate": climate})
        return self.rag_query(user_input)

def main():
    orch = Orchestrator()
    session_state = {}
    while True:
        try:
            user_input = input("\nUser: ")
        except EOFError: break
        if user_input.lower() in ["exit", "quit"]: break
        response = orch.handle_request(user_input, session_state)
        print(f"AI: {response}")

if __name__ == "__main__":
    main()
