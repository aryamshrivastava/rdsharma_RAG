import re
from dataclasses import dataclass
from typing import List, Optional

EXER_RE = re.compile(r"\bEXERCISE\s+(\d+(\.\d+)?)\b", re.IGNORECASE)
QNO_RE = re.compile(r"^\s*(?:Q\.?\s*)?(\d+)\s*[\.\)]\s+|^\s*Q\.?\s*(\d+)\b", re.IGNORECASE)
SOL_RE = re.compile(r"^\s*(SOLUTION|SOL\.|ANS\.|ANSWER)\b", re.IGNORECASE)

@dataclass
class Chunk:
    page_start: int
    page_end: int
    chunk_type: str
    title: str
    text: str

def _qno(line: str) -> Optional[str]:
    m = QNO_RE.match(line)
    if not m:
        return None
    return m.group(1) or m.group(2)

def split_pages_to_chunks(pages_text: List[str]) -> List[Chunk]:
    chunks: List[Chunk] = []
    current_ex = None
    current_q = None
    mode = "theory"
    buf = []
    pages = []

    def flush():
        nonlocal buf, pages, mode, current_ex, current_q
        if not buf:
            return
        text = "\n".join(buf).strip()
        if not text:
            buf, pages = [], []
            return
        ps, pe = min(pages), max(pages)
        if current_ex and current_q:
            title = f"Exercise {current_ex} Q{current_q}"
        elif current_ex:
            title = f"Exercise {current_ex}"
        else:
            title = "Content"
        chunks.append(Chunk(ps, pe, mode, title, text))
        buf, pages = [], []

    for i, raw in enumerate(pages_text, start=1):
        for line in (raw or "").splitlines():
            m_ex = EXER_RE.search(line)
            if m_ex:
                flush()
                current_ex = m_ex.group(1)
                current_q = None
                mode = "theory"
                buf.append(line); pages.append(i)
                continue

            qn = _qno(line)
            if qn:
                flush()
                current_q = qn
                mode = "question"
                buf.append(line); pages.append(i)
                continue

            if SOL_RE.match(line):
                flush()
                mode = "solution"
                buf.append(line); pages.append(i)
                continue

            buf.append(line); pages.append(i)

    flush()
    return chunks

def merge_question_with_solution(chunks: List[Chunk]) -> List[Chunk]:
    out: List[Chunk] = []
    i = 0
    while i < len(chunks):
        c = chunks[i]
        if c.chunk_type == "question" and i + 1 < len(chunks):
            nxt = chunks[i + 1]
            if nxt.chunk_type == "solution" and len(nxt.text) > 80:
                merged = c.text.strip() + "\n\n" + nxt.text.strip()
                out.append(Chunk(
                    page_start=min(c.page_start, nxt.page_start),
                    page_end=max(c.page_end, nxt.page_end),
                    chunk_type="mixed",
                    title=c.title,
                    text=merged
                ))
                i += 2
                continue
        out.append(c)
        i += 1
    return out
