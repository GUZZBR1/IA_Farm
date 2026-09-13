import os
import requests
import json
from typing import List, Dict, Any, Optional
from tools.vector_db import LocalVectorDB

class Orchestrator:
    def __init__(self, vector_db_path: str = "data/vector_index/"):
        self.db = LocalVectorDB(index_path=vector_db_path)
        
        # API Configuration
        self.ollama_url = "http://localhost:11434/api/generate"
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        
        # Guided flow requirements
        self.required_metadata = ["region", "climate"]

    def _call_llm(self, prompt: str, model: str = "llama3") -> str:
        """Handles LLM calls with fallback from Ollama to OpenRouter."""
        # 1. Try Ollama (Local)
        try:
            response = requests.post(
                self.ollama_url,
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=15
            )
            if response.status_code == 200:
                return response.json().get("response", "")
        except Exception as e:
            print(f"[Log] Ollama unavailable: {e}")

        # 2. Fallback to OpenRouter
        if not self.openrouter_api_key:
            return "Error: LLM unavailable (Ollama offline and no OpenRouter key configured)."

        try:
            response = requests.post(
                self.openrouter_url,
                headers={"Authorization": f"Bearer {self.openrouter_api_key}"},
                json={
                    "model": "google/gemini-pro-1.5",
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error: All LLM providers failed. {e}"

        return "Error: Failed to get a response from LLM."

    def rag_query(self, query: str, context_filters: Dict[str, Any] = None) -> str:
        """RAG Loop: Query -> Vector Search -> Context Injection -> LLM"""
        # Load DNA for behavioral alignment
        dna_path = "docs/agent_dna.md"
        system_dna = ""
        if os.path.exists(dna_path):
            with open(dna_path, 'r') as f:
                system_dna = f.read()

        # Retrieval
        docs = self.db.query(query, filters=context_filters)
        context_text = "\n".join([d["text"] for d in docs])
        
        # Prompt Construction with DNA Integration
        prompt = f"""{system_dna}

Use the following technical context to answer the user's query. 
If the answer is not in the context, say you don't have enough technical data.

Context:
{context_text}

User Query: {query}
Answer:"""
        
        return self._call_llm(prompt)

    def handle_request(self, user_input: str, session_state: Dict[str, Any]) -> str:
        """Guided flow: Ensures region/climate are known before giving technical dosages."""
        # Check if the request is about technical/dosage advice
        technical_keywords = ["dosage", "amount", "how much", "apply", "treatment", "dose"]
        is_technical_request = any(kw in user_input.lower() for kw in technical_keywords)

        if is_technical_request:
            # Check for missing required metadata in session
            missing = [m for m in self.required_metadata if m not in session_state]
            
            if missing:
                return f"To provide an accurate dosage, I need more information. Please tell me your {', '.join(missing)}."

            # If we have the metadata, we can proceed with RAG
            filters = {m: session_state[m] for m in self.required_metadata}
            return self.rag_query(user_input, context_filters=filters)
        
        # For general queries, just use standard RAG without strict filters (or broad search)
        return self.rag_query(user_input)

def main():
    orch = Orchestrator()
    session_state = {}
    
    print("--- IA_Farm Guided Interface ---")
    print("Type 'exit' to quit.")
    
    while True:
        try:
            user_input = input("\nUser: ")
        except EOFError:
            break
            
        if user_input.lower() in ["exit", "quit"]:
            break
            
        # Simple state extraction for the guided flow (normally done via LLM or Form)
        # For the CLI test, we'll look for "region: X" or "climate: Y"
        for item in ["region", "climate"]:
            if f"{item}:" in user_input.lower():
                parts = user_input.lower().split(f"{item}:")
                value = parts[1].split(",")[0].strip().strip(".")
                session_state[item] = value
                print(f"[System] Registered {item} as {value}")

        response = orch.handle_request(user_input, session_state)
        print(f"AI: {response}")

if __name__ == "__main__":
    main()
