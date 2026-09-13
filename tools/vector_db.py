import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Tuple

class LocalVectorDB:
    def __init__(self, index_path: str = "data/vector_index/", model_name: str = "all-MiniLM-L6-v2"):
        self.index_path = index_path
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        
        os.makedirs(self.index_path, exist_ok=True)
        
        self.index_file = os.path.join(self.index_path, "faiss.index")
        self.metadata_file = os.path.join(self.index_path, "metadata.json")
        
        self.index = None
        self.metadata = []
        
        self._load_db()

    def _load_db(self):
        if os.path.exists(self.index_file) and os.path.exists(self.metadata_file):
            self.index = faiss.read_index(self.index_file)
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)

    def _save_db(self):
        if self.index is not None:
            faiss.write_index(self.index, self.index_file)
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunks.append(text[i:i + chunk_size])
        return chunks

    def index_documents(self, documents: List[Dict[str, Any]]):
        """
        documents: List of dicts with 'text' and optional 'metadata'
        """
        all_chunks = []
        all_metadata = []

        for doc in documents:
            text = doc.get("text", "")
            meta = doc.get("metadata", {})
            
            chunks = self.chunk_text(text)
            for chunk in chunks:
                all_chunks.append(chunk)
                all_metadata.append({**meta, "text": chunk})

        embeddings = self.model.encode(all_chunks)
        embeddings = np.array(embeddings).astype("float32")

        if self.index is None:
            self.index = faiss.IndexFlatL2(self.dimension)
        
        self.index.add(embeddings)
        self.metadata.extend(all_metadata)
        self._save_db()

    def query(self, query_text: str, k: int = 5, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        if self.index is None:
            return []

        query_vec = self.model.encode([query_text]).astype("float32")
        distances, indices = self.index.search(query_vec, k * 10) # Get more for filtering

        results = []
        for idx in indices[0]:
            if idx == -1 or idx >= len(self.metadata):
                continue
            
            meta = self.metadata[idx]
            if filters:
                if not all(meta.get(k) == v for k, v in filters.items()):
                    continue
            
            results.append(meta)
            if len(results) == k:
                break
                
        return results

if __name__ == "__main__":
    # Basic Test
    db = LocalVectorDB()
    
    test_docs = [
        {"text": "The IA Farm is a project for autonomous agricultural AI.", "metadata": {"category": "project"}},
        {"text": "FAISS is a library for efficient similarity search and clustering of dense vectors.", "metadata": {"category": "tech"}},
        {"text": "Sentence-Transformers provide state-of-the-art embeddings for sentences.", "metadata": {"category": "tech"}},
    ]
    
    print("Indexing documents...")
    db.index_documents(test_docs)
    
    print("\nQuerying: 'What is IA Farm?'")
    res = db.query("What is IA Farm?")
    print(res)
    
    print("\nQuerying: 'tech' category only, 'What are embeddings?'")
    res_filtered = db.query("What are embeddings?", filters={"category": "tech"})
    print(res_filtered)
