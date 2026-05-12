"""
Diagram Post-Processor

Converts LLM diagram JSON data into actual images using diagram_generator.
This is called after LLM generates the answer JSON.
"""

import logging
from .diagram_generator import (
    generate_coordinate_system_diagram,
    generate_circle_diagram,
    generate_triangle_diagram,
    generate_cube_diagram,
    generate_distance_diagram,
    generate_cylinder_diagram,
    generate_cone_diagram,
    generate_tent_diagram
)

logger = logging.getLogger(__name__)


def process_diagram_data(diagram_dict: dict) -> dict:
    """
    Convert diagram specification JSON into actual generated diagram.
    
    Args:
        diagram_dict: Diagram data from LLM response
                      {
                        "required": bool,
                        "description": str,
                        "type": str,  # "coordinate_system", "circle", etc.
                        "data": dict,  # Specific data for the diagram type
                        "labels": list
                      }
    
    Returns:
        Updated diagram dict with "image" field containing generated diagram
        {
            ...original fields...,
            "image": {
                "base64": "data:image/png;base64,...",
                "url": "/static/diagrams/...",
                "path": "..."
            }
        }
    """
    
    if not diagram_dict or not diagram_dict.get("required"):
        return diagram_dict
    
    try:
        diagram_type = diagram_dict.get("type", "").lower()
        data = diagram_dict.get("data", {})
        title = diagram_dict.get("description", "Diagram")[:50]  # Use first 50 chars as title
        
        generated_image = None
        
        # Route to appropriate diagram generator
        if diagram_type == "coordinate_system" or diagram_type == "coordinates":
            points = data.get("points", [])
            if points:
                generated_image = generate_coordinate_system_diagram(points, title)
        
        elif diagram_type == "distance":
            p1 = data.get("p1")
            p2 = data.get("p2")
            if p1 and p2:
                generated_image = generate_distance_diagram(tuple(p1), tuple(p2), title)
        
        elif diagram_type == "circle":
            radius = data.get("radius", 1)
            center = tuple(data.get("center", [0, 0]))
            points = data.get("points", None)
            generated_image = generate_circle_diagram(radius, center, points, title)
        
        elif diagram_type == "triangle":
            vertices = data.get("vertices", [])
            if len(vertices) >= 3:
                generated_image = generate_triangle_diagram(vertices, title)
        
        elif diagram_type == "cube":
            side_length = data.get("side_length", 5)
            generated_image = generate_cube_diagram(side_length, title)
        
        elif diagram_type == "cylinder":
            radius = data.get("radius", 2)
            height = data.get("height", 2.1)
            generated_image = generate_cylinder_diagram(radius, height, title)
        
        elif diagram_type == "cone":
            radius = data.get("radius", 2)
            height = data.get("height", 1)
            slant_height = data.get("slant_height", None)
            generated_image = generate_cone_diagram(radius, height, slant_height, title)
        
        elif diagram_type == "tent" or diagram_type == "cylinder_cone":
            cylinder_radius = data.get("cylinder_radius", 2)
            cylinder_height = data.get("cylinder_height", 2.1)
            cone_slant_height = data.get("cone_slant_height", 2.8)
            generated_image = generate_tent_diagram(cylinder_radius, cylinder_height, cone_slant_height, title)
        
        # Add image to diagram dict
        if generated_image:
            diagram_dict["image"] = {
                "base64": generated_image["base64"],
                "url": generated_image["url"],
                "path": generated_image["path"]
            }
            logger.info(f"[Diagram] Generated {diagram_type} diagram successfully")
        else:
            logger.warning(f"[Diagram] Could not generate {diagram_type} diagram")
    
    except Exception as e:
        logger.error(f"[Diagram] Error processing diagram: {str(e)}")
    
    return diagram_dict


def enrich_answer_with_diagrams(answer_json_dict: dict) -> dict:
    """
    Process all diagrams in an answer JSON response.
    
    Args:
        answer_json_dict: The parsed JSON from LLM
    
    Returns:
        Updated answer with generated diagrams
    """
    if not isinstance(answer_json_dict, dict):
        return answer_json_dict
    
    try:
        if "diagram" in answer_json_dict:
            answer_json_dict["diagram"] = process_diagram_data(
                answer_json_dict["diagram"]
            )
    except Exception as e:
        logger.error(f"[Diagram Enrichment] Error: {str(e)}")
    
    return answer_json_dict
