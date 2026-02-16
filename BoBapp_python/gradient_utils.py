"""
Gradient Utilities

Dit bestand bevat helper functies voor het toevoegen van gradient effecten
aan CustomTkinter widgets.
"""

import tkinter as tk
from typing import Tuple


def create_gradient_frame(parent, width: int, height: int, color1: str, color2: str, 
                          horizontal: bool = True) -> tk.Canvas:
    """
    Creëer een canvas met gradient effect.
    
    Args:
        parent: Parent widget
        width: Breedte van de gradient
        height: Hoogte van de gradient
        color1: Start kleur (hex)
        color2: Eind kleur (hex)
        horizontal: True voor links->rechts, False voor boven->onder
    
    Returns:
        Canvas widget met gradient
    """
    canvas = tk.Canvas(parent, width=width, height=height, highlightthickness=0)
    
    # Parse colors
    r1, g1, b1 = hex_to_rgb(color1)
    r2, g2, b2 = hex_to_rgb(color2)
    
    # Number of steps for smooth gradient
    steps = 100
    
    if horizontal:
        step_width = width / steps
        for i in range(steps):
            # Interpolate color
            r = int(r1 + (r2 - r1) * i / steps)
            g = int(g1 + (g2 - g1) * i / steps)
            b = int(b1 + (b2 - b1) * i / steps)
            color = f'#{r:02x}{g:02x}{b:02x}'
            
            x1 = i * step_width
            x2 = (i + 1) * step_width
            canvas.create_rectangle(x1, 0, x2, height, fill=color, outline=color)
    else:
        step_height = height / steps
        for i in range(steps):
            # Interpolate color
            r = int(r1 + (r2 - r1) * i / steps)
            g = int(g1 + (g2 - g1) * i / steps)
            b = int(b1 + (b2 - b1) * i / steps)
            color = f'#{r:02x}{g:02x}{b:02x}'
            
            y1 = i * step_height
            y2 = (i + 1) * step_height
            canvas.create_rectangle(0, y1, width, y2, fill=color, outline=color)
    
    return canvas


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Converteer hex kleur naar RGB tuple.
    
    Args:
        hex_color: Hex string zoals "#3B82F6"
    
    Returns:
        (r, g, b) tuple
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def get_gradient_colors(base_color: str, lighter: bool = True) -> Tuple[str, str]:
    """
    Genereer gradient kleurenpaar gebaseerd op base kleur.
    
    Args:
        base_color: Base hex kleur
        lighter: True voor lichter, False voor donkerder gradient
    
    Returns:
        (color1, color2) tuple voor gradient
    """
    r, g, b = hex_to_rgb(base_color)
    
    if lighter:
        # Maak een lichter variant
        factor = 1.3
        r2 = min(255, int(r * factor))
        g2 = min(255, int(g * factor))
        b2 = min(255, int(b * factor))
    else:
        # Maak een donkerder variant
        factor = 0.7
        r2 = max(0, int(r * factor))
        g2 = max(0, int(g * factor))
        b2 = max(0, int(b * factor))
    
    color2 = f'#{r2:02x}{g2:02x}{b2:02x}'
    
    return (base_color, color2)
