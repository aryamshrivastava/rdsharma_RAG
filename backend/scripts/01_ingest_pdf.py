import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

import json
import tempfile
from pathlib import Path
import fitz
from tqdm import tqdm

from rag.config import RAW_DIR, OCR_DIR
from rag.ocr import ocr_image
from rag.ingest_utils import has_meaningful_text, extract_text_layer, render_page_to_png, cleanup_text

def main():
    pdf_path = next(RAW_DIR.glob("*.pdf"), None)
    if not pdf_path:
        raise SystemExit("Put your PDF in backend/data/raw/ as .pdf")

    OCR_DIR.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    total_pages = doc.page_count

    start_page = int(os.getenv("INGEST_START_PAGE", "1"))
    end_page = int(os.getenv("INGEST_END_PAGE", str(total_pages)))
    max_pages = os.getenv("INGEST_MAX_PAGES")

    start_page = max(1, start_page)
    end_page = min(total_pages, end_page)
    if max_pages:
        end_page = min(end_page, start_page + int(max_pages) - 1)

    if start_page > end_page:
        raise SystemExit(f"Invalid page range: start={start_page}, end={end_page}")

    print("PDF:", pdf_path.name)
    print("Pages:", total_pages)
    print(f"Processing range: {start_page}-{end_page}")

    for i in tqdm(range(start_page - 1, end_page), desc="Ingest"):
        page_no = i + 1
        out_json = OCR_DIR / f"page_{page_no:04d}.json"
        if out_json.exists():
            continue  # resume support

        page = doc.load_page(i)

        if has_meaningful_text(page):
            text = cleanup_text(extract_text_layer(page))
            payload = {"page": page_no, "mode": "text_layer", "text": text}
            out_json.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            continue

        # Use a unique temp image file to avoid Windows file-lock collisions.
        with tempfile.NamedTemporaryFile(prefix=f"rd_page_{page_no:04d}_", suffix=".png", delete=False) as tmp:
            tmp_img = Path(tmp.name)

        try:
            render_page_to_png(page, tmp_img)
            text = cleanup_text(ocr_image(str(tmp_img)))
        finally:
            if tmp_img.exists():
                tmp_img.unlink(missing_ok=True)

        payload = {"page": page_no, "mode": "ocr", "text": text}
        out_json.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

if __name__ == "__main__":
    main()
