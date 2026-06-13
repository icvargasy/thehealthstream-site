"""Recolors light theme assets from the old maroon brand color to the unified orange-coral accent.

Maps #8c1832 (maroon) → #ea6878 (coral/salmon, matching dark theme logo and CSS --accent-synapse).
"""

import os
from PIL import Image


def recolor_image(path: str, target_hex: str, replacement_hex: str) -> None:
    """Replaces a target color with a replacement color in a PNG image, preserving shading.

    Args:
        path: Absolute or relative path to the PNG file to recolor.
        target_hex: Hex color string to replace (e.g. '#8c1832').
        replacement_hex: Hex color string to use as replacement (e.g. '#ea6878').

    Raises:
        FileNotFoundError: If the image file does not exist at the given path.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Image file not found: {path}")

    img = Image.open(path).convert("RGBA")
    data = list(img.getdata())

    def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
        """Parses a hex color string to an RGB tuple.

        Args:
            hex_str: Hex color string with or without leading '#'.

        Returns:
            A tuple of (R, G, B) integer values in [0, 255].
        """
        h = hex_str.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    target_rgb = hex_to_rgb(target_hex)
    replacement_rgb = hex_to_rgb(replacement_hex)
    tolerance = 60

    new_data = []
    for r, g, b, a in data:
        dist = ((r - target_rgb[0])**2 + (g - target_rgb[1])**2 + (b - target_rgb[2])**2) ** 0.5
        if dist < tolerance and a > 0:
            # Interpolate to preserve anti-aliasing shading
            factor = dist / tolerance  # 0 = exact match, 1 = edge of tolerance
            nr = int(replacement_rgb[0] * (1 - factor) + r * factor)
            ng = int(replacement_rgb[1] * (1 - factor) + g * factor)
            nb = int(replacement_rgb[2] * (1 - factor) + b * factor)
            new_data.append((nr, ng, nb, a))
        else:
            new_data.append((r, g, b, a))

    img.putdata(new_data)
    img.save(path)
    print(f"  Recolored: {path}")


ASSETS_TO_RECOLOR = [
    ("assets/logo_only_light.png", "#8c1832", "#ea6878"),
    ("assets/both_together_light.png", "#8c1832", "#ea6878"),
    ("assets/favicon_light.png", "#8c1832", "#ea6878"),
]

if __name__ == "__main__":
    print("Recoloring light theme assets: #8c1832 → #ea6878 (unified coral accent)")
    for path, old_color, new_color in ASSETS_TO_RECOLOR:
        try:
            recolor_image(path, old_color, new_color)
        except FileNotFoundError as e:
            print(f"  SKIP: {e}")
    print("Done.")
