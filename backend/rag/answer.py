import json
import re
from typing import Optional

try:
    from sympy import symbols, sympify, pretty, simplify, latex
    from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
    SYMPY_AVAILABLE = True
except ImportError:
    SYMPY_AVAILABLE = False

try:
    from .diagram_generator import format_diagram_for_answer
    DIAGRAM_GENERATOR_AVAILABLE = True
except ImportError:
    DIAGRAM_GENERATOR_AVAILABLE = False

try:
    from .diagram_processor import enrich_answer_with_diagrams
    DIAGRAM_PROCESSOR_AVAILABLE = True
except ImportError:
    DIAGRAM_PROCESSOR_AVAILABLE = False

def sanitize_llm_json(text: str) -> str:
    """
    Make LLM output JSON-safe by removing invalid characters.
    """
    if not text:
        return text

    # Remove all backslashes (JSON killers)
    text = text.replace("\\", "")

    return text


def format_mathematical_expression(expr_str: str) -> str:
    """
    Format mathematical expressions using SymPy for better accuracy.
    Falls back to original string if parsing fails.
    
    Args:
        expr_str: Mathematical expression as string
        
    Returns:
        Formatted expression (pretty printed or LaTeX)
    """
    if not SYMPY_AVAILABLE or not expr_str:
        return expr_str
    
    try:
        # Try to parse the expression
        expr = parse_expr(
            expr_str,
            transformations=(standard_transformations + (implicit_multiplication_application,))
        )
        
        # Return pretty-printed format (readable notation)
        formatted = pretty(expr, use_unicode=True)
        
        # If pretty print failed or returned empty, return original
        if not formatted or formatted.strip() == "":
            return expr_str
            
        return formatted
    except Exception:
        # If parsing fails, return original string
        return expr_str


def extract_and_format_math(text: str) -> str:
    """
    Detect and format mathematical expressions in text.
    Handles: x^2, sqrt(x), frac{a}{b}, ( x ), and other math notation.
    
    Args:
        text: Text potentially containing math expressions
        
    Returns:
        Text with formatted math expressions
    """
    if not text:
        return text
    
    # 1. Remove unnecessary parentheses around single variables or simple expressions
    # Pattern: ( variable ) or ( number )
    text = re.sub(r'\(\s*([a-zA-Z])\s*\)', r'\1', text)  # ( a ) -> a
    text = re.sub(r'\(\s*(\d+)\s*\)', r'\1', text)        # ( 5 ) -> 5
    
    # 2. Convert LaTeX fraction notation to readable format
    # frac{numerator}{denominator} -> (numerator)/(denominator)
    def convert_fraction(match):
        numerator = match.group(1)
        denominator = match.group(2)
        return f"({numerator})/({denominator})"
    
    text = re.sub(r'(?:\\)?frac\{([^}]+)\}\{([^}]+)\}', convert_fraction, text)
    
    # 3. Convert LaTeX sqrt notation
    text = re.sub(r'(?:\\)?sqrt\{([^}]+)\}', r'√(\1)', text)  # sqrt{x} -> √(x)
    
    # 4. Basic symbol conversions
    text = text.replace('^2', '²')
    text = text.replace('^3', '³')
    text = text.replace('sqrt(', '√(')
    text = text.replace('+/-', '±')
    text = text.replace('\\pi', 'π')
    text = text.replace('pi', 'π')
    text = text.replace('\\sum', '∑')
    text = text.replace('sum', '∑')
    text = text.replace('\\int', '∫')
    text = text.replace('integral', '∫')
    text = text.replace('\\times', '×')
    text = text.replace('\\cdot', '·')
    text = text.replace('*', '·')  # Multiplication operator
    
    # 5. Convert double backslash (for matrices, etc.)
    text = text.replace('\\\\', '\n')
    
    return text


