"""
Professional Badge Generator for LCC Holi Color Donation Drive
Creates a 1080x1080 premium Holi-themed participation badge
White background with vibrant color splashes around the edges
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import os
import random
import math

SIZE = 1080

# ── Holi color palette ────────────────────────────────────────────────────────

HOLI_COLORS = [
    (255, 80,  150, 90),
    (255, 160,  40, 90),
    (250, 220,  40, 90),
    (60,  190,  90, 90),
    (50,  160, 240, 90),
    (160,  60, 210, 90),
    (0,   200, 210, 90),
    (255, 100,  50, 90),
]

ACCENT_COLORS = [
    (233,  30,  99, 170),
    (255, 140,   0, 170),
    (255, 210,   0, 170),
    (30,  180,  70, 160),
    (20,  130, 240, 160),
    (150,  20, 200, 150),
    (0,   190, 200, 160),
    (255,  60,  30, 160),
]

BG   = (255, 255, 255)
TEXT = (28,  28,  28)
PINK = (228,  38,  97)

# ── Font resolution ───────────────────────────────────────────────────────────

_BASE = os.path.dirname(os.path.abspath(__file__))

_BOLD_CANDIDATES = [
    os.path.join(_BASE, "fonts", "heading.ttf"),
    os.path.join(_BASE, "fonts", "bold.ttf"),
    "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf",
]

_REGULAR_CANDIDATES = [
    os.path.join(_BASE, "fonts", "body.ttf"),
    os.path.join(_BASE, "fonts", "regular.ttf"),
    "/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf",
]

_BOLD_PATH    = next((p for p in _BOLD_CANDIDATES    if p and os.path.exists(p)), None)
_REGULAR_PATH = next((p for p in _REGULAR_CANDIDATES if p and os.path.exists(p)), None)
_SCRIPT_PATH  = os.path.join(_BASE, "GreatVibes-Regular.ttf") if os.path.exists(os.path.join(_BASE, "GreatVibes-Regular.ttf")) else None
_NAME_PATH    = _SCRIPT_PATH or (os.path.join(_BASE, "fonts", "name_extra.ttf") if os.path.exists(os.path.join(_BASE, "fonts", "name_extra.ttf")) else None)

def get_bold(size):
    return ImageFont.truetype(_BOLD_PATH, size) if _BOLD_PATH else ImageFont.load_default()

def get_regular(size):
    path = _REGULAR_PATH or _BOLD_PATH
    return ImageFont.truetype(path, size) if path else ImageFont.load_default()

def get_name(size):
    path = _NAME_PATH or _REGULAR_PATH
    return ImageFont.truetype(path, size) if path else ImageFont.load_default()

# ── Splash helpers ────────────────────────────────────────────────────────────

def _blob(draw, cx, cy, radius, color, rng):
    n, pts = 13, []
    for i in range(n):
        a = (2 * math.pi / n) * i
        r = radius * rng.uniform(0.68, 1.0)
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    draw.polygon(pts, fill=color)

def _burst(draw, cx, cy, radius, color, rng):
    rays = rng.randint(9, 13)
    for i in range(rays):
        angle = (2 * math.pi / rays) * i + rng.uniform(-0.3, 0.3)
        rlen  = radius * rng.uniform(0.5, 1.0)
        rw    = radius * rng.uniform(0.18, 0.35)
        ex    = cx + math.cos(angle) * rlen
        ey    = cy + math.sin(angle) * rlen
        perp  = angle + math.pi / 2
        hw    = rw * 0.5
        pts   = [
            (cx + math.cos(perp) * hw * 0.3,  cy + math.sin(perp) * hw * 0.3),
            (cx - math.cos(perp) * hw * 0.3,  cy - math.sin(perp) * hw * 0.3),
            (ex - math.cos(perp) * hw * 0.07, ey - math.sin(perp) * hw * 0.07),
            (ex + math.cos(perp) * hw * 0.07, ey + math.sin(perp) * hw * 0.07),
        ]
        draw.polygon(pts, fill=color)
    cr = radius * 0.22
    draw.ellipse((cx - cr, cy - cr, cx + cr, cy + cr), fill=color)

def _dots(draw, cx, cy, spread, color, count, rng):
    for _ in range(count):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0, spread)
        x, y = cx + math.cos(a) * d, cy + math.sin(a) * d
        r = rng.uniform(3, 11)
        alpha = rng.randint(100, color[3]) if len(color) == 4 else 180
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(*color[:3], alpha))

def _edge_point(size, margin, rng):
    side = rng.randint(0, 3)
    if side == 0: return rng.randint(0, size), rng.randint(0, margin)
    if side == 1: return rng.randint(0, size), rng.randint(size - margin, size)
    if side == 2: return rng.randint(0, margin), rng.randint(0, size)
    return             rng.randint(size - margin, size), rng.randint(0, size)

def _build_splashes(size, rng):
    MARGIN = 240
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # Layer 1: blurred glow
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(glow)
    for _ in range(22):
        cx, cy = _edge_point(size, MARGIN, rng)
        _blob(gd, cx, cy, rng.randint(80, 200), rng.choice(HOLI_COLORS), rng)
    result = Image.alpha_composite(result, glow.filter(ImageFilter.GaussianBlur(30)))

    # Layer 2: vivid bursts + blobs
    mid = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    md  = ImageDraw.Draw(mid)
    corners = [
        (rng.randint(25, 120), rng.randint(25, 120)),
        (size - rng.randint(25, 120), rng.randint(25, 120)),
        (rng.randint(25, 120), size - rng.randint(25, 120)),
        (size - rng.randint(25, 120), size - rng.randint(25, 120)),
    ]
    for i, (cx, cy) in enumerate(corners):
        _burst(md, cx, cy, rng.randint(65, 110), ACCENT_COLORS[i % len(ACCENT_COLORS)], rng)
        _blob(md, cx, cy, rng.randint(35, 65), (*ACCENT_COLORS[(i+2)%len(ACCENT_COLORS)][:3], 130), rng)
    for _ in range(rng.randint(14, 20)):
        cx, cy = _edge_point(size, MARGIN, rng)
        _blob(md, cx, cy, rng.randint(35, 95), rng.choice(ACCENT_COLORS), rng)
    result = Image.alpha_composite(result, mid.filter(ImageFilter.GaussianBlur(3)))

    # Layer 3: powder dots
    dots = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    dd   = ImageDraw.Draw(dots)
    for i, (cx, cy) in enumerate(corners):
        _dots(dd, cx, cy, rng.randint(100, 170), ACCENT_COLORS[i%len(ACCENT_COLORS)], rng.randint(25, 40), rng)
    for _ in range(rng.randint(65, 95)):
        cx, cy = _edge_point(size, MARGIN, rng)
        col    = rng.choice(HOLI_COLORS + ACCENT_COLORS)
        r      = rng.uniform(3, 13)
        dd.ellipse((cx-r, cy-r, cx+r, cy+r), fill=(*col[:3], rng.randint(120, 210)))
    result = Image.alpha_composite(result, dots)
    return result

# ── Text helpers ──────────────────────────────────────────────────────────────

def center_text(draw, text, y, fnt, fill, size=SIZE):
    bb = draw.textbbox((0, 0), text, font=fnt)
    w  = bb[2] - bb[0]
    draw.text(((size - w) // 2, y), text, font=fnt, fill=fill)
    return bb[3] - bb[1]

def draw_decorative_line(draw, y, size=SIZE):
    pad  = 210
    x0, x1, cx, ds = pad, size - pad, size // 2, 7
    half = cx - ds - 6
    for x in range(x0, cx - ds - 4):
        t = (x - x0) / max(half, 1)
        draw.line((x, y, x+1, y), fill=(*PINK, int(40 + 180*t)), width=2)
    for x in range(cx + ds + 4, x1):
        t = (x1 - x) / max(half, 1)
        draw.line((x, y, x+1, y), fill=(*PINK, int(40 + 180*t)), width=2)
    draw.polygon([(cx, y-ds),(cx+ds, y),(cx, y+ds),(cx-ds, y)], fill=PINK)
    draw.ellipse((x0-5, y-5, x0+5, y+5), fill=(*PINK, 160))
    draw.ellipse((x1-5, y-5, x1+5, y+5), fill=(*PINK, 160))

# ── Main ──────────────────────────────────────────────────────────────────────

def generate_badge(name, date=None):
    rng    = random.Random()
    canvas = Image.new("RGBA", (SIZE, SIZE), (*BG, 255))

    # Splashes
    canvas = Image.alpha_composite(canvas, _build_splashes(SIZE, rng))

    # White vignette fade toward centre
    vig = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    vd  = ImageDraw.Draw(vig)
    for i in range(80):
        alpha = int(220 * (1 - i/80) ** 2.2)
        vd.rectangle((i*2, i*2, SIZE-i*2, SIZE-i*2), outline=(255,255,255,alpha), width=2)
    canvas = Image.alpha_composite(canvas, vig)

    draw = ImageDraw.Draw(canvas)

    # Border
    draw.rounded_rectangle((18,18,SIZE-18,SIZE-18), radius=28, outline=(*PINK,70), width=3)
    draw.rounded_rectangle((28,28,SIZE-28,SIZE-28), radius=20, outline=(255,255,255,200), width=2)

    # Logo
    logo = None
    for rel in ["logo.png","public/logo.png","../public/logo.png",
                os.path.join(_BASE,"logo.png"), os.path.join(_BASE,"public","logo.png")]:
        if os.path.exists(rel):
            try: logo = Image.open(rel).convert("RGBA")
            except: pass
            break

    if logo:
        ls     = 150
        logo   = logo.resize((ls, ls), Image.LANCZOS)
        lx, ly = (SIZE - ls)//2, 55
        draw.ellipse((lx-14, ly-14, lx+ls+14, ly+ls+14), fill=(255,255,255))
        canvas.paste(logo, (lx, ly), logo)
        draw = ImageDraw.Draw(canvas)
        y    = ly + ls + 45
    else:
        y = 130

    # Brand
    h = center_text(draw, "LEAF CLOTHING COMPANY", y, get_bold(36), TEXT)
    y += h + 12

    # Colour dot row
    dr, gap   = 7, 20
    dot_cols  = [c[:3] for c in ACCENT_COLORS]
    total     = len(dot_cols) * (dr*2+gap) - gap
    dx        = (SIZE - total) // 2
    for col in dot_cols:
        draw.ellipse((dx, y, dx+dr*2, y+dr*2), fill=col)
        dx += dr*2 + gap
    y += dr*2 + 20

    # Event title
    h = center_text(draw, "HOLI COLOR DONATION DRIVE", y, get_bold(50), PINK)
    y += h + 28

    draw_decorative_line(draw, y)
    y += 42

    h = center_text(draw, "PARTICIPATION BADGE", y, get_bold(52), TEXT)
    y += h + 28

    h = center_text(draw, "Presented To", y, get_regular(27), (110,110,110))
    y += h + 16

    # Name — elegant script font, mixed case for readability
    name_str  = (name or "Your Name").strip().title()
    name_size = (100 if len(name_str)<=10 else 86 if len(name_str)<=14
                 else 72 if len(name_str)<=18 else 58)
    f_name    = get_name(name_size)

    h = center_text(draw, name_str, y, f_name, PINK)
    y += h + 14

    draw_decorative_line(draw, y)
    y += 36

    h = center_text(draw, "For contributing to the Holi Color Donation Drive",
                    y, get_regular(26), TEXT)
    y += h + 14

    # Date — pink, nice font, below the contribution line
    if date:
        h = center_text(draw, date, y, get_name(28), PINK)
        y += h + 14
    else:
        y += 6

    center_text(draw, "#HoliForGood  \u00b7  #LCCDrive",
                y, get_regular(22), (140,140,140))

    # Bottom colour strip
    seg_w = SIZE // len(ACCENT_COLORS)
    for i, col in enumerate(ACCENT_COLORS):
        draw.rectangle((i*seg_w, SIZE-26, (i+1)*seg_w, SIZE), fill=(*col[:3], 230))

    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, "PNG")
    return buf.getvalue()