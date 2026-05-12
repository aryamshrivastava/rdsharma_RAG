import os
import re
import tempfile
import base64
import logging
from uuid import uuid4

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from rag.db import connect, fetch_chunk
from rag.embedder import embed_texts
from rag.retriever import Retriever
from rag.reranker import rerank
from rag.context import build_book_context
from rag.ocr import ocr_image
from rag.vlm_client import extract_question_and_diagram_fallback
from rag.llm_client import generate_step_by_step_fallback
from rag.answer import build_final_answer
from rag.geometry import enrich_context_with_geometry, detect_geometry_requirement

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="RD Sharma Tutor (RAG internal, tutor output only)")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ret = None 

@app.on_event("startup")
def startup():
    global ret
    try:
        ret = Retriever()
        logger.info("[Startup] Retriever initialized successfully")
    except Exception as e:
        ret = None
        logger.warning("[Startup] Retriever unavailable; running in LLM-only mode: %s", str(e))

@app.get("/health")
def health():
    return {"status": "ok"}


# -------------------------------------------------
# HYBRID RAG + LLM LOGIC
# -------------------------------------------------
def retrieve_rd_sharma_context(question: str, top_k: int = 5) -> tuple[str, bool]:
    """
    Hybrid retrieval: Check if question is RAG-relevant.
    Uses the main retrieve_book_context function instead.
    
    Returns:
        (context: str, is_rag_relevant: bool)
        - If RAG relevant: returns formatted context + True
        - If not RAG relevant: returns "" + False
    """
    # Use the main function which has proper threshold checks
    context = retrieve_book_context(question)
    is_relevant = bool(context and context.strip())
    return context, is_relevant


# -------------------------------------------------
# Session Management (In-memory storage)
# -------------------------------------------------
sessions = {}

def load_session(session_id: str) -> list:
    """Load session history for a given session_id."""
    return sessions.get(session_id, [])

def update_session(session_id: str, question: str, answer: str):
    """Update session with new Q&A pair."""
    if session_id not in sessions:
        sessions[session_id] = []
    sessions[session_id].append({"question": question, "answer": answer})

def get_session_history(session_id: str) -> dict:
    """
    Return structured chat history for a session.

    This is useful for the frontend to render the complete
    conversation so far for a given user/session.
    """
    history = load_session(session_id)
    return {
        "session_id": session_id,
        "history": history,
    }

def build_chat_context(session: list) -> str:
    """Build context from session history"""
    if not session:
        return ""
    context = "\n\n".join([
        f"Q: {item['question']}\nA: {item['answer'][:500]}"  # Truncate for context
        for item in session[-3:]  # Keep last 3 exchanges
    ])
    return context


# -------------------------------------------------
# RD Sharma RAG retrieval helpers
# -------------------------------------------------

STOPWORDS = {
    "find", "the", "of", "a", "an", "and", "or", "to", "in", "on", "for",
    "with", "by", "is", "which", "that", "this", "these", "those", "from",
    "into", "at", "as", "it", "be", "are", "joining", "segment", "line",
    "point", "ratio", "internally", "externally", "divides", "divide",
    "dividing", "coordinates", "coordinate", "join", "joins", "between"
}


def normalize_minus(s: str) -> str:
    return (s or "").replace("−", "-").replace("–", "-").replace("—", "-")


def extract_numbers_signed(s: str):
    s = normalize_minus(s)
    return re.findall(r"(?<!\w)-?\d+", s)


def extract_keywords(s: str):
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9\s:-]", " ", s)
    words = [w for w in s.split() if len(w) >= 4 and w not in STOPWORDS]
    seen = set()
    out = []
    for w in words:
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out


def is_junk_chunk(title: str, page_end: int, query: str) -> bool:
    """
    Heuristic filter to avoid front-matter / contents pages unless explicitly asked.
    """
    q = (query or "").lower()
    t = (title or "").lower()

    # Filter early pages that look like contents unless the query asks for them
    if page_end <= 25:
        if (
            ("content" in t or t == "content")
            and not any(x in q for x in ("content", "preface", "isbn", "edition"))
        ):
            return True
        if any(x in q for x in ("isbn", "edition", "publisher")):
            return False
        if page_end <= 10:
            return True

    return False


