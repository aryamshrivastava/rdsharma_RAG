"""
Geometry Detection and Diagram Handling Module

Detects when math problems require diagrams/figures and enriches
the context with geometry-specific information.
"""

import re
import logging

logger = logging.getLogger(__name__)

# Topics that ALWAYS require diagrams/figures
GEOMETRY_TOPICS = {
    # Coordinate Geometry
    "coordinate geometry": ["points", "distance", "section formula", "midpoint", "line", "slope"],
    "coordinate system": ["axes", "plotting", "coordinates"],
    "distance formula": ["points", "distance", "length"],
    "section formula": ["divides", "ratio", "internal", "external"],
    "midpoint": ["midpoint", "divides", "1:1"],
    
    # Circles
    "circle": ["circle", "center", "radius", "circumference", "diameter"],
    "tangent": ["tangent", "circle", "perpendicular"],
    "chord": ["chord", "circle", "segment"],
    "arc": ["arc", "circle", "sector", "segment"],
    "secant": ["secant", "circle"],
    
    # Triangles
    "triangle": ["triangle", "sides", "angles", "vertices", "area", "altitude", "median"],
    "congruence": ["congruent", "triangle", "sss", "sas", "aas", "rhs"],
    "similarity": ["similar", "triangle", "proportional", "ratio"],
    "pythagoras": ["pythagoras", "hypotenuse", "right angle"],
    "triangle inequality": ["triangle", "inequality", "sides"],
    
    # Constructions
    "construction": ["construct", "draw", "perpendicular", "bisector", "angle"],
    "perpendicular bisector": ["perpendicular", "bisector"],
    "angle bisector": ["angle", "bisector"],
    "parallel lines": ["parallel", "construct", "lines"],
    
    # Quadrilaterals
    "quadrilateral": ["quadrilateral", "parallelogram", "rectangle", "square", "rhombus", "trapezium"],
    "parallelogram": ["parallelogram", "opposite", "sides", "angles"],
    "rectangle": ["rectangle", "diagonal", "square"],
    "square": ["square", "sides", "diagonal"],
    "rhombus": ["rhombus", "diagonal", "sides"],
    
    # Areas
    "area": ["area", "triangle", "circle", "quadrilateral", "square", "rectangle", "square units"],
    "surface area": ["surface area", "cube", "cuboid", "cylinder", "sphere"],
    "volume": ["volume", "cube", "cuboid", "cylinder", "sphere", "cone"],
    
    # 3D Geometry
    "3d geometry": ["cube", "cuboid", "cylinder", "sphere", "cone", "pyramid"],
    "cube": ["cube", "edges", "faces", "diagonal"],
    "cuboid": ["cuboid", "length", "breadth", "height"],
    "sphere": ["sphere", "radius", "diameter"],
    "cylinder": ["cylinder", "radius", "height", "lateral"],
    "cone": ["cone", "radius", "height", "slant height", "lateral"],
    "tent": ["tent", "cylinder", "cone", "surmounted", "canvas"],
    "prism": ["prism", "lateral", "surface area"],
    
    # Angles
    "angle": ["angle", "degrees", "vertically opposite", "supplementary", "complementary"],
    "vertically opposite": ["vertically opposite", "angle"],
    "adjacent angles": ["adjacent", "angle"],
    
    # Polygons
    "polygon": ["polygon", "sides", "angles", "regular", "irregular"],
    "regular polygon": ["regular", "polygon", "sides"],
    
    # Vectors and Transformations
    "translation": ["translation", "vector", "shift"],
    "rotation": ["rotation", "angle", "center"],
    "reflection": ["reflection", "mirror", "line"],
    "enlargement": ["enlargement", "scale factor", "center"],
    
    # Statistics and Probability
    "histogram": ["histogram", "frequency", "class", "width"],
    "graph": ["graph", "plot", "chart", "line graph", "bar graph"],
    "scatter plot": ["scatter", "plot", "correlation"],
}

