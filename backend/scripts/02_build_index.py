import json
from pathlib import Path

import faiss
from tqdm import tqdm

from rag.config import OCR_DIR
from rag.db import connect, insert_chunk
from rag.chunker import split_pages_to_chunks, merge_question_with_solution
from rag.embedder import embed_texts
from rag.indexer import save_faiss


def load_pages_text():
    files = sorted(OCR_DIR.glob("page_*.json"))
    if not files:
        raise SystemExit("No OCR files found. Run 01_ingest_pdf.py first.")

    pages = []
    for fp in files:
        data = json.loads(fp.read_text(encoding="utf-8"))
        pages.append((data["page"], data.get("text", "")))

    pages.sort(key=lambda x: x[0])
    return [t for _, t in pages]


def cap_text(t: str, max_chars: int = 4000) -> str:
    t = (t or "").strip()
    return t[:max_chars]


def main():
    pages_text = load_pages_text()
    print("Loaded pages:", len(pages_text))

    chunks = split_pages_to_chunks(pages_text)
    chunks = merge_question_with_solution(chunks)

    con = connect()
    con.execute("DELETE FROM chunks;")
    con.commit()

    source_pdf = "RD_Sharma_X.pdf"

    print("Writing chunks to SQLite...")
    for c in tqdm(chunks):
        if not c.text.strip():
            continue
        insert_chunk(
            con,
            source_pdf=source_pdf,
            page_start=c.page_start,
            page_end=c.page_end,
            chunk_type=c.chunk_type,
            title=c.title,
            text=c.text,
        )
    con.commit()

    # Index: mixed + solution only
    cur = con.execute(
        "SELECT id, text FROM chunks WHERE chunk_type IN ('mixed','solution')"
    )
    rows = cur.fetchall()

    ids = [r[0] for r in rows]
    texts = [cap_text(r[1], 4000) for r in rows]

    print(f"Embedding {len(texts)} chunks...")
    emb = embed_texts(texts)

    dim = emb.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(emb)

    save_faiss(index, {"ids": ids, "dim": dim})
    print("FAISS index saved. DONE.")


if __name__ == "__main__":
    main()