def sql_numeric_candidates(con, query: str, limit: int = 30):
    """
    Fast numeric + keyword filter in SQLite to narrow down RD Sharma chunks.
    """
    nums = extract_numbers_signed(query)
    if not nums:
        return []

    kws = extract_keywords(query)

    where_nums = " AND ".join(["text LIKE ?"] * len(nums))
    params = [f"%{n}%" for n in nums]

    cur = con.execute(
        f"""
        SELECT id, title, page_start, page_end, chunk_type, text
        FROM chunks
        WHERE {where_nums}
        LIMIT {limit}
        """,
        params,
    )
    rows = cur.fetchall()

    out = []
    for r in rows:
        cid, title, ps, pe, ctype, text = r

        if is_junk_chunk(title, pe, query):
            continue

        # keyword filter: require at least 1 keyword match (if keywords exist)
        if kws:
            t = (text or "").lower()
            if not any(k in t for k in kws[:6]):
                continue

        out.append(
            {
                "chunk_id": cid,
                "title": title,
                "pages": [ps, pe],
                "chunk_type": ctype,
                "text": text,
            }
        )

    return out


def cap_context(ctx: str, max_chars: int = 2500) -> str:
    ctx = (ctx or "").strip()
    return ctx[:max_chars]


# Relevance thresholds for RAG mode selection (lowered for better performance)
FAISS_RELEVANCE_THRESHOLD = 0.25  # Minimum FAISS cosine similarity
RERANK_RELEVANCE_THRESHOLD = 0.15  # Minimum rerank score (cross-encoder)


def retrieve_book_context(query: str) -> str:
    """
    Try to retrieve RD Sharma book context for a question.

    If RELEVANT chunks are found (above threshold), returns a compact internal 
    context string (used only as reference for the LLM). If nothing relevant is found,
    returns an empty string so the LLM answers from its own knowledge (Qwen).
    
    Auto-enriches context with geometry information when detected.
    """
    query = (query or "").strip()
    if not query:
        return ""

    if ret is None:
        logger.info("[RAG] Retriever not initialized; using pure LLM mode")
        return ""

    con = connect()
    try:
        context = ""
        match_info = {"source": None, "score": 0.0}
        
        # 1) SQL numeric+keyword match first (fast, high precision)
        exact = sql_numeric_candidates(con, query, limit=30)
        if exact:
            # Require at least 2 keyword matches for relevance
            kws = extract_keywords(query)
            if len(kws) >= 2:
                # Check if chunks have sufficient keyword overlap
                relevant_chunks = []
                for chunk in exact[:5]:
                    text_lower = (chunk.get("text", "") or "").lower()
                    kw_matches = sum(1 for k in kws if k in text_lower)
                    if kw_matches >= 2:
                        relevant_chunks.append(chunk)
                
                if relevant_chunks:
                    context = cap_context(build_book_context(relevant_chunks[:3]), 2500)
                    match_info = {"source": "SQL", "score": 1.0}
                    logger.info("[RAG] Using SQL RD Sharma context (kw_matches=%d) for query: %s", 
                               kw_matches, query[:80])
            else:
                # Not enough keywords for reliable SQL match - skip to FAISS
                logger.info("[RAG] Skipping SQL match: only %d keywords found", len(kws))
        
        # 2) FAISS semantic retrieval + reranking (only if SQL didn't find relevant context)
        if not context:
            qv = embed_texts([query])[0]
            hits = ret.search(qv, top_k=60)

            candidates = []
            seen = set()

            for h in hits:
                # Filter by FAISS similarity threshold
                if h["score"] < FAISS_RELEVANCE_THRESHOLD:
                    continue  # Skip low-similarity chunks early
                
                c = fetch_chunk(con, h["chunk_id"])
                if not c:
                    continue
                cid = c["id"]
                if cid in seen:
                    continue
                seen.add(cid)

                candidates.append(
                    {
                        "chunk_id": cid,
                        "title": c["title"],
                        "pages": [c["page_start"], c["page_end"]],
                        "chunk_type": c["chunk_type"],
                        "text": c["text"],
                        "faiss_score": h["score"],
                    }
                )

            # rerank small set for relevance
            candidates = candidates[:30]
            
            # OPTIMIZATION: Skip reranker if top FAISS score is already good (>= 0.50)
            # Reranker is slow on CPU - only use it for borderline cases
            top_faiss_score = candidates[0].get("faiss_score", 0) if candidates else 0
            
            if top_faiss_score >= 0.50:
                # FAISS score is good enough - skip expensive reranking
                logger.info("[RAG] Skipping reranker (FAISS score %.4f >= 0.50)", top_faiss_score)
                top = candidates[:3]  # Use top 3 from FAISS directly
                relevant_top = top  # Accept all with good FAISS score
            else:
                # Borderline case - use reranker for better filtering
                top = rerank(query, candidates, top_n=3)
                # Filter by rerank score threshold
                relevant_top = [c for c in top if c.get("rerank_score", 0) >= RERANK_RELEVANCE_THRESHOLD]
            
            if relevant_top:
                top_score = relevant_top[0].get("rerank_score", 0)
                context = cap_context(build_book_context(relevant_top), 2500)
                match_info = {"source": "FAISS", "score": top_score}
                logger.info("[RAG] Using FAISS RD Sharma context (rerank_score=%.4f, threshold=%.2f) for query: %s", 
                           top_score, RERANK_RELEVANCE_THRESHOLD, query[:80])
            else:
                logger.info("[RAG] FAISS candidates rejected: top rerank_score=%.4f < threshold=%.2f",
                           top[0].get("rerank_score", 0) if top else 0, RERANK_RELEVANCE_THRESHOLD)
        
        # Final check: Only use RAG if we have relevant context
        if not context:
            logger.info("[RAG] ⚠️ NO relevant context - falling back to PURE LLM for query: %s", query[:80])
            return ""
        else:
            logger.info("[RAG] ✓ Using RAG context (source=%s, score=%.4f)", match_info["source"], match_info["score"])
        
        # Enrich context with geometry information if this is a geometry question
        context = enrich_context_with_geometry(context, query)
        geometry_info = detect_geometry_requirement(query)
        if geometry_info["requires_geometry"]:
            logger.info("[RAG] Geometry detected: %s", ", ".join(geometry_info["geometry_types"]))
        
        logger.info("[RAG] Match: source=%s, score=%.4f", match_info["source"], match_info["score"])
        return context

    except Exception as e:
        logger.error("[RAG] Error while retrieving book context: %s", str(e))
        return ""
    finally:
        con.close()


