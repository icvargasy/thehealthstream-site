import os
from PIL import Image
from collections import Counter

def analyze_image(path):
    if not os.path.exists(path):
        print(f"{path} does not exist")
        return
    img = Image.open(path).convert("RGBA")
    pixels = list(img.getdata())
    colors = []
    for r, g, b, a in pixels:
        if a > 20: # ignore transparent
            colors.append((r, g, b))
    counter = Counter(colors)
    print(f"\nDominant colors in {path}:")
    for color, count in counter.most_common(3):
        hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
        print(f"  RGB: {color} | Hex: {hex_color} | Count: {count}")

for filename in os.listdir("assets"):
    if filename.endswith(".png"):
        analyze_image(os.path.join("assets", filename))
