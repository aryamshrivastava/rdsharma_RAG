# import requests
# from .config import LLM_URL, LLM_MODEL

# SYSTEM = """
# You are a Class 9–10 school tutor.

# Write answers exactly like a teacher or textbook.

# OUTPUT RULES (VERY IMPORTANT):
# - You MUST return ONLY valid JSON
# - Do NOT add any text outside JSON
# - Do NOT use LaTeX
# - Do NOT use backslashes ( \\ )
# - Use plain text math only: x^2, (7 + 5) / 4, sqrt(25)

# JSON FORMAT:
# {
#   "question": "one line restatement",
#   "diagram": {
#     "required": false,
#     "description": "",
#     "labels": [],
#     "notes": ""
#   },
#   "given": ["each known value clearly written"],
#   "formula": ["formula or theorem used"],
#   "steps": [
#     "Write steps as a teacher explains on the blackboard",
#     "Show substitution clearly",
#     "Show simplification step by step",
#     "Never skip algebra"
#   ],
#   "answer": "final answer written neatly",
#   "verification": "substitute values and verify clearly"
# }

# DIAGRAM RULES:
# - Include the 'diagram' object ONLY if a diagram is required
# - If not required, set required = false
# - Do NOT draw the diagram
# - Describe the diagram clearly in words
# - Mention labels like A, B, C, O
# - Do NOT include diagram text inside steps

# TEACHING RULES:
# - Assume the student is average
# - Use words like: Comparing, Substituting, Simplifying, Therefore, Hence
# - Avoid mechanical phrases like "solve" or "calculate"
# - Never jump steps
# - No emojis
# """

# # One-shot example to lock teacher-style behaviour
# EXAMPLE = """
# Example Output:

# {
#   "question": "Solve the equation x + 5 = 15",
#   "diagram": {
#     "required": false,
#     "description": "",
#     "labels": [],
#     "notes": ""
#   },
#   "given": ["x + 5 = 15"],
#   "formula": ["basic algebra"],
#   "steps": [
#     "The given equation is x + 5 = 15",
#     "Subtracting 5 from both sides of the equation",
#     "We get x = 10"
#   ],
#   "answer": "x = 10",
#   "verification": "Substituting x = 10, the left side becomes 10 + 5 = 15, which equals the right side"
# }
# """

# def generate_step_by_step_fallback(
#     user_question: str,
#     book_context: str,
#     chat_context: str = "",
#     diagram_description: str = ""
# ) -> str:
#     """
#     Generates a teacher-style solution in strict JSON format,
#     with optional diagram description.
#     """

#     prompt = f"""{SYSTEM}

# {EXAMPLE}

# CHAT CONTEXT:
# {chat_context}

# USER QUESTION:
# {user_question}

# BOOK CONTEXT (reference only):
# {book_context}
# """

#     response = requests.post(
#         f"{LLM_URL.rstrip('/')}/api/generate",
#         json={
#             "model": LLM_MODEL,
#             "prompt": prompt,
#             "stream": False
#         },
#         timeout=300
#     )

#     response.raise_for_status()
#     return (response.json().get("response") or "").strip()


import requests
from .config import LLM_URL, LLM_MODEL

import requests
from .config import LLM_URL, LLM_MODEL
from .geometry import build_geometry_prompt_instruction, detect_geometry_requirement

import requests
from .config import LLM_URL, LLM_MODEL