# -------------------------------------------------
# GET AVAILABLE METHODS FOR A QUESTION
# -------------------------------------------------
@app.post("/chat/methods")
def get_methods(question: str = Form(...)):
    """Generate available solution methods for a question"""
    question = (question or "").strip()
    if not question:
        return {"error": True, "methods": []}

    logger.info(f"[Methods] Generating methods for: {question[:50]}")
    
    try:
        # Generate methods using LLM
        from rag.llm_client import generate_methods_fallback
        methods = generate_methods_fallback(question)
        
        logger.info(f"[Methods] Generated {len(methods)} methods")
        return {
            "error": False,
            "question": question,
            "methods": methods
        }
    except Exception as e:
        logger.error(f"[Methods] Error: {str(e)}")
        return {
            "error": True,
            "methods": ["Approach 1", "Approach 2"],
            "message": str(e)
        }


# -------------------------------------------------
# TEXT CHAT WITH METHOD SELECTION
# -------------------------------------------------
@app.post("/chat/text")
def chat_text(
    question: str = Form(...),
    session_id: str = Form(None),
    method: str = Form(None)
):
    question = (question or "").strip()
    if not question:
        return {"answer": "Type a question."}

    if not session_id:
        session_id = str(uuid4())

    # Load session memory
    session = load_session(session_id)
    chat_context = build_chat_context(session)

    # Try to fetch RD Sharma book context (RAG).
    # If none is found, this will be an empty string and the LLM (Qwen)
    # will answer from its own knowledge.
    book_context = retrieve_book_context(question)
    is_rag_mode = bool(book_context and book_context.strip())
    source_label = "RD SHARMA (RAG)" if is_rag_mode else "QWEN (Pure LLM)"
    logger.info(
        "[Chat/Text] session=%s mode=%s",
        session_id,
        source_label,
    )

    # Generate raw LLM answer with method preference
    method_instruction = f"\n\nUse this method: {method}" if method else ""
    raw_answer = generate_step_by_step_fallback(
        user_question=question + method_instruction,
        book_context=book_context,
        chat_context=chat_context
    )

    # CBSE formatted answer
    final_answer = build_final_answer(
        book_context=book_context,
        step_by_step=raw_answer
    )

    # Save formatted answer to session
    update_session(session_id, question, final_answer)

    return {
        "answer": final_answer,
        "session_id": session_id,
        "method_used": method,
        "mode": "RAG (RD Sharma)" if is_rag_mode else "LLM (Qwen)",
        # Full chat history for this session so the UI
        # can show the ongoing conversation.
        "history": load_session(session_id),
    }


