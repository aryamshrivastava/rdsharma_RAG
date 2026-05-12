"""
Geometric Diagram Generation Module

Generates actual diagrams (PNG/SVG) for geometry problems using matplotlib.
Creates visual representations of common geometry shapes and concepts.
"""

import os
import json
import base64
import logging
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO

logger = logging.getLogger(__name__)

# Diagram output directory
DIAGRAMS_DIR = Path(__file__).parent.parent.parent / "static" / "diagrams"
DIAGRAMS_DIR.mkdir(parents=True, exist_ok=True)


def generate_coordinate_system_diagram(points: list, title: str = "Coordinate Geometry") -> dict:
    """
    Generate a coordinate system with plotted points.
    
    Args:
        points: List of tuples [(name, x, y), ...]
                Example: [("A", 2, 3), ("B", 5, 7)]
        title: Diagram title
    
    Returns:
        {
            "path": "path/to/diagram.png",
            "base64": "base64_encoded_image",
            "description": "What the diagram shows"
        }
    """
    try:
        fig, ax = plt.subplots(figsize=(8, 8))
        
        # Draw axes
        ax.axhline(y=0, color='black', linewidth=0.5)
        ax.axvline(x=0, color='black', linewidth=0.5)
        
        # Draw grid
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Plot points
        if points:
            xs = [p[1] for p in points]
            ys = [p[2] for p in points]
            
            # Calculate axis limits with padding
            min_x = min(xs + [0]) - 1
            max_x = max(xs + [0]) + 1
            min_y = min(ys + [0]) - 1
            max_y = max(ys + [0]) + 1
            
            ax.set_xlim(min_x, max_x)
            ax.set_ylim(min_y, max_y)
            
            # Plot each point
            for name, x, y in points:
                ax.plot(x, y, 'ro', markersize=8)
                ax.annotate(f'{name}({x}, {y})', (x, y), 
                           textcoords="offset points", xytext=(0, 10),
                           ha='center', fontsize=10, fontweight='bold')
            
            # Connect points if more than 1
            if len(points) > 1:
                xs_line = [p[1] for p in points]
                ys_line = [p[2] for p in points]
                ax.plot(xs_line, ys_line, 'b-', linewidth=2, alpha=0.6)
        
        ax.set_xlabel('X', fontsize=12, fontweight='bold')
        ax.set_ylabel('Y', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_aspect('equal', adjustable='box')
        
        # Save diagram
        diagram_path = DIAGRAMS_DIR / f"coordinate_{id(fig)}.png"
        plt.savefig(diagram_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        # Create base64
        with open(diagram_path, 'rb') as f:
            base64_str = base64.b64encode(f.read()).decode('utf-8')
        
        return {
            "path": str(diagram_path),
            "base64": f"data:image/png;base64,{base64_str}",
            "url": f"/static/diagrams/{diagram_path.name}",
            "description": f"Coordinate system showing {len(points)} point(s)"
        }
    
    except Exception as e:
        logger.error(f"Error generating coordinate diagram: {e}")
        return None


def generate_circle_diagram(radius: float, center: tuple = (0, 0), 
                           points: list = None, title: str = "Circle Geometry") -> dict:
    """
    Generate a circle diagram with optional points/chords/tangents.
    
    Args:
        radius: Circle radius
        center: (x, y) center coordinates
        points: Optional points on/near circle [("A", x, y), ...]
        title: Diagram title
    
    Returns:
        Diagram dict with path, base64, url
    """
    try:
        fig, ax = plt.subplots(figsize=(8, 8))
        
        # Draw circle
        circle = patches.Circle(center, radius, fill=False, edgecolor='blue', linewidth=2)
        ax.add_patch(circle)
        
        # Draw center
        ax.plot(center[0], center[1], 'ko', markersize=6)
        ax.annotate('O', center, textcoords="offset points", xytext=(5, 5),
                   fontsize=10, fontweight='bold')
        
        # Draw radius line
        ax.plot([center[0], center[0] + radius], [center[1], center[1]], 
               'r--', linewidth=1.5, label=f'Radius = {radius}')
        ax.annotate(f'r = {radius}', (center[0] + radius/2, center[1] + 0.2),
                   fontsize=10, fontweight='bold', color='red')
        
        # Plot additional points if provided
        if points:
            for name, x, y in points:
                ax.plot(x, y, 'go', markersize=8)
                ax.annotate(name, (x, y), textcoords="offset points", xytext=(5, 5),
                           fontsize=10, fontweight='bold')
        
        # Set limits
        margin = radius * 1.2
        ax.set_xlim(center[0] - margin, center[0] + margin)
        ax.set_ylim(center[1] - margin, center[1] + margin)
        
        ax.set_aspect('equal', adjustable='box')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_xlabel('X', fontsize=12, fontweight='bold')
        ax.set_ylabel('Y', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(loc='upper right', fontsize=10)
        
        # Save diagram
        diagram_path = DIAGRAMS_DIR / f"circle_{id(fig)}.png"
        plt.savefig(diagram_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        # Create base64
        with open(diagram_path, 'rb') as f:
            base64_str = base64.b64encode(f.read()).decode('utf-8')
        
        return {
            "path": str(diagram_path),
            "base64": f"data:image/png;base64,{base64_str}",
            "url": f"/static/diagrams/{diagram_path.name}",
            "description": f"Circle diagram with radius {radius}"
        }
    
    except Exception as e:
        logger.error(f"Error generating circle diagram: {e}")
        return None


def generate_triangle_diagram(vertices: list, title: str = "Triangle") -> dict:
    """
    Generate a triangle diagram.
    
    Args:
        vertices: [("A", x1, y1), ("B", x2, y2), ("C", x3, y3)]
        title: Diagram title
    
    Returns:
        Diagram dict
    """
    try:
        if len(vertices) < 3:
            return None
        
        fig, ax = plt.subplots(figsize=(8, 8))
        
        # Extract coordinates
        names = [v[0] for v in vertices]
        coords = np.array([[v[1], v[2]] for v in vertices])
        
        # Draw triangle
        triangle = patches.Polygon(coords, fill=False, edgecolor='blue', linewidth=2)
        ax.add_patch(triangle)
        
        # Plot vertices
        for (name, x, y) in vertices:
            ax.plot(x, y, 'ro', markersize=8)
            ax.annotate(name, (x, y), textcoords="offset points", xytext=(5, 5),
                       fontsize=11, fontweight='bold')
        
        # Calculate and show side lengths
        for i in range(3):
            p1 = coords[i]
            p2 = coords[(i + 1) % 3]
            mid = (p1 + p2) / 2
            length = np.linalg.norm(p2 - p1)
            ax.text(mid[0], mid[1], f'{length:.1f}', fontsize=9,
                   ha='center', bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
        
        # Set limits
        margin = np.std(coords) * 0.5
        ax.set_xlim(coords[:, 0].min() - margin, coords[:, 0].max() + margin)
        ax.set_ylim(coords[:, 1].min() - margin, coords[:, 1].max() + margin)
        
        ax.set_aspect('equal', adjustable='box')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_xlabel('X', fontsize=12, fontweight='bold')
        ax.set_ylabel('Y', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        # Save diagram
        diagram_path = DIAGRAMS_DIR / f"triangle_{id(fig)}.png"
        plt.savefig(diagram_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        # Create base64
        with open(diagram_path, 'rb') as f:
            base64_str = base64.b64encode(f.read()).decode('utf-8')
        
        return {
            "path": str(diagram_path),
            "base64": f"data:image/png;base64,{base64_str}",
            "url": f"/static/diagrams/{diagram_path.name}",
            "description": f"Triangle with vertices {', '.join(names)}"
        }
    
    except Exception as e:
        logger.error(f"Error generating triangle diagram: {e}")
        return None


def generate_cube_diagram(side_length: float, title: str = "Cube") -> dict:
    """
    Generate a 3D cube diagram.
    
    Args:
        side_length: Length of cube side
        title: Diagram title
    
    Returns:
        Diagram dict
    """
    try:
        from mpl_toolkits.mplot3d import Axes3D
        
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # Define cube vertices
        s = side_length
        vertices = np.array([
            [0, 0, 0], [s, 0, 0], [s, s, 0], [0, s, 0],  # bottom
            [0, 0, s], [s, 0, s], [s, s, s], [0, s, s]   # top
        ])
        
        # Draw edges
        edges = [
            [0, 1], [1, 2], [2, 3], [3, 0],  # bottom
            [4, 5], [5, 6], [6, 7], [7, 4],  # top
            [0, 4], [1, 5], [2, 6], [3, 7]   # vertical
        ]
        
        for edge in edges:
            points = vertices[edge]
            ax.plot3D(*points.T, 'b-', linewidth=2)
        
        # Plot vertices
        ax.scatter(*vertices.T, c='red', s=50)
        
        # Add labels
        labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        for i, (vertex, label) in enumerate(zip(vertices, labels)):
            ax.text(vertex[0], vertex[1], vertex[2], label, fontsize=10, fontweight='bold')
        
        ax.set_xlabel('X', fontsize=11, fontweight='bold')
        ax.set_ylabel('Y', fontsize=11, fontweight='bold')
        ax.set_zlabel('Z', fontsize=11, fontweight='bold')
        ax.set_title(f"{title} (Side = {side_length})", fontsize=14, fontweight='bold')
        
        # Save diagram
        diagram_path = DIAGRAMS_DIR / f"cube_{id(fig)}.png"
        plt.savefig(diagram_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        # Create base64
        with open(diagram_path, 'rb') as f:
            base64_str = base64.b64encode(f.read()).decode('utf-8')
        
        return {
            "path": str(diagram_path),
            "base64": f"data:image/png;base64,{base64_str}",
            "url": f"/static/diagrams/{diagram_path.name}",
            "description": f"3D Cube with side length {side_length}"
        }
    
    except Exception as e:
        logger.error(f"Error generating cube diagram: {e}")
        return None


def generate_distance_diagram(p1: tuple, p2: tuple, title: str = "Distance Formula") -> dict:
    """
    Generate a distance diagram showing distance between two points.
    
    Args:
        p1: (name, x1, y1)
        p2: (name, x2, y2)
        title: Title
    
    Returns:
        Diagram dict
    """
    try:
        fig, ax = plt.subplots(figsize=(8, 8))
        
        n1, x1, y1 = p1
        n2, x2, y2 = p2
        
        # Draw axes
        ax.axhline(y=0, color='black', linewidth=0.5)
        ax.axvline(x=0, color='black', linewidth=0.5)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Plot points
        ax.plot(x1, y1, 'ro', markersize=10, label='Point 1')
        ax.plot(x2, y2, 'go', markersize=10, label='Point 2')
        
        # Draw distance line
        ax.plot([x1, x2], [y1, y2], 'b-', linewidth=2.5, label='Distance')
        
        # Draw right triangle for visualization
        ax.plot([x1, x2], [y1, y1], 'k--', linewidth=1, alpha=0.5)  # horizontal
        ax.plot([x2, x2], [y1, y2], 'k--', linewidth=1, alpha=0.5)  # vertical
        
        # Calculate distance
        distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        
        # Labels
        ax.annotate(f'{n1}({x1}, {y1})', (x1, y1), textcoords="offset points", 
                   xytext=(-15, -15), fontsize=11, fontweight='bold')
        ax.annotate(f'{n2}({x2}, {y2})', (x2, y2), textcoords="offset points", 
                   xytext=(5, 5), fontsize=11, fontweight='bold')
        
        # Distance label
        mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mid_x, mid_y, f'd = {distance:.2f}', fontsize=12, fontweight='bold',
               bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8))
        
        # Dimensions
        ax.text((x1 + x2) / 2, y1 - 0.5, f'Δx = {abs(x2 - x1):.1f}', 
               fontsize=10, ha='center', color='red')
        ax.text(x2 + 0.5, (y1 + y2) / 2, f'Δy = {abs(y2 - y1):.1f}', 
               fontsize=10, ha='left', color='red')
        
        margin = max(abs(x2 - x1), abs(y2 - y1)) * 0.3
        ax.set_xlim(min(x1, x2) - margin, max(x1, x2) + margin)
        ax.set_ylim(min(y1, y2) - margin, max(y1, y2) + margin)
        
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlabel('X', fontsize=12, fontweight='bold')
        ax.set_ylabel('Y', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(loc='upper right', fontsize=10)
        
        # Save diagram
        diagram_path = DIAGRAMS_DIR / f"distance_{id(fig)}.png"
        plt.savefig(diagram_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        # Create base64
        with open(diagram_path, 'rb') as f:
            base64_str = base64.b64encode(f.read()).decode('utf-8')
        
        return {
            "path": str(diagram_path),
            "base64": f"data:image/png;base64,{base64_str}",
            "url": f"/static/diagrams/{diagram_path.name}",
            "description": f"Distance between {n1} and {n2}: {distance:.2f} units"
        }
    
    except Exception as e:
        logger.error(f"Error generating distance diagram: {e}")
        return None


def generate_cylinder_diagram(radius: float, height: float, title: str = "Cylinder") -> dict:
    """
    Generate a 3D cylinder diagram.
    
    Args:
        radius: Radius of cylinder
        height: Height of cylinder
        title: Diagram title
    
    Returns:
        Diagram dict with path, base64, url, description
    """
    try:
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # Create cylinder using parametric equations
        z = np.linspace(0, height, 50)
        theta = np.linspace(0, 2 * np.pi, 50)
        
        # Mesh for cylinder surface
        Theta, Z = np.meshgrid(theta, z)
        X = radius * np.cos(Theta)
        Y = radius * np.sin(Theta)
        
        # Plot cylinder surface
        ax.plot_surface(X, Y, Z, alpha=0.7, cmap='viridis', edgecolor='black', linewidth=0.2)
        
        # Top circle
        circle_z = np.ones_like(theta) * height
        circle_x = radius * np.cos(theta)
        circle_y = radius * np.sin(theta)
        ax.plot(circle_x, circle_y, circle_z, 'b-', linewidth=2)
        
        # Bottom circle
        circle_z = np.zeros_like(theta)
        ax.plot(circle_x, circle_y, circle_z, 'b-', linewidth=2)
        
        # Vertical lines (guides)
        for t in np.linspace(0, 2*np.pi, 8, endpoint=False):
            x = radius * np.cos(t)
            y = radius * np.sin(t)
            ax.plot([x, x], [y, y], [0, height], 'gray', linewidth=0.5, alpha=0.5)
        
        # Add dimension labels
        ax.text(radius + 0.5, 0, height/2, f'h = {height}', fontsize=11, fontweight='bold')
        ax.text(0, radius + 0.5, 0, f'r = {radius}', fontsize=11, fontweight='bold')
        
        ax.set_xlabel('X', fontsize=10)
        ax.set_ylabel('Y', fontsize=10)
        ax.set_zlabel('Z (Height)', fontsize=10)
        ax.set_title(title, fontsize=12, fontweight='bold')
        
        # Set equal aspect
        max_range = max(radius, height)
        ax.set_xlim([-max_range, max_range])
        ax.set_ylim([-max_range, max_range])
        ax.set_zlim([0, height * 1.2])
        
        # Save diagram
        diagram_path = DIAGRAMS_DIR / f"cylinder_{id(fig)}.png"
        plt.savefig(diagram_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        # Create base64
        with open(diagram_path, 'rb') as f:
            base64_str = base64.b64encode(f.read()).decode('utf-8')
        
        lateral_area = 2 * np.pi * radius * height
        return {
            "path": str(diagram_path),
            "base64": f"data:image/png;base64,{base64_str}",
            "url": f"/static/diagrams/{diagram_path.name}",
            "description": f"Cylinder with radius {radius} m and height {height} m. Lateral surface area = 2πrh = {lateral_area:.2f} m²"
        }
    
    except Exception as e:
        logger.error(f"Error generating cylinder diagram: {e}")
        return None


def generate_cone_diagram(radius: float, height: float, slant_height: float = None, title: str = "Cone") -> dict:
    """
    Generate a 3D cone diagram.
    / 
    Args:
        radius: Radius of cone base
        height: Height of cone
        slant_height: Slant height (optional, calculated if not provided)
        title: Diagram title
    
    Returns:
        Diagram dict with path, base64, url, description
    """
    try:
        if slant_height is None:
            slant_height = np.sqrt(radius**2 + height**2)
        
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # Create cone using parametric equations
        z = np.linspace(0, height, 50)
        theta = np.linspace(0, 2 * np.pi, 50)
        
        # Mesh for cone surface
        Z, Theta = np.meshgrid(z, theta)
        # Radius decreases linearly with height
        R = radius * (1 - Z / height)
        X = R * np.cos(Theta)
        Y = R * np.sin(Theta)
        
        # Plot cone surface
        ax.plot_surface(X, Y, Z, alpha=0.7, cmap='plasma', edgecolor='black', linewidth=0.2)
        
        # Base circle
        circle_z = np.zeros_like(theta)
        circle_x = radius * np.cos(theta)
        circle_y = radius * np.sin(theta)
        ax.plot(circle_x, circle_y, circle_z, 'b-', linewidth=2)
        
        # Apex to base lines (guides)
        for t in np.linspace(0, 2*np.pi, 8, endpoint=False):
            x = radius * np.cos(t)
            y = radius * np.sin(t)
            ax.plot([0, x], [0, y], [height, 0], 'gray', linewidth=0.5, alpha=0.5)
        
        # Add dimension labels
        ax.text(0, 0, height + 0.5, 'Apex', fontsize=11, fontweight='bold')
        ax.text(radius + 0.5, 0, 0, f'r = {radius}', fontsize=11, fontweight='bold')
        ax.text(radius/2, radius/2, height/2, f'l = {slant_height:.2f}', fontsize=11, fontweight='bold', color='red')
        ax.text(0, 0, -height*0.2, f'h = {height}', fontsize=11, fontweight='bold')
        
        ax.set_xlabel('X', fontsize=10)
        ax.set_ylabel('Y', fontsize=10)
        ax.set_zlabel('Z (Height)', fontsize=10)
        ax.set_title(title, fontsize=12, fontweight='bold')
        
        # Set equal aspect
        max_range = max(radius, height)
        ax.set_xlim([-max_range, max_range])
        ax.set_ylim([-max_range, max_range])
        ax.set_zlim([0, height * 1.2])
        
        # Save diagram
        diagram_path = DIAGRAMS_DIR / f"cone_{id(fig)}.png"
        plt.savefig(diagram_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        # Create base64
        with open(diagram_path, 'rb') as f:
            base64_str = base64.b64encode(f.read()).decode('utf-8')
        
        lateral_area = np.pi * radius * slant_height
        return {
            "path": str(diagram_path),
            "base64": f"data:image/png;base64,{base64_str}",
            "url": f"/static/diagrams/{diagram_path.name}",
            "description": f"Cone with base radius {radius} m, height {height} m, and slant height {slant_height:.2f} m. Lateral surface area = πrl = {lateral_area:.2f} m²"
        }
    
    except Exception as e:
        logger.error(f"Error generating cone diagram: {e}")
        return None


def generate_tent_diagram(cylinder_radius: float, cylinder_height: float, cone_slant_height: float, title: str = "Tent") -> dict:
    """
    Generate a diagram of a tent (cylinder with conical top).
    
    Args:
        cylinder_radius: Radius of cylindrical part
        cylinder_height: Height of cylindrical part
        cone_slant_height: Slant height of conical top
        title: Diagram title
    
    Returns:
        Diagram dict with path, base64, url, description
    """
    try:
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        # Create cylinder
        z_cyl = np.linspace(0, cylinder_height, 40)
        theta = np.linspace(0, 2 * np.pi, 40)
        Theta, Z_cyl = np.meshgrid(theta, z_cyl)
        X_cyl = cylinder_radius * np.cos(Theta)
        Y_cyl = cylinder_radius * np.sin(Theta)
        
        # Plot cylinder surface
        ax.plot_surface(X_cyl, Y_cyl, Z_cyl, alpha=0.6, cmap='Blues', edgecolor='black', linewidth=0.1)
        
        # Create cone on top
        # Cone height calculated from slant height and radius: h = sqrt(l^2 - r^2)
        cone_height = np.sqrt(cone_slant_height**2 - cylinder_radius**2)
        
        z_cone = np.linspace(0, cone_height, 40)
        Z_cone, Theta_cone = np.meshgrid(z_cone, theta)
        R_cone = cylinder_radius * (1 - Z_cone / cone_height)
        X_cone = R_cone * np.cos(Theta_cone)
        Y_cone = R_cone * np.sin(Theta_cone)
        Z_cone_plot = Z_cone + cylinder_height
        
        # Plot cone surface
        ax.plot_surface(X_cone, Y_cone, Z_cone_plot, alpha=0.6, cmap='Reds', edgecolor='black', linewidth=0.1)
        
        # Base circle of cylinder
        circle_x = cylinder_radius * np.cos(theta)
        circle_y = cylinder_radius * np.sin(theta)
        ax.plot(circle_x, circle_y, np.zeros_like(theta), 'b-', linewidth=2)
        
        # Junction between cylinder and cone
        ax.plot(circle_x, circle_y, np.ones_like(theta) * cylinder_height, 'b-', linewidth=2)
        
        # Apex
        apex_z = cylinder_height + cone_height
        ax.scatter([0], [0], [apex_z], color='red', s=100, marker='^', label='Apex')
        
        # Dimension labels
        ax.text(cylinder_radius + 0.3, 0, cylinder_height/2, f'h₁ = {cylinder_height} m', fontsize=10, fontweight='bold')
        ax.text(cylinder_radius + 0.3, 0, cylinder_height + cone_height/2, f'l = {cone_slant_height:.2f} m', fontsize=10, fontweight='bold', color='darkred')
        ax.text(1.2, 0, 0, f'r = {cylinder_radius} m', fontsize=10, fontweight='bold')
        
        # Add guide lines showing dimensions
        ax.plot([cylinder_radius, cylinder_radius], [0, 0], [0, cylinder_height], 'gray', linewidth=1, alpha=0.5, linestyle='--')
        ax.plot([cylinder_radius, 0], [0, 0], [cylinder_height, apex_z], 'red', linewidth=1, alpha=0.5, linestyle='--')
        
        ax.set_xlabel('X', fontsize=10)
        ax.set_ylabel('Y', fontsize=10)
        ax.set_zlabel('Z (Height)', fontsize=10)
        ax.set_title(title, fontsize=13, fontweight='bold')
        ax.legend()
        
        # Set viewing angle
        max_range = max(cylinder_radius, cylinder_height + cone_height)
        ax.set_xlim([-max_range * 0.7, max_range * 0.7])
        ax.set_ylim([-max_range * 0.7, max_range * 0.7])
        ax.set_zlim([0, max_range])
        ax.view_init(elev=20, azim=45)
        
        # Save diagram
        diagram_path = DIAGRAMS_DIR / f"tent_{id(fig)}.png"
        plt.savefig(diagram_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        # Create base64
        with open(diagram_path, 'rb') as f:
            base64_str = base64.b64encode(f.read()).decode('utf-8')
        
        cylinder_area = 2 * np.pi * cylinder_radius * cylinder_height
        cone_area = np.pi * cylinder_radius * cone_slant_height
        total_area = cylinder_area + cone_area
        
        return {
            "path": str(diagram_path),
            "base64": f"data:image/png;base64,{base64_str}",
            "url": f"/static/diagrams/{diagram_path.name}",
            "description": f"Tent with cylinder (radius {cylinder_radius} m, height {cylinder_height} m) and cone (slant height {cone_slant_height:.2f} m). Total canvas area = {total_area:.2f} m²"
        }
    
    except Exception as e:
        logger.error(f"Error generating tent diagram: {e}")
        return None


def format_diagram_for_answer(diagram_dict: dict) -> str:
    """
    Format a diagram dictionary into HTML/Markdown for display.
    
    Args:
        diagram_dict: Output from diagram generation functions
    
    Returns:
        Formatted string for display
    """
    if not diagram_dict:
        return ""
    
    # Return markdown with embedded base64 image
    return f"""
![Diagram]({diagram_dict['base64']})

*{diagram_dict['description']}*
"""