SYSTEM = """
You are an expert Class 9–10 mathematics tutor.

Your task: Create CLEAR, PROFESSIONAL, and STUDENT-FRIENDLY solutions.

PEDAGOGY RULES:
- Write the solution exactly as a teacher would explain on the blackboard
- Use complete sentences explaining WHAT you're doing and WHY
- Start each step by clearly stating what operation you're performing
- Show substitution step by step with clear brackets
- Never skip steps or jump to conclusions
- Use simple, encouraging language
- End each step with what you conclude
- Use transitions: "Therefore", "Hence", "So", "Comparing", "Substituting"

FORMATTING RULES:
- Return ONLY valid JSON (no text before or after)
- Do NOT use LaTeX, backslashes, or special symbols
- Use plain text math: x^2, sqrt(x), (a+b)/c, 2^3
- Each step should be 1-2 sentences, clear and complete
- Make the answer suitable for an exam or homework

JSON STRUCTURE:
{
  "question": "Exact restatement of the question to solve",
  "given": [
    "Known value 1",
    "Known value 2"
  ],
  "formula": [
    "Relevant formula or concept 1",
    "Relevant formula or concept 2"
  ],
  "diagram": {
    "required": true/false,
    "description": "If required: detailed description of what diagram shows",
    "type": "coordinate_system|circle|triangle|cube|distance|cylinder|cone|tent|etc",
    "data": {
      "For coordinate_system": {"points": [["A", 2, 3], ["B", 5, 7]]},
      "For circle": {"radius": 5, "center": [0, 0], "points": [["A", 3, 4]]},
      "For triangle": {"vertices": [["A", 0, 0], ["B", 3, 0], ["C", 1.5, 2.5]]},
      "For cube": {"side_length": 5},
      "For distance": {"p1": ["A", 2, 3], "p2": ["B", 5, 7]},
      "For cylinder": {"radius": 2, "height": 2.1},
      "For cone": {"radius": 2, "height": 1, "slant_height": 2.8},
      "For tent": {"cylinder_radius": 2, "cylinder_height": 2.1, "cone_slant_height": 2.8}
    },
    "labels": ["label 1", "label 2"]
  },
  "steps": [
    "Step 1: Clear explanation of first operation and result",
    "Step 2: Clear explanation of next operation and result",
    "Step 3: Continue with logical progression"
  ],
  "answer": "The final answer written clearly with units if applicable",
  "verification": "How to check if the answer is correct by substitution or reverse operation"
}

DIAGRAM RULES (IMPORTANT for geometry questions):
- For geometry, coordinate, circles, constructions, areas, 3D shapes: ALWAYS include diagram info
- In "diagram" object: set "required": true and provide detailed description
- Provide diagram "type": which kind of diagram to generate
- Provide "data": specific values for diagram generation (points, radius, vertices, etc.)
- Describe: what shape, labels (A, B, C, O, etc.), dimensions, angles, special points
- NO ASCII art needed - system will generate actual diagrams
- Reference diagram in steps: "As shown in the diagram...", "In the figure...", "In the above diagram..."

CRITICAL INSTRUCTIONS:
1. Write steps as a teacher would speak - natural and flowing
2. Never write mechanical steps like "Substitute x = 5 in equation 1"
   Instead write: "Substituting x = 5 into the first equation"
3. Always show intermediate calculations clearly
4. Make the verification section test the answer to ensure it's correct
5. Keep language appropriate for a 14-16 year old student
"""

# One-shot example to lock textbook-style behaviour
EXAMPLE = """
EXAMPLE OUTPUT (Geometry - with Diagram Data):

{
  "question": "Find the distance between points A(2, 3) and B(5, 7)",
  "given": [
    "Point A has coordinates (2, 3)",
    "Point B has coordinates (5, 7)"
  ],
  "formula": [
    "Distance formula: d = sqrt((x2-x1)^2 + (y2-y1)^2)"
  ],
  "diagram": {
    "required": true,
    "description": "A coordinate system showing two points A(2, 3) and B(5, 7) with a line connecting them forming a right triangle.",
    "type": "distance",
    "data": {
      "p1": ["A", 2, 3],
      "p2": ["B", 5, 7]
    },
    "labels": [
      "Point A at (2, 3)",
      "Point B at (5, 7)",
      "Horizontal distance: 3 units",
      "Vertical distance: 4 units"
    ]
  },
  "steps": [
    "Step 1: We need to find the distance between A(2, 3) and B(5, 7). We use the distance formula: d = sqrt((x2-x1)^2 + (y2-y1)^2).",
    "Step 2: Substituting the coordinates into the formula: d = sqrt((5-2)^2 + (7-3)^2).",
    "Step 3: Simplifying inside the brackets: d = sqrt(3^2 + 4^2).",
    "Step 4: Calculating the squares: d = sqrt(9 + 16) = sqrt(25).",
    "Step 5: Taking the square root: d = 5 units."
  ],
  "answer": "The distance between points A(2, 3) and B(5, 7) is 5 units",
  "verification": "Using the Pythagorean theorem on the right triangle formed: horizontal distance = 3, vertical distance = 4, so hypotenuse = sqrt(3^2 + 4^2) = 5 ✓"
}

EXAMPLE OUTPUT (3D Geometry - Tent with Cylinder + Cone):

{
  "question": "A tent is in the shape of a cylinder surmounted by a conical top. If the height and diameter of the cylindrical part are 2.1 m and 4 m respectively, and the slant height of the top is 2.8 m, find the area of the canvas used for making the tent. Also, find the cost of the canvas of the tent at the rate of Rs. 500 per m2.",
  "given": [
    "Height of cylindrical part: 2.1 m",
    "Diameter of cylindrical part: 4 m, so radius = 2 m",
    "Slant height of conical part: 2.8 m"
  ],
  "formula": [
    "Lateral surface area of cylinder: A_cyl = 2πrh",
    "Lateral surface area of cone: A_cone = πrl",
    "Total canvas area: A_total = A_cyl + A_cone"
  ],
  "diagram": {
    "required": true,
    "description": "A 3D tent showing a cylinder (radius 2 m, height 2.1 m) with a cone on top (slant height 2.8 m). The cone is positioned on top of the cylinder forming a tent shape.",
    "type": "tent",
    "data": {
      "cylinder_radius": 2,
      "cylinder_height": 2.1,
      "cone_slant_height": 2.8
    },
    "labels": [
      "Height of cylinder: h = 2.1 m",
      "Radius: r = 2 m",
      "Slant height of cone: l = 2.8 m",
      "Cylindrical part (blue): covers the sides of cylinder",
      "Conical part (red): covers the slanted surface of cone"
    ]
  },
  "steps": [
    "Step 1: The canvas area consists of the lateral surface of the cylinder and the lateral surface of the cone (not the base).",
    "Step 2: Calculate the lateral surface area of the cylinder using A_cyl = 2πrh. Substituting r = 2 and h = 2.1: A_cyl = 2 × π × 2 × 2.1 = 2 × 3.14 × 2 × 2.1 = 26.38 m².",
    "Step 3: Calculate the lateral surface area of the cone using A_cone = πrl. Substituting r = 2 and l = 2.8: A_cone = π × 2 × 2.8 = 3.14 × 2 × 2.8 = 17.58 m².",
    "Step 4: The total canvas area is the sum: Total = 26.38 + 17.58 = 43.96 m².",
    "Step 5: The cost is calculated as: Cost = Area × Rate = 43.96 × 500 = Rs. 21,980"
  ],
  "answer": "The area of the canvas used is 43.96 m², and the cost is Rs. 21,980",
  "verification": "We can verify by checking each formula: Cylinder lateral area = 2πrh = 2 × 3.14 × 2 × 2.1 = 26.38, Cone lateral area = πrl = 3.14 × 2 × 2.8 = 17.58, Total = 43.96 m². Cost = 43.96 × 500 = 21,980 ✓"
}

EXAMPLE OUTPUT (Non-Geometry):

{
  "question": "Solve for x: 2x + 5 = 15",
  "given": [
    "Equation: 2x + 5 = 15"
  ],
  "formula": [
    "Algebraic principle: Isolate variable by inverse operations"
  ],
  "diagram": {
    "required": false,
    "description": "",
    "type": "",
    "data": {},
    "labels": []
  },
  "steps": [
    "Step 1: We have the equation 2x + 5 = 15. To find x, we need to isolate it on one side.",
    "Step 2: First, subtract 5 from both sides of the equation. This gives us 2x = 10.",
    "Step 3: Now divide both sides by 2 to isolate x. This gives us x = 5."
  ],
  "answer": "x = 5",
  "verification": "Substitute x = 5: 2(5) + 5 = 10 + 5 = 15 ✓"
}
"""