def build_final_answer(book_context: str, step_by_step: str) -> str:
    """
    Build professional, student-friendly formatted answer from LLM JSON output.
    Uses visual separators, clear hierarchical structure, and generates actual diagrams.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    cleaned = sanitize_llm_json(step_by_step)

    try:
        data = json.loads(cleaned)
        
        # Log diagram info from LLM response
        diagram_from_llm = data.get("diagram", {})
        logger.info(f"[Answer] LLM diagram section: required={diagram_from_llm.get('required', False)}, type={diagram_from_llm.get('type', 'N/A')}, has_data={bool(diagram_from_llm.get('data'))}")
        
        # Process diagrams: convert JSON data to actual images
        if DIAGRAM_PROCESSOR_AVAILABLE:
            try:
                logger.info(f"[Answer] Calling diagram processor...")
                data = enrich_answer_with_diagrams(data)
                logger.info(f"[Answer] Diagram processor completed successfully")
                
                # Check if image was added
                if data.get("diagram", {}).get("image"):
                    logger.info(f"[Answer] Image successfully generated. Base64 length: {len(data['diagram']['image'].get('base64', ''))}")
                else:
                    logger.warning(f"[Answer] No image was generated by diagram processor")
            except Exception as e:
                logger.error(f"[Answer] Diagram processing failed: {e}", exc_info=True)
        else:
            logger.warning(f"[Answer] Diagram processor not available")
        
    except Exception as e:
        logger.error(f"[Answer] JSON parse error: {e}")
        return "Solution:\n\n" + step_by_step.strip()

    output = []

    # Header
    output.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    output.append("📝 SOLUTION")
    output.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    output.append("")

    # Question
    if data.get("question"):
        output.append("❓ QUESTION:")
        question = extract_and_format_math(data['question'])
        output.append(f"  {question}")
        output.append("")

    # Diagram (if required) - NOW WITH ACTUAL IMAGES
    diagram = data.get("diagram")
    if diagram and diagram.get("required"):
        output.append("📐 DIAGRAM / FIGURE:")
        output.append("─" * 50)
        
        diagram_desc = diagram.get("description", "")
        if diagram_desc:
            # Indent diagram description
            for line in diagram_desc.split("\n"):
                if line.strip():
                    output.append(f"  {line}")
        
        # Show actual generated image
        diagram_image = diagram.get("image")
        if diagram_image:
            output.append("")
            
            if diagram_image.get("base64"):
                # Embedded base64 image (for web display)
                output.append(f"  ![Diagram]({diagram_image['base64'][:100]}...)")
            elif diagram_image.get("url"):
                # URL reference (for static serving)
                output.append(f"  ![Diagram]({diagram_image['url']})")
            elif diagram_image.get("path"):
                # File path
                output.append(f"  [Diagram saved at: {diagram_image['path']}]")
        else:
            # Fallback if image generation failed
            output.append("")
            output.append("  [Diagram would be displayed here]")
        
        # Show labels if available
        labels = diagram.get("labels", [])
        if labels:
            output.append("")
            output.append("  Labels & Reference:")
            for label in labels:
                output.append(f"    • {label}")
        
        output.append("─" * 50)
        output.append("")

    # Given
    if data.get("given"):
        output.append("✓ GIVEN:")
        for g in data["given"]:
            formatted_g = extract_and_format_math(str(g))
            output.append(f"  • {formatted_g}")
        output.append("")

    # Formula/Concept
    if data.get("formula"):
        output.append("🔧 FORMULA / CONCEPT:")
        for f in data["formula"]:
            formatted_f = extract_and_format_math(str(f))
            output.append(f"  • {formatted_f}")
        output.append("")

    # Steps
    if data.get("steps"):
        output.append("📌 STEP-BY-STEP SOLUTION:")
        output.append("")
        for i, step in enumerate(data["steps"], start=1):
            # Format step content with math formatting
            step_str = str(step)
            formatted_step = extract_and_format_math(step_str)
            
            # Check if step already starts with "Step N:" - if so, don't duplicate
            step_pattern = r'^Step\s+\d+:\s*'
            if re.match(step_pattern, formatted_step):
                # Already has "Step N:" prefix, just indent it
                for line in formatted_step.split("\n"):
                    output.append(f"  {line}")
            else:
                # Doesn't have "Step N:" prefix, add it
                output.append(f"  Step {i}:")
                for line in formatted_step.split("\n"):
                    output.append(f"    {line}")
            output.append("")

    # Final Answer - Highlighted with math formatting
    if data.get("answer"):
        output.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        output.append("✓ FINAL ANSWER:")
        output.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        answer = extract_and_format_math(data['answer'])
        output.append(f"  {answer}")
        output.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        output.append("")

    # Verification
    if data.get("verification"):
        output.append("✔ VERIFICATION:")
        verification = extract_and_format_math(str(data["verification"]))
        for line in verification.split("\n"):
            output.append(f"  {line}")
        output.append("")

    output.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    return "\n".join(output).strip()
