import easyocr
from PIL import Image
import logging

logger = logging.getLogger(__name__)

# Singleton OCR instance
_OCR = None


def get_ocr():
    """
    Lazily load EasyOCR only once
    """
    global _OCR
    if _OCR is None:
        logger.info("[OCR] Initializing EasyOCR for English")
        _OCR = easyocr.Reader(['en'], gpu=False, verbose=False)
    return _OCR


def _preprocess_image(image_path: str):
    """
    Light preprocessing:
    - Convert to RGB
    - Resize to reasonable bounds
    """
    try:
        img = Image.open(image_path).convert("RGB")
        img.thumbnail((1024, 1024))
        img.save(image_path)
        logger.info(f"[OCR] Image preprocessed: {image_path}")
    except Exception as e:
        logger.error(f"[OCR] Image preprocessing error: {e}")


def _normalize(text: str) -> str:
    """
    Normalize math symbols for LLM friendliness
    """
    return (
        text.replace("×", "*")
            .replace("÷", "/")
            .replace("−", "-")
            .replace("–", "-")
            .replace("—", "-")
            .replace("√", "sqrt")
            .replace("^", "**")
    )


def ocr_image(image_path: str) -> str:
    """
    Main OCR entry point using EasyOCR
    """
    try:
        logger.info(f"[OCR] Starting for image: {image_path}")
        
        _preprocess_image(image_path)
        logger.info("[OCR] Image preprocessed")
        
        logger.info("[OCR] Getting EasyOCR reader...")
        reader = get_ocr()
        logger.info("[OCR] EasyOCR ready")

        logger.info("[OCR] Running OCR...")
        results = reader.readtext(image_path)
        logger.debug(f"[OCR] Raw results: {len(results)} text regions found")

        # Extract text from results
        texts = []
        for detection in results:
            if len(detection) >= 2:
                text = detection[1]  # Text is the second element
                confidence = detection[2]  # Confidence is third
                if text and confidence > 0.3:  # Only include if confidence > 30%
                    texts.append(text)
        
        extracted_text = "\n".join(texts)
        logger.info(f"[OCR] Extracted text length: {len(extracted_text)} chars")
        
        if not extracted_text.strip():
            logger.warning("[OCR] ✗ No text detected in image")
            return ""

        normalized = _normalize(extracted_text)
        logger.info(f"[OCR] ✓ Successfully extracted: {normalized[:100]}...")
        return normalized

    except Exception as e:
        logger.error(f"[OCR] ✗ Processing error: {e}", exc_info=True)
        return ""


