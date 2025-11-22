import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import random
import math

# --- Configuration ---
WIDTH, HEIGHT = 500, 350
FRAMES = 40  # Number of frames for a smooth loop
DURATION = 80  # Milliseconds per frame (lower = faster)
HORIZON_Y = HEIGHT * 0.55  # Where the sky meets the grid

# Synthwave Color Palette
C_BG_TOP = (10, 0, 30)  # Deep space purple
C_BG_BOT = (40, 0, 60)  # Horizon glow purple
C_GRID = (255, 20, 180)  # Neon Magenta
C_CYAN = (0, 255, 255)  # Electric Cyan
C_PURPLE = (160, 50, 255)  # Bright Purple
C_STAR = (220, 240, 255)  # Near white star

# --- Helper Functions ---


def create_gradient_bg(w, h):
    # Creates a vertical gradient background
    base = Image.new("RGB", (w, h), C_BG_TOP)
    top = Image.new("RGB", (w, h), C_BG_TOP)
    bot = Image.new("RGB", (w, h), C_BG_BOT)
    mask = Image.linear_gradient("L").resize((w, h))
    bg = Image.composite(base, bot, mask)
    return bg


def draw_glow_line(draw, start, end, color, width_base, glow_intensity=1.0):
    # Draws a line with a faux "glow" effect by drawing a wider, transparent line underneath
    # Deconstruct color for transparency
    r, g, b = color
    # Glow layer (wider, transparent)
    glow_color = (r, g, b, int(100 * glow_intensity))
    draw.line([start, end], fill=glow_color, width=width_base + 4)
    # Core layer (thinner, brighter)
    core_color = (min(r + 50, 255), min(g + 50, 255), min(b + 50, 255), 255)
    draw.line([start, end], fill=core_color, width=width_base)


def rotate_point(point, center, angle):
    # Rotates a point around a center axis
    x, y = point
    cx, cy = center
    rad = math.radians(angle)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    nx = cos_a * (x - cx) - sin_a * (y - cy) + cx
    ny = sin_a * (x - cx) + cos_a * (y - cy) + cy
    return nx, ny


# --- Pre-computation Setup ---

# 1. Initialize Stars (fixed positions, varying brightness)
num_stars = 150
stars = []
for _ in range(num_stars):
    x = random.randint(0, WIDTH)
    y = random.randint(0, int(HORIZON_Y))
    base_size = random.randint(1, 3)
    # Each star gets a unique phase offset for twinkling
    phase = random.uniform(0, math.pi * 2)
    stars.append({"pos": (x, y), "size": base_size, "phase": phase})

# 2. Define Cosmic Structure (A wireframe Icosahedron-like shape)
# Define vertices relative to a center (0,0,0)
structure_vertices = [
    (0, -50, 0),
    (0, 50, 0),  # Top/Bottom peaks
    (-40, -20, 40),
    (40, -20, 40),
    (40, -20, -40),
    (-40, -20, -40),  # Upper ring
    (-40, 20, 40),
    (40, 20, 40),
    (40, 20, -40),
    (-40, 20, -40),  # Lower ring
]
# Define edges connecting vertices (indices)
structure_edges = [
    (0, 2),
    (0, 3),
    (0, 4),
    (0, 5),  # Top peak to upper ring
    (1, 6),
    (1, 7),
    (1, 8),
    (1, 9),  # Bottom peak to lower ring
    (2, 3),
    (3, 4),
    (4, 5),
    (5, 2),  # Upper ring loop
    (6, 7),
    (7, 8),
    (8, 9),
    (9, 6),  # Lower ring loop
    (2, 6),
    (3, 7),
    (4, 8),
    (5, 9),  # Connect rings vertically
]

structure_center_base = (WIDTH * 0.7, HEIGHT * 0.3)

# --- Main Loop Generation ---
frames = []
print("Generating frames...")

