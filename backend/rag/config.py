# from pathlib import Path
# import os

# BASE_DIR = Path(__file__).resolve().parents[1]
# DATA_DIR = BASE_DIR / "data"

# RAW_DIR = DATA_DIR / "raw"
# PAGES_DIR = DATA_DIR / "pages"
# OCR_DIR = DATA_DIR / "ocr"
# DB_DIR = DATA_DIR / "db"
# FAISS_DIR = DATA_DIR / "faiss"

# SQLITE_PATH = DB_DIR / "chunks.sqlite"
# FAISS_INDEX_PATH = FAISS_DIR / "index.faiss"
# FAISS_META_PATH = FAISS_DIR / "meta.json"

# # Embeddings (CPU-safe)
# EMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"

# OCR_LANG = "en"
# RENDER_DPI = 220

# # Ollama config (local)
# LLM_URL = os.getenv("LLM_URL", "http://127.0.0.1:11434")
# LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b-instruct")
# # LLM_MODEL = os.getenv("LLM_MODEL", "qwen3")
# VLM_URL = os.getenv("VLM_URL", "http://127.0.0.1:9001/vlm")



from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[1]


def _load_local_env() -> None:
	"""Load key=value pairs from backend/.env.local if present."""
	env_path = BASE_DIR / ".env.local"
	if not env_path.exists():
		return

	for raw_line in env_path.read_text(encoding="utf-8").splitlines():
		line = raw_line.strip()
		if not line or line.startswith("#") or "=" not in line:
			continue
		key, value = line.split("=", 1)
		key = key.strip()
		value = value.strip().strip('"').strip("'")
		# Respect already-exported env vars from shell/OS.
		if key and key not in os.environ:
			os.environ[key] = value


_load_local_env()

DEFAULT_LOCAL_DATA_DIR = Path(os.getenv("LOCALAPPDATA", str(BASE_DIR))) / "rdsharma-rag" / "data"
DATA_DIR = Path(os.getenv("LOCAL_DATA_DIR", str(DEFAULT_LOCAL_DATA_DIR))).expanduser()

# Prefer the repository PDF location by default; OCR/DB/FAISS outputs are local-writable.
REPO_RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR = Path(os.getenv("RAW_DIR", str(REPO_RAW_DIR))).expanduser()

PAGES_DIR = DATA_DIR / "pages"
OCR_DIR = DATA_DIR / "ocr"
DB_DIR = DATA_DIR / "db"
FAISS_DIR = DATA_DIR / "faiss"

SQLITE_PATH = DB_DIR / "chunks.sqlite"
FAISS_INDEX_PATH = FAISS_DIR / "index.faiss"
FAISS_META_PATH = FAISS_DIR / "meta.json"

for _path in (DATA_DIR, RAW_DIR, PAGES_DIR, OCR_DIR, DB_DIR, FAISS_DIR):
	_path.mkdir(parents=True, exist_ok=True)

# -------------------------
# Embeddings
# -------------------------
EMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"

OCR_LANG = "en"
RENDER_DPI = 220

# -------------------------
# Ollama / VLM
# -------------------------
LLM_URL = os.getenv("LLM_URL", "http://127.0.0.1:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b-instruct")
# LLM_MODEL = os.getenv("LLM_MODEL", "qwen3")

VLM_URL = os.getenv("VLM_URL", "http://127.0.0.1:9001/vlm")

# ==================================================
# SESSION / CHAT MEMORY
# ==================================================
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
SESSION_TTL = 1800   # 30 minutes
MAX_TURNS = 5        # last 5 Q&A only

# Local run config (used by launcher scripts/commands)
APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
