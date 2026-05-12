import json
import faiss
from .config import FAISS_DIR, FAISS_INDEX_PATH, FAISS_META_PATH

def save_faiss(index, meta: dict):
    FAISS_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(FAISS_INDEX_PATH))
    with open(FAISS_META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

def load_faiss():
    index = faiss.read_index(str(FAISS_INDEX_PATH))
    with open(FAISS_META_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)
    return index, meta
