import numpy as np
from .indexer import load_faiss

class Retriever:
    def __init__(self):
        self.index, self.meta = load_faiss()

    def search(self, query_vec: np.ndarray, top_k: int = 20):
        q = query_vec.reshape(1, -1).astype("float32")
        scores, ids = self.index.search(q, top_k)
        hits = []
        for score, idx in zip(scores[0], ids[0]):
            if idx == -1:
                continue
            hits.append({"score": float(score), "chunk_id": int(self.meta["ids"][idx])})
        return hits
