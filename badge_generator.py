"""
Professional Badge Generator for LCC Holi Color Donation Drive
Creates a 1080x1080 premium Holi-themed participation badge
with vibrant color splashes and modern typography
"""

from PIL import Image, ImageDraw, ImageFont
import urllib.request
import io
import os
import random
import math

SIZE = 1080

# Vibrant Holi color palette — splashes
HOLI_COLORS = [
    (255, 183, 197, 120),   # soft pink
    (255, 214, 165, 120),   # peach
    (255, 236, 179, 120),   # light yellow
    (197, 225, 165, 120),   # mint green
    (179, 229, 252, 120),   # sky blue
    (225, 190, 231, 120),   # lavender
]

# Brighter accent splashes
ACCENT_COLORS = [
    (233, 30, 99, 80),      # hot pink
    (255, 152, 0, 80),      # orange
    (156, 39, 176, 70),     # purple
    (76, 175, 80, 70),      # green
    (33, 150, 243, 70),     # blue
    (255, 87, 34, 70),      # deep orange
    (0, 188, 212, 70),      # cyan
    (255, 193, 7, 80),      # amber
]

BG = (255, 248, 250)
TEXT = (40, 40, 40)
PINK = (233, 30, 99)

# Fonts
FONTS_DIR = "fonts"
os.makedirs(FONTS_DIR, exist_ok=True)

FONT_URLS = {
    "heading": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf",
    "body": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf",
    "name": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf",
    "name_extra": "https://github.com/google/fonts/raw/main/ofl/outfit/Outfit%5Bwght%5D.ttf",
}


def download_fonts():
    for name, url in FONT_URLS.items():
        path = f"{FONTS_DIR}/{name}.ttf"
        if not os.path.exists(path):
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as r, open(path, "wb") as f:
                    f.write(r.read())
            except Exception as e:
                print(f"Font download failed for {name}: {e}")


download_fonts()


def font(name, size):
    path = f"{FONTS_DIR}/{name}.ttf"
    if os.path.exists(path):
        return ImageFont.truetype(path, size)
    # Fallback to heading font if specific font missing
    return ImageFont.truetype(f"{FONTS_DIR}/heading.ttf", size)


def load_logo():
    """Load LCC logo if present"""
    paths = [
        "logo.png",
        "public/logo.png",
        "../public/logo.png"
    ]

    for p in paths:
        if os.path.exists(p):
            return Image.open(p).convert("RGBA")

    return None


def draw_color_burst(draw, cx, cy, radius, color, num_rays=12):
    """Draw a starburst / color powder burst effect"""
    for i in range(num_rays):
        angle = (2 * math.pi / num_rays) * i + random.uniform(-0.2, 0.2)
        ray_len = random.uniform(radius * 0.4, radius)
        ray_width = random.uniform(radius * 0.15, radius * 0.4)

        ex = cx + math.cos(angle) * ray_len
        ey = cy + math.sin(angle) * ray_len

        # Draw tapered ray as a polygon
        perp_angle = angle + math.pi / 2
        hw = ray_width * 0.5
        points = [
            (cx + math.cos(perp_angle) * hw * 0.3, cy + math.sin(perp_angle) * hw * 0.3),
            (cx - math.cos(perp_angle) * hw * 0.3, cy - math.sin(perp_angle) * hw * 0.3),
            (ex - math.cos(perp_angle) * hw * 0.1, ey - math.sin(perp_angle) * hw * 0.1),
            (ex + math.cos(perp_angle) * hw * 0.1, ey + math.sin(perp_angle) * hw * 0.1),
        ]
        draw.polygon(points, fill=color)

    # Central circle
    cr = radius * 0.25
    draw.ellipse((cx - cr, cy - cr, cx + cr, cy + cr), fill=color)


