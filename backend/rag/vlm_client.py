import requests
import json
import logging
from .config import VLM_URL

logger = logging.getLogger(__name__)

def _fallback_extract_from_image() -> dict:
    return {
        "question_text": "",
        "diagram_description": ""
    }

def extract_question_and_diagram_fallback(image_b64: str) -> dict:
    """
    Extract question text and diagram description from an image using VLM.
    """
    prompt = (
        "You are reading a MATHEMATICS TEXTBOOK PAGE or EXAM PAPER.\n\n"
        
        "YOUR TASK:\n"
        "1. Read the QUESTION TEXT only (not solutions or answers)\n"
        "2. Transcribe the entire question word-for-word, including all numbers, variables, and conditions\n"
        "3. If there is a diagram, graph, or geometric figure, describe it in detail\n"
        "4. Return ONLY a valid JSON object (no extra text)\n\n"
        
        "IMPORTANT:\n"
        "- Transcribe the QUESTION, not the solution\n"
        "- Include all given information (numbers, equations, conditions)\n"
        "- If you see a diagram, describe: shapes, labels, given measurements, angles, parallel lines, etc.\n"
        "- Return ONLY JSON, no markdown, no backticks\n\n"
        
        "JSON FORMAT:\n"
        "{\n"
        '  "question_text": "Complete question text transcribed exactly",\n'
        '  "diagram_description": "Detailed description of any diagram or geometric figure (empty string if none)"\n'
        "}\n"
    )

    try:
        logger.info(f"[VLM] Attempting VLM extraction, URL: {VLM_URL}")
        r = requests.post(
            VLM_URL,
            json={"prompt": prompt, "image_b64": image_b64},
            timeout=120
        )
        r.raise_for_status()
        
        response_text = r.text.strip()
        logger.debug(f"[VLM] Raw response: {response_text[:200]}")
        
        # Try to parse JSON from the response
        data = r.json()
        
        if isinstance(data, dict):
            question = (data.get("question_text") or "").strip()
            diagram = (data.get("diagram_description") or "").strip()
            
            if question:
                logger.info(f"[VLM] ✓ Successfully extracted question: {question[:100]}...")
                return {
                    "question_text": question,
                    "diagram_description": diagram
                }
            else:
                logger.warning("[VLM] Returned empty question_text")
        else:
            logger.warning(f"[VLM] Response is not a dict: {type(data)}")
            
        return _fallback_extract_from_image()
        
    except json.JSONDecodeError as e:
        logger.error(f"[VLM] Failed to parse JSON: {e}")
        return _fallback_extract_from_image()
    except requests.exceptions.ConnectionError as e:
        logger.warning(f"[VLM] Connection failed (expected if VLM not running): {e}")
        return _fallback_extract_from_image()
    except requests.exceptions.RequestException as e:
        logger.error(f"[VLM] Request failed: {e}")
        return _fallback_extract_from_image()
    except Exception as e:
        logger.error(f"[VLM] Unexpected error: {e}")
        return _fallback_extract_from_image()