# -------------------------------------------------
# SESSION HISTORY ENDPOINT
# -------------------------------------------------
@app.post("/chat/history")
def chat_history(session_id: str = Form(...)):
    """
    Return the full chat history for a given session_id.

    The frontend can call this when a page loads (with a
    stored session_id) to restore the conversation for
    returning users.
    """
    session_id = (session_id or "").strip()
    if not session_id:
        return {"error": True, "message": "session_id is required"}

    return {
        "error": False,
        **get_session_history(session_id),
    }


# -------------------------------------------------
# IMAGE EXTRACTION (Extract text first, then show methods)
# -------------------------------------------------
@app.post("/chat/image/extract")
async def extract_image(
    file: UploadFile = File(...),
    session_id: str = Form(None)
):
    if not session_id:
        session_id = str(uuid4())

    try:
        content = await file.read()
        image_b64 = base64.b64encode(content).decode("utf-8")
        
        logger.info(f"[{session_id}] Image received: {file.filename} ({len(content)} bytes)")

        # Step 1: Try VLM extraction
        logger.info(f"[{session_id}] Step 1: Attempting VLM extraction")
        extracted = extract_question_and_diagram_fallback(image_b64=image_b64)
        qtext = (extracted.get("question_text") or "").strip()
        diag = (extracted.get("diagram_description") or "").strip()
        
        logger.info(f"[{session_id}] VLM result - qtext: {'✓' if qtext else '✗'}, diag: {'✓' if diag else '✗'}")

        # Step 2: Fallback to OCR if VLM failed
        if not qtext:
            logger.info(f"[{session_id}] Step 2: VLM extraction empty, using OCR fallback")
            suffix = "." + (file.filename.split(".")[-1] if "." in file.filename else "png")
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            logger.info(f"[{session_id}] OCR processing: {tmp_path}")
            qtext = (ocr_image(tmp_path) or "").strip()
            logger.info(f"[{session_id}] OCR result: {'✓' if qtext else '✗'} ({len(qtext)} chars)")
            
            # Cleanup
            try:
                os.unlink(tmp_path)
            except:
                pass

        # Step 3: Final validation
        if not qtext:
            logger.error(f"[{session_id}] Failed to extract text from image")
            return {
                "error": True,
                "message": (
                    "I couldn't automatically extract text from the image. "
                    "Troubleshooting:\n"
                    "1. Ensure the image is clear and well-lit\n"
                    "2. Make sure the question text is visible and not cropped\n"
                    "3. Try uploading a JPEG or PNG file\n"
                    "4. Type the question manually if issues persist"
                ),
                "session_id": session_id
            }

        logger.info(f"[{session_id}] Successfully extracted: {qtext[:100]}...")

        # Now get available methods for this extracted question
        from rag.llm_client import generate_methods_fallback
        try:
            methods = generate_methods_fallback(qtext)
            logger.info(f"[{session_id}] Generated {len(methods)} methods")
        except Exception as e:
            logger.warning(f"[{session_id}] Could not generate methods: {str(e)}")
            methods = ["Approach 1", "Approach 2"]

        return {
            "error": False,
            "extracted_question": qtext,
            "diagram_description": diag,
            "methods": methods,
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"[{session_id}] Unexpected error in /chat/image/extract: {str(e)}", exc_info=True)
        return {
            "error": True,
            "message": f"Error processing image: {str(e)}",
            "session_id": session_id
        }


# -------------------------------------------------
# IMAGE ANSWER (Generate answer with selected method)
# -------------------------------------------------
@app.post("/chat/image/answer")
def answer_image(
    question: str = Form(...),
    session_id: str = Form(None),
    method: str = Form(None),
    diagram_description: str = Form(None)
):
    question = (question or "").strip()
    if not question:
        return {"error": True, "answer": "No question provided"}

    if not session_id:
        session_id = str(uuid4())

    try:
        # Load session memory
        session = load_session(session_id)
        chat_context = build_chat_context(session)

        # RAG: fetch RD Sharma context for the extracted/typed question
        book_context = retrieve_book_context(question)
        is_rag_mode = bool(book_context and book_context.strip())
        source_label = "RD SHARMA (RAG)" if is_rag_mode else "QWEN (Pure LLM)"
        logger.info(
            "[Chat/Image/Answer] session=%s mode=%s",
            session_id,
            source_label,
        )

        # Generate raw LLM answer with method preference
        method_instruction = f"\n\nUse this method: {method}" if method else ""
        diagram_instruction = f"\n\nDiagram info: {diagram_description}" if diagram_description else ""
        
        raw_answer = generate_step_by_step_fallback(
            user_question=question + method_instruction + diagram_instruction,
            book_context=book_context,
            chat_context=chat_context,
            diagram_description=diagram_description
        )

        # CBSE formatted answer
        final_answer = build_final_answer(
            book_context=book_context,
            step_by_step=raw_answer
        )

        # Save formatted answer to session
        update_session(session_id, question, final_answer)

        logger.info(f"[{session_id}] Image answer generated successfully with method: {method}")
        
        return {
            "error": False,
            "answer": final_answer,
            "session_id": session_id,
            "method_used": method,
            "mode": "RAG (RD Sharma)" if is_rag_mode else "LLM (Qwen)",
            # Full chat history so UI can render conversation
            "history": load_session(session_id),
        }
        
    except Exception as e:
        logger.error(f"[{session_id}] Unexpected error in /chat/image/answer: {str(e)}", exc_info=True)
        return {
            "error": True,
            "answer": f"Error generating answer: {str(e)}",
            "session_id": session_id
        }