def draw_powder_dots(draw, cx, cy, radius, color, count=20):
    """Scatter small dots around a center point like powder particles"""
    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(0, radius)
        x = cx + math.cos(angle) * dist
        y = cy + math.sin(angle) * dist
        r = random.uniform(2, 8)
        dot_color = (*color[:3], random.randint(40, color[3]))
        draw.ellipse((x - r, y - r, x + r, y + r), fill=dot_color)


def draw_ring_splash(draw, cx, cy, outer_r, color):
    """Draw a donut/ring splash"""
    inner_r = outer_r * random.uniform(0.4, 0.7)
    # Draw outer
    draw.ellipse((cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r), fill=color)
    # Cut inner with background
    bg_with_alpha = (*BG[:3], 0)
    draw.ellipse((cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r), fill=bg_with_alpha)


def holi_splash(draw):
    """Random Holi powder splashes only on outer edges"""

    SAFE_MARGIN = 220
    splash_count = random.randint(10, 16)

    for _ in range(splash_count):

        side = random.choice(["top", "bottom", "left", "right"])

        if side == "top":
            x = random.randint(0, SIZE)
            y = random.randint(0, SAFE_MARGIN)

        elif side == "bottom":
            x = random.randint(0, SIZE)
            y = random.randint(SIZE - SAFE_MARGIN, SIZE)

        elif side == "left":
            x = random.randint(0, SAFE_MARGIN)
            y = random.randint(0, SIZE)

        else:
            x = random.randint(SIZE - SAFE_MARGIN, SIZE)
            y = random.randint(0, SIZE)

        color = random.choice(HOLI_COLORS)
        radius = random.randint(70, 180)

        for _ in range(random.randint(8, 15)):

            r = random.randint(radius // 3, radius)
            dx = random.randint(-radius, radius)
            dy = random.randint(-radius, radius)

            draw.ellipse(
                (x + dx - r, y + dy - r, x + dx + r, y + dy + r),
                fill=color
            )


def add_decorative_splashes(draw):
    """Add colorful SVG-like decorative elements: bursts, rings, dots"""

    SAFE_MARGIN = 200  # keep center text area clear

    # --- Corner color bursts ---
    corners = [
        (random.randint(40, 160), random.randint(40, 160)),
        (SIZE - random.randint(40, 160), random.randint(40, 160)),
        (random.randint(40, 160), SIZE - random.randint(40, 160)),
        (SIZE - random.randint(40, 160), SIZE - random.randint(40, 160)),
    ]

    for i, (cx, cy) in enumerate(corners):
        color = ACCENT_COLORS[i % len(ACCENT_COLORS)]
        draw_color_burst(draw, cx, cy, random.randint(60, 110), color, num_rays=random.randint(8, 14))
        draw_powder_dots(draw, cx, cy, random.randint(80, 140), color, count=random.randint(15, 30))

    # --- Edge splashes with rings ---
    for _ in range(random.randint(3, 5)):
        side = random.choice(["top", "bottom", "left", "right"])
        if side == "top":
            x, y = random.randint(200, SIZE - 200), random.randint(20, 100)
        elif side == "bottom":
            x, y = random.randint(200, SIZE - 200), random.randint(SIZE - 100, SIZE - 20)
        elif side == "left":
            x, y = random.randint(20, 100), random.randint(200, SIZE - 200)
        else:
            x, y = random.randint(SIZE - 100, SIZE - 20), random.randint(200, SIZE - 200)

        color = random.choice(ACCENT_COLORS)
        draw_ring_splash(draw, x, y, random.randint(25, 55), color)
        draw_powder_dots(draw, x, y, random.randint(40, 80), color, count=random.randint(10, 20))

    # --- Floating powder dots along edges ---
    for _ in range(random.randint(40, 70)):
        # Place dots only in the margins
        if random.random() < 0.5:
            x = random.randint(0, SIZE)
            y = random.choice([random.randint(0, SAFE_MARGIN), random.randint(SIZE - SAFE_MARGIN, SIZE)])
        else:
            x = random.choice([random.randint(0, SAFE_MARGIN), random.randint(SIZE - SAFE_MARGIN, SIZE)])
            y = random.randint(0, SIZE)

        r = random.uniform(3, 12)
        color = random.choice(ACCENT_COLORS + HOLI_COLORS)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=color)


