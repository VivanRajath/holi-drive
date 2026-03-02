"""
Professional Badge Generator for LCC Holi Color Donation Drive
Creates a 1080x1080 premium Holi-themed participation badge
"""

from PIL import Image, ImageDraw, ImageFont
import urllib.request
import io
import os
import random

SIZE = 1080

# Soft Holi pastel palette
HOLI_COLORS = [
    (255, 183, 197, 120),
    (255, 214, 165, 120),
    (255, 236, 179, 120),
    (197, 225, 165, 120),
    (179, 229, 252, 120),
    (225, 190, 231, 120)
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
    "name": "https://github.com/google/fonts/raw/main/ofl/greatvibes/GreatVibes-Regular.ttf"
}


def download_fonts():
    for name, url in FONT_URLS.items():
        path = f"{FONTS_DIR}/{name}.ttf"
        if not os.path.exists(path):
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as r, open(path, "wb") as f:
                f.write(r.read())


download_fonts()


def font(name, size):
    return ImageFont.truetype(f"{FONTS_DIR}/{name}.ttf", size)


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


def center_text(draw, text, y, font_obj, fill):
    bbox = draw.textbbox((0, 0), text, font=font_obj)
    w = bbox[2] - bbox[0]
    x = (SIZE - w) // 2
    draw.text((x, y), text, font=font_obj, fill=fill)
    return bbox[3] - bbox[1]


def generate_badge(name):

    img = Image.new("RGBA", (SIZE, SIZE), BG)
    draw = ImageDraw.Draw(img)

    # Holi splashes
    holi_splash(draw)
    holi_splash(draw)

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

        y = logo_y + logo_size + 60

    else:
        y = 140

    h = center_text(draw, "LEAF CLOTHING COMPANY", y, font("heading", 40), TEXT)
    y += h + 20

    h = center_text(draw, "HOLI COLOR DONATION DRIVE", y, font("heading", 48), PINK)
    y += h + 40

    draw.line((280, y, 800, y), fill=PINK, width=4)
    y += 50

    h = center_text(draw, "PARTICIPATION BADGE", y, font("heading", 60), TEXT)
    y += h + 40

    h = center_text(draw, "Presented To", y, font("body", 32), TEXT)
    y += h + 20

    h = center_text(draw, name, y, font("name", 120), PINK)
    y += h + 40

    center_text(
        draw,
        "For contributing to the Holi Color Donation Drive",
        y,
        font("body", 30),
        TEXT
    )

    buffer = io.BytesIO()
    img.convert("RGB").save(buffer, "PNG")

    return buffer.getvalue()