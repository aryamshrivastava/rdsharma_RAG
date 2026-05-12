import re
import fitz
from pathlib import Path
from .config import RENDER_DPI

def has_meaningful_text(page: fitz.Page) -> bool:
    txt = page.get_text("text") or ""
    return sum(ch.isalnum() for ch in txt) > 60

def extract_text_layer(page: fitz.Page) -> str:
    return (page.get_text("text") or "").strip()

def render_page_to_png(page: fitz.Page, out_path: Path, dpi: int = RENDER_DPI):
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pix.save(str(out_path))

def cleanup_text(s: str) -> str:
    s = s.replace("\r", "")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()
