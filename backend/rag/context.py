# def build_book_context(top_chunks: list[dict]) -> str:
#     parts = []
#     for i, c in enumerate(top_chunks, start=1):
#         parts.append(
#             f"[Match {i}] {c['title']} (pages {c['pages'][0]}-{c['pages'][1]})\n"
#             f"{(c['text'] or '').strip()}"
#         )
#     return "\n\n---\n\n".join(parts).strip()


import json
import redis
from .config import REDIS_URL, SESSION_TTL, MAX_TURNS


# Redis client
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


# -------------------------------------------------
# Book context (UNCHANGED logic)
# -------------------------------------------------
def build_book_context(top_chunks: list[dict]) -> str:
    parts = []
    for i, c in enumerate(top_chunks, start=1):
        parts.append(
            f"[Match {i}] {c['title']} (pages {c['pages'][0]}-{c['pages'][1]})\n"
            f"{(c['text'] or '').strip()}"
        )
    return "\n\n---\n\n".join(parts).strip()


# -------------------------------------------------
# Session memory helpers
# -------------------------------------------------
def load_session(session_id: str) -> dict:
    data = redis_client.get(f"session:{session_id}")
    if not data:
        return {"summary": "", "turns": []}
    return json.loads(data)


def save_session(session_id: str, session: dict):
    redis_client.setex(
        f"session:{session_id}",
        SESSION_TTL,
        json.dumps(session)
    )


def update_session(session_id: str, question: str, answer: str):
    session = load_session(session_id)

    session["turns"].append({
        "q": question,
        "a": answer
    })

    # keep last N turns only
    session["turns"] = session["turns"][-MAX_TURNS:]

    save_session(session_id, session)


def build_chat_context(session: dict) -> str:
    parts = []

    if session.get("summary"):
        parts.append(f"Conversation so far:\n{session['summary']}")

    for t in session.get("turns", []):
        parts.append(f"Q: {t['q']}\nA: {t['a']}")

    return "\n\n".join(parts).strip()