# Keywords that indicate geometry is involved
GEOMETRY_KEYWORDS = {
    "diagram", "figure", "sketch", "draw", "construct", "perpendicular", "parallel",
    "angle", "triangle", "circle", "polygon", "quadrilateral", "area", "perimeter",
    "volume", "surface", "coordinate", "axes", "plot", "vertices", "sides", "edges",
    "faces", "radius", "diameter", "circumference", "arc", "chord", "tangent", "sector",
    "cone", "cylinder", "sphere", "cube", "cuboid", "pyramid", "rhombus", "trapezium",
    "altitude", "median", "bisector", "congruent", "similar", "symmetry", "rotation",
    "reflection", "translation", "height", "base", "diagonal", "slant", "lateral",
    "tent", "prism", "cylinder", "3d", "three-dimensional"
}

# CBSE chapters that are geometry-heavy
GEOMETRY_CHAPTERS = {
    "Chapter 9": "Applications of Trigonometry (if involving angles)",
    "Chapter 10": "Circles",
    "Chapter 11": "Constructions",
    "Chapter 12": "Areas Related to Circles",
    "Chapter 13": "Surface Areas and Volumes",
    "Chapter 14": "Statistics",
}


def detect_geometry_requirement(question: str) -> dict:
    """
    Detect if a question requires geometry/diagrams.
    
    Returns:
        {
            "requires_geometry": bool,
            "geometry_types": list,
            "key_concepts": list,
            "diagram_hints": str
        }
    """
    question_lower = question.lower()
    
    result = {
        "requires_geometry": False,
        "geometry_types": [],
        "key_concepts": [],
        "diagram_hints": ""
    }
    
    # Check for geometry keywords
    found_keywords = []
    for keyword in GEOMETRY_KEYWORDS:
        if keyword in question_lower:
            found_keywords.append(keyword)
    
    if found_keywords:
        result["requires_geometry"] = True
    
    # Check for specific geometry topics
    for topic, keywords in GEOMETRY_TOPICS.items():
        matches = sum(1 for kw in keywords if kw in question_lower)
        if matches >= 1:  # At least 1 keyword match
            result["geometry_types"].append(topic)
            result["requires_geometry"] = True
    
    # Build diagram hints based on detected geometry
    if result["requires_geometry"]:
        geometry_types = result["geometry_types"]
        
        if any("coordinate" in t for t in geometry_types):
            result["diagram_hints"] += "• A coordinate system with plotted points\n"
        
        if any("circle" in t for t in geometry_types):
            result["diagram_hints"] += "• A circle diagram showing center, radius, or other elements\n"
        
        if any("triangle" in t for t in geometry_types):
            result["diagram_hints"] += "• Triangle diagram with labeled sides and angles\n"
        
        if any("construction" in t for t in geometry_types):
            result["diagram_hints"] += "• Step-by-step construction diagram\n"
        
        if any("quadrilateral" in t for t in geometry_types):
            result["diagram_hints"] += "• Quadrilateral diagram with vertices and angles\n"
        
        if any("area" in t or "volume" in t for t in geometry_types):
            result["diagram_hints"] += "• 2D/3D shape diagram with dimensions labeled\n"
        
        if any("3d" in t for t in geometry_types):
            result["diagram_hints"] += "• 3D perspective view of the shape\n"
        
        if any("polygon" in t for t in geometry_types):
            result["diagram_hints"] += "• Polygon diagram with sides labeled\n"
    
    result["key_concepts"] = found_keywords
    
    return result


def enrich_context_with_geometry(context: str, question: str) -> str:
    """
    Enrich the retrieved context with diagram hints and geometry information.
    """
    geometry_info = detect_geometry_requirement(question)
    
    if not geometry_info["requires_geometry"]:
        return context
    
    # Build enrichment
    enrichment = "\n\n" + "="*70 + "\n"
    enrichment += "📐 GEOMETRY/DIAGRAM INFORMATION:\n"
    enrichment += "="*70 + "\n"
    
    if geometry_info["geometry_types"]:
        enrichment += "Geometry Topics Detected:\n"
        for geom_type in geometry_info["geometry_types"]:
            enrichment += f"  • {geom_type.title()}\n"
        enrichment += "\n"
    
    if geometry_info["diagram_hints"]:
        enrichment += "Expected Diagram Elements:\n"
        enrichment += geometry_info["diagram_hints"]
        enrichment += "\n"
    
    enrichment += "⚠️ IMPORTANT: This question requires diagrams.\n"
    enrichment += "Provide diagram data (type, specific values, labels).\n"
    enrichment += "The system will automatically generate professional PNG diagrams.\n"
    enrichment += "="*70 + "\n"
    
    return context + enrichment