def center_text(draw, text, y, font_obj, fill):
    bbox = draw.textbbox((0, 0), text, font=font_obj)
    w = bbox[2] - bbox[0]
    x = (SIZE - w) // 2
    draw.text((x, y), text, font=font_obj, fill=fill)
    return bbox[3] - bbox[1]


def draw_decorative_line(draw, y):
    """Draw a gradient-like decorative divider line"""
    line_width = 520
    x_start = (SIZE - line_width) // 2
    x_end = x_start + line_width

    # Main line
    draw.line((x_start, y, x_end, y), fill=PINK, width=3)

    # Small diamond in center
    cx = SIZE // 2
    diamond_size = 8
    draw.polygon([
        (cx, y - diamond_size),
        (cx + diamond_size, y),
        (cx, y + diamond_size),
        (cx - diamond_size, y),
    ], fill=PINK)

    # Small circles at ends
    draw.ellipse((x_start - 4, y - 4, x_start + 4, y + 4), fill=PINK)
    draw.ellipse((x_end - 4, y - 4, x_end + 4, y + 4), fill=PINK)


def generate_badge(name):

    img = Image.new("RGBA", (SIZE, SIZE), BG)
    draw = ImageDraw.Draw(img)

    # Layer 1: Soft Holi splashes (background)
    holi_splash(draw)
    holi_splash(draw)

    # Layer 2: Decorative color bursts, rings, and dots
    add_decorative_splashes(draw)

    # --- LOGO ---
    logo = load_logo()

    if logo:
        logo_size = 160
        logo = logo.resize((logo_size, logo_size), Image.LANCZOS)

        logo_x = (SIZE - logo_size) // 2
        logo_y = 60

        # white circle behind logo
        draw.ellipse(
            (logo_x - 15, logo_y - 15, logo_x + logo_size + 15, logo_y + logo_size + 15),
            fill=(255, 255, 255)
        )

        img.paste(logo, (logo_x, logo_y), logo)

        y = logo_y + logo_size + 50

    else:
        y = 140

    h = center_text(draw, "LEAF CLOTHING COMPANY", y, font("heading", 40), TEXT)
    y += h + 16

    h = center_text(draw, "HOLI COLOR DONATION DRIVE", y, font("heading", 48), PINK)
    y += h + 35

    draw_decorative_line(draw, y)
    y += 45

    h = center_text(draw, "PARTICIPATION BADGE", y, font("heading", 56), TEXT)
    y += h + 35

    h = center_text(draw, "Presented To", y, font("body", 30), (100, 100, 100))
    y += h + 18

    # --- Name in bold modern font (NOT cursive) ---
    # Try Outfit first, fallback to Poppins Bold
    name_font_size = 88
    # Auto-size: if name is long, reduce font size
    if len(name) > 18:
        name_font_size = 68
    elif len(name) > 12:
        name_font_size = 78

    try:
        name_font = font("name_extra", name_font_size)
    except Exception:
        name_font = font("name", name_font_size)

    h = center_text(draw, name.upper(), y, name_font, PINK)
    y += h + 30

    # Another decorative line under name
    draw_decorative_line(draw, y)
    y += 40

    center_text(
        draw,
        "For contributing to the Holi Color Donation Drive",
        y,
        font("body", 28),
        TEXT
    )

    y += 50

    center_text(
        draw,
        "#HoliForGood  ·  #LCCDrive",
        y,
        font("body", 22),
        (150, 150, 150)
    )

    buffer = io.BytesIO()
    img.convert("RGB").save(buffer, "PNG")

    return buffer.getvalue()