# -------------------------------------------------
# IMAGE CHAT (Legacy - Direct Answer)
# -------------------------------------------------
@app.post("/chat/image")
async def chat_image(
    file: UploadFile = File(...),
    session_id: str = Form(None)
):
    if not session_id:
        session_id = str(uuid4())

    try:
        content = await file.read()
        image_b64 = base64.b64encode(content).decode("utf-8")
        
        logger.info(f"[{session_id}] Image received: {file.filename} ({len(content)} bytes)")

        # Step 1: Try VLM extraction
        logger.info(f"[{session_id}] Step 1: Attempting VLM extraction")
        extracted = extract_question_and_diagram_fallback(image_b64=image_b64)
        qtext = (extracted.get("question_text") or "").strip()
        diag = (extracted.get("diagram_description") or "").strip()
        
        logger.info(f"[{session_id}] VLM result - qtext: {'✓' if qtext else '✗'}, diag: {'✓' if diag else '✗'}")

        # Step 2: Fallback to OCR if VLM failed
        if not qtext:
            logger.info(f"[{session_id}] Step 2: VLM extraction empty, using OCR fallback")
            suffix = "." + (file.filename.split(".")[-1] if "." in file.filename else "png")
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            logger.info(f"[{session_id}] OCR processing: {tmp_path}")
            qtext = (ocr_image(tmp_path) or "").strip()
            logger.info(f"[{session_id}] OCR result: {'✓' if qtext else '✗'} ({len(qtext)} chars)")
            
            # Cleanup
            try:
                os.unlink(tmp_path)
            except:
                pass

        # Step 3: Final validation
        if not qtext:
            logger.error(f"[{session_id}] Failed to extract text from image")
            return {
                "error": True,
                "answer": (
                    "I couldn't automatically extract text from the image. "
                    "Troubleshooting:\n"
                    "1. Ensure the image is clear and well-lit\n"
                    "2. Make sure the question text is visible and not cropped\n"
                    "3. Try uploading a JPEG or PNG file\n"
                    "4. Type the question manually if issues persist"
                ),
                "session_id": session_id
            }

        logger.info(f"[{session_id}] Successfully extracted: {qtext[:100]}...")

        # Load session memory
        session = load_session(session_id)
        chat_context = build_chat_context(session)

        # RAG: fetch RD Sharma context if this looks like a book question
        book_context = retrieve_book_context(qtext)
        logger.info(
            "[Chat/Image] session=%s source=%s",
            session_id,
            "rd_sharma_rag" if book_context else "llm_generic",
        )

        # Generate raw LLM answer
        raw_answer = generate_step_by_step_fallback(
            user_question=qtext,
            book_context=book_context,
            chat_context=chat_context,
            diagram_description=diag
        )

        # CBSE formatted answer
        final_answer = build_final_answer(
            book_context=book_context,
            step_by_step=raw_answer
        )

        # Save formatted answer to session
        update_session(session_id, qtext, final_answer)

        logger.info(f"[{session_id}] Answer generated successfully")
        
        return {
            "error": False,
            "answer": final_answer,
            "session_id": session_id,
            # Full chat history so UI can render conversation
            "history": load_session(session_id),
        }
        
    except Exception as e:
        logger.error(f"[{session_id}] Unexpected error in /chat/image: {str(e)}", exc_info=True)
        return {
            "error": True,
            "answer": f"Error processing image: {str(e)}",
            "session_id": session_id
        }
