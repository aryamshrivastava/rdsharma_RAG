from sentence_transformers import CrossEncoder
import re

_reranker = None

def extract_numbers(s: str):
    return set(re.findall(r"\b\d+\b", s or ""))

def numeric_overlap_score(query: str, text: str) -> float:
    qn = extract_numbers(query)
    if not qn:
        return 0.0
    tn = extract_numbers(text)
    if not tn:
        return 0.0
    return len(qn & tn) / max(1, len(qn))

def get_reranker():
    global _reranker
    if _reranker is None:
        print("[reranker] using device: cpu")
        _reranker = CrossEncoder("BAAI/bge-reranker-large", device="cpu")
    return _reranker

def rerank(query: str, candidates: list[dict], top_n: int = 5) -> list[dict]:
    if not candidates:
        return []

    # cap for speed
    candidates = candidates[:200]

    rr = get_reranker()
    pairs = [(query, c.get("text", "")) for c in candidates]
    scores = rr.predict(pairs)

    for c, s in zip(candidates, scores):
        c["rerank_score"] = float(s)

        # if SQL already set num_score=1.0 keep it, otherwise compute overlap
        if "num_score" not in c:
            c["num_score"] = numeric_overlap_score(query, c.get("text", ""))

        # heavy numeric weight for math books
        c["final_score"] = c["rerank_score"] + (5.0 * float(c["num_score"]))

    candidates.sort(key=lambda x: x["final_score"], reverse=True)
    return candidates[:top_n]