for i in range(FRAMES):
    # 1. Background
    img = create_gradient_bg(WIDTH, HEIGHT).convert("RGBA")
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Calculate loop progress (0.0 to 1.0)
    progress = i / FRAMES

    # 2. Draw Stars (Scintillating)
    for star in stars:
        # Scintillation math: sin wave based on frame + unique phase
        brightness = (math.sin(progress * math.pi * 4 + star["phase"]) + 1) / 2
        # Map brightness (0.0-1.0) to alpha (50-255)
        alpha = int(50 + brightness * 205)
        r, g, b = C_STAR
        star_color = (r, g, b, alpha)
        sx, sy = star["pos"]
        # Slight slow drift of stars
        sx = (sx + progress * 20) % WIDTH

        # Draw star with glow
        draw.ellipse(
            [(sx - 1, sy - 1), (sx + star["size"], sy + star["size"])], fill=star_color
        )
        if star["size"] > 1 and alpha > 200:
            draw.ellipse(
                [(sx - 3, sy - 3), (sx + star["size"] + 2, sy + star["size"] + 2)],
                fill=(r, g, b, 50),
            )

    # 3. Draw Synthwave Grid (Scrolling Perspective)
    # Vanishing point for perspective lines
    vp_x, vp_y = WIDTH / 2, HORIZON_Y - 50

    # Vertical perspective lines
    for x_base in range(-WIDTH, WIDTH * 2, 60):
        # Find bottom point
        bx = x_base
        by = HEIGHT
        # Find intersection with horizon line
        # Simple maths: derive line equation from VP to Bottom Point, find X at HORIZON_Y
        if by - vp_y != 0:
            slope = (bx - vp_x) / (by - vp_y)
            hx = vp_x + slope * (HORIZON_Y - vp_y)
            draw_glow_line(draw, (hx, HORIZON_Y), (bx, by), C_GRID, 1)

    # Horizontal scrolling lines
    # Use exponential spacing for perspective effect
    num_h_lines = 12
    for j in range(num_h_lines):
        # Calculate base proportionality (0.0 at horizon, 1.0 at bottom)
        prop_base = j / num_h_lines
        # Add scrolling offset, ensure it loops perfectly with modulo 1.0
        prop_scrolled = (prop_base - progress) % 1.0

        # Apply power curve for perspective spacing (lines get closer near horizon)
        y_pos = HORIZON_Y + (HEIGHT - HORIZON_Y) * (prop_scrolled**2.5)

        # Fade out lines near the horizon
        intensity = prop_scrolled**1.5
        if y_pos > HORIZON_Y + 2:  # Don't draw exactly on horizon
            draw_glow_line(
                draw, (0, y_pos), (WIDTH, y_pos), C_GRID, 1, glow_intensity=intensity
            )

    # 4. Draw Cosmic Structure (Rotating and Drifting)
    cx, cy = structure_center_base
    # Slow drift left
    cx = cx - (progress * 40)
    current_center = (cx, cy)

    # Rotation angles based on progress
    angle_y = progress * 360  # Full spin around Y axis
    angle_z = progress * 180  # Slow spin around Z axis

    transformed_vertices = []
    for vx, vy, vz in structure_vertices:
        # 1. Rotate around Y axis (horizontal spin)
        # Simplified 3D rotation projection
        rad_y = math.radians(angle_y)
        rx = vx * math.cos(rad_y) - vz * math.sin(rad_y)
        rz = vx * math.sin(rad_y) + vz * math.cos(rad_y)

        # 2. Rotate around Z axis (tilt spin)
        rad_z = math.radians(angle_z)
        rrx = rx * math.cos(rad_z) - vy * math.sin(rad_z)
        rry = rx * math.sin(rad_z) + vy * math.cos(rad_z)

        # 3. Project to 2D (Weak perspective scaling based on Z depth)
        scale = 1.2 / (1 + rz / 400)
        final_x = cx + rrx * scale
        final_y = cy + rry * scale
        transformed_vertices.append((final_x, final_y))

    # Draw edges
    for start_idx, end_idx in structure_edges:
        p1 = transformed_vertices[start_idx]
        p2 = transformed_vertices[end_idx]
        # Use Cyan/Purple gradient based on Y position for the lines
        avg_y = (p1[1] + p2[1]) / 2
        if avg_y < cy:
            edge_color = C_CYAN
        else:
            edge_color = C_PURPLE

        draw_glow_line(draw, p1, p2, edge_color, 2)

    # Draw bright vertices (scintillating joints)
    for vx, vy in transformed_vertices:
        # Scintillate vertices randomly
        vert_bright = random.randint(150, 255)
        draw.ellipse(
            [(vx - 2, vy - 2), (vx + 2, vy + 2)], fill=(255, 255, 255, vert_bright)
        )

    # Composite overlay onto background
    comp = Image.alpha_composite(img, overlay)

    # Optional: Add slight scanline effect for extra retro feel
    scan_overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    scan_draw = ImageDraw.Draw(scan_overlay)
    for y in range(0, HEIGHT, 4):
        scan_draw.line([(0, y), (WIDTH, y)], fill=(0, 0, 0, 50), width=1)
    comp = Image.alpha_composite(comp, scan_overlay)

    # Convert back to RGB for GIF saving (prevents palette issues sometimes)
    frames.append(comp.convert("RGB"))
    print(f"Frame {i+1}/{FRAMES} rendered.")

print("Saving GIF...")
# Save the frames as a GIF
frames[0].save(
    "synthwave_cosmos.gif",
    save_all=True,
    append_images=frames[1:],
    optimize=False,
    duration=DURATION,
    loop=0,
)
print("GIF generated successfully!")
