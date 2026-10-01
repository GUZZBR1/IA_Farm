import os
import json
from typing import List, Dict, Any

from tools.metadata import metadata_matches

class LocalVectorDB:
    def __init__(self, index_path: str = "data/vector_index/", model_name: str = "all-MiniLM-L6-v2"):
        try:
            import faiss
            import numpy as np
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "Vector DB dependencies are missing. Install requirements.txt first."
            ) from exc

        self.index_path = index_path
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        get_dimension = getattr(
            self.model,
            "get_embedding_dimension",
            self.model.get_sentence_embedding_dimension,
        )
        self.dimension = get_dimension()
        self._faiss = faiss
        self._np = np
        
        os.makedirs(self.index_path, exist_ok=True)
        
        self.index_file = os.path.join(self.index_path, "faiss.index")
        self.metadata_file = os.path.join(self.index_path, "metadata.json")
        
        self.index = None
        self.metadata = []
        
        self._load_db()

    def _load_db(self):
        index_exists = os.path.exists(self.index_file)
        metadata_exists = os.path.exists(self.metadata_file)
        if index_exists != metadata_exists:
            raise RuntimeError("Vector index is incomplete: index and metadata must exist together")

        if index_exists and metadata_exists:
            try:
                self.index = self._faiss.read_index(self.index_file)
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
            except (OSError, RuntimeError, ValueError, TypeError, json.JSONDecodeError) as exc:
                raise RuntimeError(f"Invalid vector index at {self.index_path}") from exc

            if self.index.ntotal != len(self.metadata):
                raise RuntimeError("Vector index and metadata have different sizes")

    def _save_db(self):
        if self.index is not None:
            self._faiss.write_index(self.index, self.index_file)
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
            raise ValueError("chunk_size must be positive and overlap must be smaller than chunk_size")

        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunks.append(text[i:i + chunk_size])
        return chunks

    def index_documents(self, documents: List[Dict[str, Any]], *, exact_documents: bool = False):
        """
        documents: List of dicts with 'text' and optional 'metadata'
        """
        if not documents:
            raise ValueError("At least one document is required to build the index")

        all_chunks = []
        all_metadata = []

        for doc in documents:
            text = doc.get("text", "")
            meta = doc.get("metadata", {})
            
            # Approved excerpts are indexed as the exact reviewed unit. The
            # published knowledge builder must not create unapproved chunks.
            chunks = [text] if exact_documents else self.chunk_text(text)
            for chunk in chunks:
                all_chunks.append(chunk)
                all_metadata.append({**meta, "text": chunk})

        if not all_chunks:
            raise ValueError("Documents must contain non-empty text")

        embeddings = self.model.encode(all_chunks)
        embeddings = self._np.array(embeddings).astype("float32")

        if self.index is None:
            self.index = self._faiss.IndexFlatL2(self.dimension)
        elif self.index.d != self.dimension:
            raise RuntimeError("Existing index dimension does not match the embedding model")
        
        self.index.add(embeddings)
        self.metadata.extend(all_metadata)
        self._save_db()

    def query(self, query_text: str, k: int = 5, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        if self.index is None or k <= 0:
            return []

        query_vec = self.model.encode([query_text]).astype("float32")
        results = []
        candidate_count = min(k * 10, self.index.ntotal)
        while candidate_count:
            distances, indices = self.index.search(query_vec, candidate_count)
            results = []
            for distance, idx in zip(distances[0], indices[0]):
                if idx == -1 or idx >= len(self.metadata):
                    continue
                meta = self.metadata[idx]
                if filters and not all(metadata_matches(key, meta.get(key), value)
                                       for key, value in filters.items()):
                    continue
                results.append({**meta, "retrieval_distance": float(distance)})
                if len(results) == k:
                    break
            if len(results) >= k or candidate_count >= self.index.ntotal:
                break
            candidate_count = min(candidate_count * 2, self.index.ntotal)
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
