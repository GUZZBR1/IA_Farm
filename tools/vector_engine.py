
import faiss
import numpy as np
import pickle
import os
import requests
import json

class VectorEngine:
    def __init__(self, api_key, index_path="/var/tmp/ia_farm_data/vector_index"):
        self.api_key = api_key
        self.index_path = index_path
        self.index = None
        self.metadata = []
        self._load_index()

    def _get_embedding(self, text):
        # Using OpenRouter for embeddings to avoid local Torch dependency
        url = "https://openrouter.ai/api/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "openai/text-embedding-3-small",
            "input": text
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            resp.raise_for_status()
            return resp.json()['data'][0]['embedding']
        except Exception as e:
            print(f"Embedding API Error: {e}")
            return None

    def _load_index(self):
        if os.path.exists(f"{self.index_path}.index"):
            self.index = faiss.read_index(f"{self.index_path}.index")
            with open(f"{self.index_path}.meta", "rb") as f:
                self.metadata = pickle.load(f)
        else:
            self.index = None

    def add_documents(self, documents):
        embeddings = []
        valid_metadata = []
        for doc in documents:
            emb = self._get_embedding(doc['text'])
            if emb:
                embeddings.append(emb)
                valid_metadata.append(doc['metadata'])
        
        if not embeddings:
            return

        emb_array = np.array(embeddings).astype('float32')
        dim = emb_array.shape[1]
        if self.index is None:
            self.index = faiss.IndexFlatL2(dim)
        
        self.index.add(emb_array)
        self.metadata.extend(valid_metadata)
        self.save()

    def save(self):
        if self.index:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            faiss.write_index(self.index, f"{self.index_path}.index")
            with open(f"{self.index_path}.meta", "wb") as f:
                pickle.dump(self.metadata, f)

    def search(self, query, k=3):
        if self.index is None:
            return []
        query_emb = self._get_embedding(query)
        if query_emb is None:
            return []
        distances, indices = self.index.search(np.array([query_emb]).astype('float32'), k)
        results = []
        for i in indices[0]:
            if i != -1 and i < len(self.metadata):
                results.append(self.metadata[i])
        return results