def build_geometry_prompt_instruction(question: str) -> str:
    """
    Build specific LLM instructions for geometry-heavy questions.
    """
    geometry_info = detect_geometry_requirement(question)
    
    if not geometry_info["requires_geometry"]:
        return ""
    
    instruction = """

GEOMETRY-SPECIFIC INSTRUCTIONS (ACTUAL DIAGRAMS - NO ASCII):
- This question involves geometry and REQUIRES an actual diagram.
- You MUST include a "diagram" section with generation specifications.
- Provide these fields in the diagram object:
  * "required": true
  * "description": What the diagram shows (text description)
  * "type": One of: coordinate_system, distance, circle, triangle, cube, cylinder, cone, tent
  * "data": Actual numeric values for diagram generation
  * "labels": Clear labels for points, angles, distances shown in diagram

DIAGRAM GENERATION DATA RULES:
For "coordinate_system": {"points": [["A", x1, y1], ["B", x2, y2]]}
For "distance": {"p1": ["name", x1, y1], "p2": ["name", x2, y2]}
For "circle": {"radius": 5, "center": [0, 0], "points": [["A", 3, 4]]}
For "triangle": {"vertices": [["A", 0, 0], ["B", 3, 0], ["C", 1.5, 2.5]]}
For "cube": {"side_length": 5}
For "cylinder": {"radius": 2, "height": 2.1}
For "cone": {"radius": 2, "height": 1, "slant_height": 2.8}
For "tent": {"cylinder_radius": 2, "cylinder_height": 2.1, "cone_slant_height": 2.8}

EXAMPLE DIAGRAM OBJECT (3D TENT):
"diagram": {
  "required": true,
  "description": "A 3D tent showing a cylinder (radius 2 m, height 2.1 m) with cone on top (slant height 2.8 m). The cone is positioned on top of cylinder forming a tent shape.",
  "type": "tent",
  "data": {"cylinder_radius": 2, "cylinder_height": 2.1, "cone_slant_height": 2.8},
  "labels": ["Height of cylinder: h = 2.1 m", "Radius: r = 2 m", "Slant height of cone: l = 2.8 m"]
}

IMPORTANT:
- Do NOT include "ascii_view" - system generates actual PNG diagrams
- Provide SPECIFIC numeric values in the "data" field
- For 3D shapes (cylinder, cone, tent): use exact dimensions from problem
- Reference diagram in steps: "As shown in the diagram...", "In the figure..."
- Make labels clear and descriptive
- For tent: cylinder_radius and cone radius are SAME value
- The system will automatically generate professional diagrams from your data
"""
    
    return instruction


def extract_diagram_info_from_response(response_json: dict) -> dict:
    """
    Extract diagram information from LLM JSON response.
    """
    diagram_info = {
        "required": False,
        "description": "",
        "labels": [],
        "ascii_view": ""
    }
    
    if isinstance(response_json, dict):
        # Try to get diagram info if present
        if "diagram" in response_json:
            diagram_data = response_json["diagram"]
            if isinstance(diagram_data, dict):
                diagram_info["required"] = diagram_data.get("required", False)
                diagram_info["description"] = diagram_data.get("description", "")
                diagram_info["labels"] = diagram_data.get("labels", [])
                diagram_info["ascii_view"] = diagram_data.get("ascii_view", "")
    
    return diagram_info


def format_diagram_in_answer(answer_text: str) -> str:
    """
    Format diagram information nicely in the answer text.
    """
    # This function can be enhanced to format diagrams from the response
    return answer_text
