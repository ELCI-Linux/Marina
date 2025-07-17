import os
import json
import time
import uuid
import numpy as np
from typing import List, Optional, Dict, Any

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None
    # You can implement a fallback using OpenAI embeddings or any other model

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

class AdvancedContextualMemory:
    def __init__(self, storage_path="memory_vectors.json", model_name="all-MiniLM-L6-v2"):
        self.storage_path = storage_path
        self.entries: List[Dict[str, Any]] = []
        self.model = None
        if SentenceTransformer is not None:
            self.model = SentenceTransformer(model_name)
        else:
            raise ImportError("sentence-transformers not installed. Please install it or provide embedding function.")
        self._load()

    def _load(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path, "r", encoding="utf-8") as f:
                self.entries = json.load(f)
            # Convert embeddings back to numpy arrays
            for e in self.entries:
                e["embedding"] = np.array(e["embedding"])

    def _save(self):
        # Convert embeddings to lists for JSON serialization
        to_save = []
        for e in self.entries:
            copy_entry = e.copy()
            copy_entry["embedding"] = copy_entry["embedding"].tolist()
            to_save.append(copy_entry)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(to_save, f, indent=2)

    def _embed_text(self, text: str) -> np.ndarray:
        if self.model:
            embedding = self.model.encode(text, normalize_embeddings=True)
            return embedding
        raise RuntimeError("No embedding model available")

    def add_entry(self, text: str, metadata: Optional[Dict[str, Any]] = None):
        entry_id = str(uuid.uuid4())
        embedding = self._embed_text(text)
        entry = {
            "id": entry_id,
            "text": text,
            "embedding": embedding,
            "metadata": metadata or {},
            "timestamp": time.time(),
        }
        self.entries.append(entry)
        self._save()
        return entry_id

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        query_emb = self._embed_text(query)
        scored = []
        for e in self.entries:
            score = cosine_similarity(query_emb, e["embedding"])
            scored.append((score, e))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [entry for score, entry in scored[:top_k]]
        return results

    def update_entry(self, entry_id: str, new_text: Optional[str] = None, new_metadata: Optional[Dict[str, Any]] = None):
        for e in self.entries:
            if e["id"] == entry_id:
                if new_text is not None:
                    e["text"] = new_text
                    e["embedding"] = self._embed_text(new_text)
                if new_metadata is not None:
                    e["metadata"].update(new_metadata)
                e["timestamp"] = time.time()
                self._save()
                return True
        return False

    def delete_entry(self, entry_id: str):
        before_len = len(self.entries)
        self.entries = [e for e in self.entries if e["id"] != entry_id]
        if len(self.entries) < before_len:
            self._save()
            return True
        return False

    def clear_memory(self):
        self.entries = []
        self._save()