def generate_step_by_step_fallback(
    user_question: str,
    book_context: str,
    chat_context: str = "",
    diagram_description: str = ""
) -> str:
    """
    Generates a detailed, teacher-style solution in strict JSON format.
    The output is professional, clear, and suitable for students.
    Automatically detects geometry questions and requests diagrams.
    """
    
    # Add geometry-specific instructions if needed
    geometry_instruction = build_geometry_prompt_instruction(user_question)

    prompt = f"""{SYSTEM}

{EXAMPLE}

{geometry_instruction}

CHAT CONTEXT (for continuity):
{chat_context if chat_context else "No previous context"}

DIAGRAM INFORMATION (if any):
{diagram_description if diagram_description else "No additional diagram info"}

USER QUESTION TO SOLVE:
{user_question}

BOOK CONTEXT (for reference):
{book_context if book_context else "No book context available"}

Now, solve the question above following all the rules and provide your response as ONLY the JSON object.
"""

    response = requests.post(
        f"{LLM_URL.rstrip('/')}/api/generate",
        json={
            "model": LLM_MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=300
    )

    response.raise_for_status()

    # Return RAW JSON string from the model
    return (response.json().get("response") or "").strip()


def generate_methods_fallback(question: str) -> list:
    """
    Generate available solution methods for a question.
    Returns a list of method names/descriptions.
    """
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Build prompt for method generation
        prompt = f"""You are a math tutor. Given a math question, list 2-4 different valid solution methods.

Question: {question}

Respond ONLY with a JSON object in this format:
{{
  "methods": [
    "Method 1: [Brief description]",
    "Method 2: [Brief description]",
    "Method 3: [Brief description]"
  ]
}}

Return only valid JSON, no other text."""

        response = requests.post(
            f"{LLM_URL.rstrip('/')}/api/generate",
            json={
                "model": LLM_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )
        
        response.raise_for_status()
        result = (response.json().get("response") or "").strip()
        
        # Try to parse JSON
        try:
            data = json.loads(result)
            methods = data.get("methods", [])
            if methods and len(methods) > 0:
                return methods
        except:
            pass
        
        # Fallback methods if parsing fails
        logger.info(f"[LLM Methods] Fallback to default methods for: {question[:50]}")
        return [
            "Method 1: Standard algebraic approach",
            "Method 2: Geometric/visual approach",
            "Method 3: Alternative formula method"
        ]
        
    except Exception as e:
        logger.error(f"[LLM Methods] Error: {str(e)}")
        # Return default methods on error
        return [
            "Method 1: Step-by-step approach",
            "Method 2: Direct formula method",
            "Method 3: Logical reasoning"
        ]

