import numpy as np
from sentence_transformers import SentenceTransformer
from .config import EMBED_MODEL_NAME

_model = None

def get_embedder():
    global _model
    if _model is None:
        print("[embedder] using device: cpu")
        _model = SentenceTransformer(EMBED_MODEL_NAME, device="cpu")
    return _model

def embed_texts(texts: list[str]) -> np.ndarray:
    model = get_embedder()
    emb = model.encode(
        texts,
        # The `batch_size` parameter in the `embed_texts` function is specifying the number of texts
        # to process in each batch during the embedding process. In this case, it is set to 8, meaning
        # that the texts will be processed in batches of 8. This can help improve efficiency and
        # memory usage during the embedding process.
        batch_size=5,
        normalize_embeddings=True,
        show_progress_bar=False,
        convert_to_numpy=True
    )
    return np.asarray(emb, dtype="float32")
