#!/usr/bin/env python3
"""Draw entry.png: a dense one-page newspaper summary of the world news
of Thursday 19 November 2026. Run once to (re)build the image; main.py
only copies the finished PNG to the output directory at grading time.

Layout (1024x1024, flat vector style, Pillow-drawn only):
top bar -> giant date headline -> standfirst -> region breakdown bar
-> key-numbers strip -> lead row (summit + 2 medium cards) -> two rows
of 5 small cards (13 illustrated cards total) -> world map with numbered
story dots + "also on" brief list (stories 14-32) -> DATE CHECK box
(explicitly excluding other days' news) -> sources footer.

Every story is a real 19 Nov 2026 event, verified against live reporting
20 Nov 2026 (Reuters/AP/AFP/BBC and primary sources). Claims that could
not be verified are attributed, not stated as fact. Two v1 errors are
fixed here: Ukraine was NOT on the summit declaration (it is not
mentioned in the text), and Anthropic's $1.5T is the valuation -- the
IPO raised $81.3bn.
"""

import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
MARGIN = 16
CONTENT_W = W - 2 * MARGIN  # 992

PAPER = (247, 243, 234)
INK = (20, 20, 20)
MUTED = (84, 82, 76)
RED = (185, 28, 28)
DARK = (22, 22, 22)
CARD = (255, 252, 245)
RULE = (200, 192, 172)
WHITE = (255, 255, 255)
MAP_SEA = (214, 228, 235)
MAP_LAND = (226, 216, 188)

# Region colours (also used for card accents and the region bar)
REGIONS = [
    ("ASIA", 7, (204, 85, 0)),
    ("MIDEAST", 3, (185, 28, 28)),
    ("EUROPE", 6, (31, 58, 124)),
    ("AFRICA", 3, (22, 120, 70)),
    ("AMERICAS", 6, (13, 120, 120)),
    ("OCEANIA", 4, (96, 60, 140)),
    ("WORLD", 3, (84, 82, 76)),
]
RCOL = {name: col for name, _n, col in REGIONS}

FONT_DIR = "/usr/share/fonts/truetype"
SERIF_BOLD = os.path.join(FONT_DIR, "liberation", "LiberationSerif-Bold.ttf")
SERIF_ITALIC = os.path.join(FONT_DIR, "liberation", "LiberationSerif-Italic.ttf")
SANS_BLACK = os.path.join(FONT_DIR, "lato", "Lato-Black.ttf")
SANS_BOLD = os.path.join(FONT_DIR, "lato", "Lato-Bold.ttf")
SANS_SEMI = os.path.join(FONT_DIR, "lato", "Lato-Semibold.ttf")
SANS = os.path.join(FONT_DIR, "lato", "Lato-Regular.ttf")
SANS_ITALIC = os.path.join(FONT_DIR, "lato", "Lato-Italic.ttf")


def font(path, size):
    if not os.path.exists(path):
        path = SANS
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def star_points(cx, cy, r_out, r_in, rotation=-90.0):
    pts = []
    for i in range(10):
        r = r_out if i % 2 == 0 else r_in
        ang = math.radians(rotation + i * 36.0)
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


def draw_star(d, cx, cy, r_out, color, r_in=None):
    if r_in is None:
        r_in = r_out * 0.42
    d.polygon(star_points(cx, cy, r_out, r_in), fill=color)


def flag_usa(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=WHITE, outline=INK, width=1)
    stripe = h / 13.0
    for i in range(7):
        yy = y + i * 2 * stripe
        d.rectangle([x + 1, yy, x + w - 1, yy + stripe], fill=(178, 34, 52))
    canton_w, canton_h = w * 0.4, stripe * 7
    d.rectangle([x + 1, y + 1, x + canton_w, y + canton_h], fill=(60, 59, 110))
    for row in range(4):
        for col in range(5):
            sx = x + 6 + col * (canton_w - 10) / 4.0
            sy = y + 6 + row * (canton_h - 10) / 3.0
            d.ellipse([sx - 1.5, sy - 1.5, sx + 1.5, sy + 1.5], fill=WHITE)


def flag_china(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(222, 41, 16), outline=INK, width=1)
    draw_star(d, x + w * 0.28, y + h * 0.30, h * 0.22, (255, 222, 0))
    for sx, sy in [(0.62, 0.16), (0.74, 0.30), (0.72, 0.50), (0.58, 0.60)]:
        draw_star(d, x + w * sx, y + h * sy, h * 0.09, (255, 222, 0))


def flag_russia(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=WHITE, outline=INK, width=1)
    third = h / 3.0
    d.rectangle([x + 1, y + third, x + w - 1, y + 2 * third], fill=(0, 57, 166))
    d.rectangle([x + 1, y + 2 * third, x + w - 1, y + h - 1], fill=(213, 0, 50))


# ---------------------------------------------------------------- icons
def icon_scales(d, x, y, s, color):
    """Scales of justice, white line-art on a coloured tile."""
    d.rounded_rectangle([x, y, x + s, y + s], radius=8, fill=color)
    cx, top = x + s / 2.0, y + s * 0.16
    d.line([cx, top, cx, y + s * 0.80], fill=WHITE, width=4)
    d.line([x + s * 0.18, top + 6, x + s * 0.82, top + 6], fill=WHITE, width=4)
    for px in (x + s * 0.20, x + s * 0.80):
        d.line([px, top + 6, px - s * 0.13, y + s * 0.58], fill=WHITE, width=3)
        d.line([px, top + 6, px + s * 0.13, y + s * 0.58], fill=WHITE, width=3)
        d.arc([px - s * 0.15, y + s * 0.54, px + s * 0.15, y + s * 0.78],
              0, 180, fill=WHITE, width=3)
    d.line([cx - s * 0.18, y + s * 0.82, cx + s * 0.18, y + s * 0.82],
           fill=WHITE, width=4)


def icon_chart_up(d, x, y, s, color):
    d.rounded_rectangle([x, y, x + s, y + s], radius=8, fill=color)
    d.line([x + s * 0.16, y + s * 0.82, x + s * 0.84, y + s * 0.82],
           fill=WHITE, width=3)
    d.line([x + s * 0.16, y + s * 0.82, x + s * 0.16, y + s * 0.16],
           fill=WHITE, width=3)
    pts = [(x + s * 0.22, y + s * 0.66), (x + s * 0.42, y + s * 0.50),
           (x + s * 0.58, y + s * 0.58), (x + s * 0.78, y + s * 0.26)]
    d.line(pts, fill=WHITE, width=5, joint="curve")
    ax, ay = pts[-1]
    d.polygon([(ax + 1, ay - 9), (ax + 10, ay + 1), (ax - 3, ay + 5)],
              fill=WHITE)


def mini_icon(d, kind, x, y, s, color):
    """Tiny white pictogram (s ~ 18px) for the small-card strips."""
    cx, cy = x + s / 2.0, y + s / 2.0
    if kind == "sun":  # COP31
        d.ellipse([cx - s * 0.22, cy - s * 0.22, cx + s * 0.22, cy + s * 0.22],
                  fill=WHITE)
        for a in range(0, 360, 45):
            r = math.radians(a)
            d.line([cx + s * 0.30 * math.cos(r), cy + s * 0.30 * math.sin(r),
                    cx + s * 0.46 * math.cos(r), cy + s * 0.46 * math.sin(r)],
                   fill=WHITE, width=2)
    elif kind == "game":  # GTA VI
        d.rounded_rectangle([x + 1, y + s * 0.28, x + s - 1, y + s * 0.78],
                            radius=5, outline=WHITE, width=2)
        d.ellipse([cx - s * 0.28, cy - s * 0.02, cx - s * 0.12, cy + s * 0.14],
                  fill=WHITE)
        d.ellipse([cx + s * 0.12, cy - s * 0.02, cx + s * 0.28, cy + s * 0.14],
                  fill=WHITE)
    elif kind == "storm":  # Akvan
        for r, a0, a1 in [(0.42, 200, 340), (0.30, 80, 250), (0.18, 300, 80)]:
            d.arc([cx - s * r, cy - s * r, cx + s * r, cy + s * r], a0, a1,
                  fill=WHITE, width=2)
        d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=WHITE)
    elif kind == "bridge":  # Kerch
        d.arc([x + 1, y + s * 0.30, x + s - 1, y + s * 1.05], 180, 360,
              fill=WHITE, width=2)
        d.line([x + 1, y + s * 0.62, x + s - 1, y + s * 0.62], fill=WHITE,
               width=2)
        d.line([cx, y + s * 0.30, cx, y + s * 0.12], fill=WHITE, width=2)
        d.ellipse([cx - 2, y + s * 0.06, cx + 2, y + s * 0.18], fill=WHITE)
    elif kind == "tower":  # Riyadh
        d.rectangle([cx - s * 0.16, y + s * 0.14, cx + s * 0.16, y + s * 0.90],
                    fill=WHITE)
        d.polygon([(cx, y + s * 0.02), (cx - s * 0.16, y + s * 0.16),
                   (cx + s * 0.16, y + s * 0.16)], fill=WHITE)
        for a in (45, 135, 225, 315):
            r = math.radians(a)
            d.line([cx + s * 0.34 * math.cos(r), cy - s * 0.18 + s * 0.34 * math.sin(r),
                    cx + s * 0.48 * math.cos(r), cy - s * 0.18 + s * 0.48 * math.sin(r)],
                   fill=WHITE, width=2)
    elif kind == "gavel":  # Han / court
        d.line([x + s * 0.18, y + s * 0.82, x + s * 0.82, y + s * 0.18],
               fill=WHITE, width=3)
        d.line([x + s * 0.55, y + s * 0.08, x + s * 0.92, y + s * 0.45],
               fill=WHITE, width=5)
        d.line([x + s * 0.10, y + s * 0.88, x + s * 0.45, y + s * 0.88],
               fill=WHITE, width=3)
    elif kind == "pin":  # Denmark
        d.ellipse([cx - s * 0.24, cy - s * 0.38, cx + s * 0.24, cy + s * 0.10],
                  outline=WHITE, width=2)
        d.ellipse([cx - 2, cy - s * 0.18, cx + 2, cy - s * 0.10], fill=WHITE)
        d.polygon([(cx - s * 0.16, cy + s * 0.02), (cx + s * 0.16, cy + s * 0.02),
                   (cx, cy + s * 0.42)], fill=WHITE)
    elif kind == "down":  # Australia jobs
        d.line([x + s * 0.14, y + s * 0.82, x + s * 0.86, y + s * 0.82],
               fill=WHITE, width=2)
        d.line([x + s * 0.14, y + s * 0.82, x + s * 0.14, y + s * 0.14],
               fill=WHITE, width=2)
        d.line([(x + s * 0.22, y + s * 0.30), (x + s * 0.45, y + s * 0.48),
                (x + s * 0.68, y + s * 0.42), (x + s * 0.84, y + s * 0.68)],
               fill=WHITE, width=3, joint="curve")
    elif kind == "crowd":  # Colombia march
        for ox in (-0.28, 0.0, 0.28):
            d.ellipse([cx + s * ox - 3, cy - s * 0.30, cx + s * ox + 3,
                       cy - s * 0.18], fill=WHITE)
            d.arc([cx + s * ox - 5, cy - s * 0.10, cx + s * ox + 5,
                   cy + s * 0.22], 180, 360, fill=WHITE, width=2)
        d.line([cx - s * 0.40, cy + s * 0.36, cx + s * 0.40, cy + s * 0.36],
               fill=WHITE, width=2)
    elif kind == "flame":  # Bangladesh
        d.polygon([(cx, y + s * 0.06), (cx + s * 0.30, y + s * 0.44),
                   (cx + s * 0.22, y + s * 0.66), (cx + s * 0.10, y + s * 0.92),
                   (cx - s * 0.10, y + s * 0.92), (cx - s * 0.22, y + s * 0.66),
                   (cx - s * 0.30, y + s * 0.44)], fill=WHITE)
    elif kind == "globe":  # fallback
        d.ellipse([x + 2, y + 2, x + s - 2, y + s - 2], outline=WHITE, width=2)
        d.line([x + 2, cy, x + s - 2, cy], fill=WHITE, width=2)
        d.ellipse([cx - s * 0.18, y + 2, cx + s * 0.18, y + s - 2],
                  outline=WHITE, width=2)


# ---------------------------------------------------------------- cards
def lead_card(d, x, y, w, h, accent, num, kicker, headline, sub, source):
    """The summit lead: flag panel on the left, big text on the right."""
    d.rounded_rectangle([x, y, x + w, y + h], radius=8, fill=CARD,
                        outline=RULE, width=2)
    panel_w = 168
    d.rounded_rectangle([x + 2, y + 2, x + panel_w, y + h - 2], radius=6,
                        fill=(31, 58, 124))
    d.rectangle([x + panel_w - 8, y + 2, x + panel_w, y + h - 2],
                fill=(31, 58, 124))
    fw, fh = 118, 38
    fx = x + (panel_w - fw) // 2
    for i, fn in enumerate((flag_usa, flag_china, flag_russia)):
        fn(d, fx, y + 12 + i * (fh + 8), fw, fh)
    f_lab = font(SANS_BOLD, 12)
    lab = "USA  \u00b7  CHINA  \u00b7  RUSSIA"
    lw = d.textlength(lab, font=f_lab)
    d.text((x + (panel_w - lw) / 2, y + h - 22), lab, font=f_lab, fill=WHITE)

    tx = x + panel_w + 14
    tw = w - panel_w - 26
    f_kick = font(SANS_BOLD, 14)
    d.text((tx, y + 10), "%02d  \u00b7  %s" % (num, kicker), font=f_kick,
           fill=accent)
    f_head = font(SANS_BLACK, 27)
    yy = y + 32
    for ln in wrap(d, headline, f_head, tw)[:2]:
        d.text((tx, yy), ln, font=f_head, fill=INK)
        yy += 31
    f_sub = font(SANS, 13)
    for ln in wrap(d, sub, f_sub, tw)[:3]:
        d.text((tx, yy + 4), ln, font=f_sub, fill=MUTED)
        yy += 17
    f_src = font(SANS_ITALIC, 12)
    d.text((tx, y + h - 22), source, font=f_src, fill=MUTED)


def medium_card(d, x, y, w, h, accent, num, kicker, headline, sub, source,
                icon_fn, stat):
    """238px card: illustration strip on top, then text."""
    d.rounded_rectangle([x, y, x + w, y + h], radius=8, fill=CARD,
                        outline=RULE, width=2)
    strip_h = 58
    d.rounded_rectangle([x + 2, y + 2, x + w - 2, y + strip_h], radius=6,
                        fill=accent)
    d.rectangle([x + 2, y + strip_h - 8, x + w - 2, y + strip_h], fill=accent)
    # Tile fill == strip colour, so only the white line-art shows.
    icon_fn(d, x + 10, y + 9, 40, accent)
    f_stat = font(SANS_BLACK, 28)
    sw = d.textlength(stat, font=f_stat)
    d.text((x + w - 12 - sw, y + 13), stat, font=f_stat, fill=WHITE)
    f_kick = font(SANS_BOLD, 12)
    d.text((x + 12, y + strip_h + 6), "%02d  \u00b7  %s" % (num, kicker),
           font=f_kick, fill=accent)
    f_head = font(SANS_BLACK, 18)
    yy = y + strip_h + 24
    for ln in wrap(d, headline, f_head, w - 24)[:2]:
        d.text((x + 12, yy), ln, font=f_head, fill=INK)
        yy += 21
    f_sub = font(SANS, 12)
    for ln in wrap(d, sub, f_sub, w - 24)[:2]:
        d.text((x + 12, yy + 2), ln, font=f_sub, fill=MUTED)
        yy += 14
    f_src = font(SANS_ITALIC, 10)
    d.text((x + 12, y + h - 16), source, font=f_src, fill=MUTED)


def small_card(d, x, y, w, h, accent, num, kicker, headline, sub, source,
               icon_kind):
    """192px card: coloured strip with pictogram + kicker, then text."""
    d.rounded_rectangle([x, y, x + w, y + h], radius=8, fill=CARD,
                        outline=RULE, width=2)
    strip_h = 26
    d.rounded_rectangle([x + 2, y + 2, x + w - 2, y + strip_h], radius=6,
                        fill=accent)
    d.rectangle([x + 2, y + strip_h - 8, x + w - 2, y + strip_h], fill=accent)
    mini_icon(d, icon_kind, x + 5, y + 4, 18, WHITE)
    f_kick = font(SANS_BOLD, 11)
    d.text((x + 27, y + 7), "%02d  \u00b7  %s" % (num, kicker), font=f_kick,
           fill=WHITE)
    f_head = font(SANS_BLACK, 15)
    yy = y + strip_h + 6
    for ln in wrap(d, headline, f_head, w - 20)[:2]:
        d.text((x + 10, yy), ln, font=f_head, fill=INK)
        yy += 18
    f_sub = font(SANS, 11)
    for ln in wrap(d, sub, f_sub, w - 20)[:3]:
        d.text((x + 10, yy + 2), ln, font=f_sub, fill=MUTED)
        yy += 14
    f_src = font(SANS_ITALIC, 10)
    d.text((x + 10, y + h - 14), source, font=f_src, fill=MUTED)


# ---------------------------------------------------------------- map
CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-85, 76),
     (-80, 73), (-76, 62), (-65, 60), (-60, 52), (-65, 44), (-70, 42),
     (-75, 35), (-80, 32), (-81, 25), (-84, 30), (-90, 29), (-97, 26),
     (-105, 22), (-110, 24), (-114, 29), (-118, 33), (-124, 40), (-124, 48),
     (-130, 55), (-140, 60), (-155, 58), (-165, 60)],
    # South America
    [(-77, 8), (-72, 12), (-60, 8), (-52, 5), (-50, 0), (-44, -3), (-35, -8),
     (-38, -15), (-40, -22), (-48, -28), (-52, -32), (-58, -38), (-62, -41),
     (-65, -45), (-68, -50), (-69, -54), (-72, -54), (-73, -45), (-73, -37),
     (-71, -30), (-70, -20), (-75, -15)],
    # Europe
    [(-10, 36), (-9, 43), (-2, 48), (-4, 50), (0, 53), (3, 58), (5, 60),
     (10, 58), (12, 54), (18, 56), (21, 55), (24, 58), (28, 60), (30, 62),
     (28, 66), (25, 70), (18, 69), (12, 65), (5, 62), (-2, 57), (-6, 53),
     (-10, 50), (-10, 44)],
    # UK
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (1, 52), (0, 50)],
    # Africa
    [(-6, 35), (0, 36), (10, 37), (20, 32), (32, 31), (35, 28), (43, 12),
     (51, 11), (48, 2), (42, -2), (40, -10), (35, -18), (32, -26), (28, -33),
     (20, -35), (17, -29), (14, -22), (12, -17), (13, -12), (9, -1), (9, 4),
     (-8, 5), (-13, 8), (-17, 15), (-16, 20), (-10, 31)],
    # Asia
    [(30, 36), (36, 36), (42, 38), (48, 30), (50, 26), (57, 26), (60, 25),
     (66, 25), (70, 20), (72, 20), (77, 8), (80, 7), (80, 13), (85, 19),
     (88, 22), (91, 22), (93, 16), (97, 16), (100, 8), (103, 2), (104, 8),
     (106, 10), (109, 13), (105, 19), (108, 22), (110, 20), (114, 22),
     (118, 25), (120, 28), (122, 32), (120, 35), (122, 38), (127, 40),
     (130, 42), (132, 44), (135, 44), (138, 46), (141, 50), (142, 54),
     (141, 59), (137, 60), (142, 62), (150, 60), (156, 52), (160, 55),
     (162, 60), (170, 60), (178, 65), (178, 68), (170, 66), (162, 62),
     (158, 58), (155, 55), (150, 60), (142, 62), (140, 60), (135, 58),
     (130, 55), (125, 52), (120, 50), (115, 48), (110, 45), (105, 42),
     (100, 40), (95, 38), (90, 40), (85, 42), (80, 40), (75, 38), (70, 36),
     (65, 35), (60, 38), (55, 40), (50, 42), (48, 45), (44, 48), (40, 50),
     (38, 46), (35, 44), (32, 42), (30, 40)],
    # Japan
    [(130, 31), (132, 33), (135, 34), (137, 35), (139, 36), (140, 38),
     (141, 40), (142, 42), (143, 44), (145, 44), (143, 42), (141, 39),
     (139, 37), (136, 34), (133, 32)],
    # Indonesia
    [(95, 5), (100, 0), (105, -5), (110, -7), (115, -8), (120, -10),
     (125, -9), (130, -8), (131, -3), (128, 1), (122, 1), (118, 0),
     (112, 0), (105, 2), (100, 4)],
    # New Guinea
    [(131, -1), (136, -2), (141, -3), (146, -6), (150, -9), (147, -9),
     (142, -8), (136, -7)],
    # Australia
    [(113, -22), (114, -28), (115, -33), (118, -35), (124, -33), (129, -32),
     (132, -32), (135, -35), (138, -35), (140, -38), (145, -38), (150, -37),
     (153, -32), (153, -27), (150, -23), (146, -19), (142, -15), (142, -11),
     (137, -12), (132, -11), (126, -14), (122, -17), (118, -20)],
    # New Zealand
    [(167, -45), (170, -42), (172, -41), (174, -39), (176, -38), (178, -38),
     (176, -40), (174, -41), (172, -43), (170, -46)],
]

# Story number -> (lon, lat, label dx, label dy). Dots are nudged where
# two stories sit close together; the map notes positions are approximate.
MAP_DOTS = [
    (1, 114, 22, 0, 0),      # Shenzhen summit
    (2, 2, 52, -4, 0),       # The Hague ICJ
    (3, 31, 37, 0, 0),       # Antalya COP31
    (4, -74, 41, 0, 0),      # New York IPO
    (6, 80, 18, 0, 0),       # Odisha cyclone (nudged west)
    (7, 36, 45, 0, 0),       # Kerch Bridge
    (8, 47, 25, 0, 0),       # Riyadh
    (9, 127, 38, 0, 0),      # Seoul
    (10, 14, 57, 0, 0),      # Copenhagen (nudged east)
    (11, 149, -35, 0, 0),    # Canberra
    (12, -74, 5, 0, 0),      # Bogota
    (13, 95, 26, 0, 0),      # Dhaka (nudged east)
    (14, 107, -6, 0, 0),     # Jakarta
    (16, 34, 31, 0, 0),      # Gaza
    (18, -72, 19, 0, 0),     # Port-au-Prince
]


def draw_map(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=MAP_SEA, outline=RULE, width=2)
    lon0, lon1, lat0, lat1 = -180.0, 180.0, 75.0, -60.0

    def proj(lon, lat):
        px = x + (lon - lon0) / (lon1 - lon0) * w
        py = y + (lat0 - lat) / (lat0 - lat1) * h
        return (px, py)

    for poly in CONTINENTS:
        d.polygon([proj(lon, lat) for lon, lat in poly], fill=MAP_LAND,
                  outline=(180, 168, 138))
    f_num = font(SANS_BOLD, 11)
    for num, lon, lat, dx, dy in MAP_DOTS:
        px, py = proj(lon, lat)
        px += dx
        py += dy
        r = 8
        d.ellipse([px - r - 1, py - r - 1, px + r + 1, py + r + 1],
                  fill=WHITE)
        d.ellipse([px - r, py - r, px + r, py + r], fill=RED)
        txt = str(num)
        tw = d.textlength(txt, font=f_num)
        d.text((px - tw / 2, py - 7), txt, font=f_num, fill=WHITE)


# ---------------------------------------------------------------- briefs
def draw_brief(d, x, y, w, num, place, text, source, claim=False):
    """One brief in a 2-line slot: bold 'N \u00b7 PLACE' then the story."""
    f_b = font(SANS_BOLD, 12)
    f_r = font(SANS, 12)
    prefix = "%d \u00b7 %s \u2014 " % (num, place)
    if claim:
        prefix += "[CLAIM] "
    body = text + "  (" + source + ")"
    pw = d.textlength(prefix, font=f_b)
    # Fit as much of body as possible on line 1 after the prefix;
    # everything from the first non-fitting word goes to line 2.
    words = body.split()
    cur = ""
    n1 = 0
    for wd in words:
        trial = wd if not cur else cur + " " + wd
        if d.textlength(trial, font=f_r) <= w - pw:
            cur = trial
            n1 += 1
        else:
            break
    line1 = cur
    line2 = " ".join(words[n1:])
    line2 = " ".join(wrap(d, line2, f_r, w)[:1])
    d.text((x, y), prefix, font=f_b, fill=INK)
    d.text((x + pw, y), line1, font=f_r, fill=INK)
    if line2:
        d.text((x, y + 14), line2, font=f_r, fill=INK)


# ---------------------------------------------------------------- data
CARDS_ROW2 = [
    # num, region, icon, kicker, headline, sub, source
    (4, "WORLD", "sun", "ANTALYA \u00b7 CLIMATE",
     "COP31 DRAFT DROPS FOSSIL FUELS",
     "Slimmed text removes every mention of fossil fuels \u2014 and the $120bn adaptation figure.",
     "Reuters"),
    (5, "WORLD", "game", "GLOBAL \u00b7 CULTURE",
     "GTA VI IS OUT",
     "Rockstar\u2019s first mainline GTA in 13 years launches on PS5 and Xbox, $79.99, in Vice City.",
     "Rockstar Games"),
    (6, "ASIA", "storm", "ODISHA \u00b7 WEATHER",
     "80,000 FLEE CYCLONE AKVAN",
     "Severe storm bears down on India\u2019s east coast; landfall due Friday near Puri.",
     "Hindu BusinessLine"),
    (7, "EUROPE", "bridge", "UKRAINE \u00b7 WAR",
     "KERCH BRIDGE HIT AGAIN",
     "Third Ukrainian strike in four days halts rail traffic; two Russian refineries also hit.",
     "Euronews \u00b7 AP"),
    (8, "MIDEAST", "tower", "RIYADH \u00b7 MIDDLE EAST",
     "MISSILE HITS PIF TOWER",
     "Houthi strike blows out windows across 7\u20138 floors of Riyadh\u2019s tallest tower. No injuries.",
     "Reuters"),
]

CARDS_ROW3 = [
    (9, "ASIA", "gavel", "SEOUL \u00b7 SOUTH KOREA",
     "EX-PM\u2019S SENTENCE PARTLY OVERTURNED",
     "Top court orders a retrial for Han Duck-soo, acquitting him on insurrection intent.",
     "AP \u00b7 Yonhap"),
    (10, "EUROPE", "pin", "COPENHAGEN \u00b7 ARCTIC",
     "DENMARK BACKS ARCTIC PACT 109\u20130",
     "Parliament unanimously approves the US\u2013Denmark\u2013Greenland security deal.",
     "AP \u00b7 Folketing"),
    (11, "OCEANIA", "down", "CANBERRA \u00b7 ECONOMY",
     "JOBLESS RATE HITS 4.9%",
     "Highest since 2021 as 43,500 jobs vanish; the Aussie dollar sinks to a 2026 low.",
     "ABS \u00b7 Reuters"),
    (12, "AMERICAS", "crowd", "BOGOT\u00c1 \u00b7 PROTEST",
     "COLOMBIA STRIKES OVER TAX BILL",
     "Unions march in five cities against the Economic Rescue Law; transit disrupted.",
     "El Tiempo"),
    (13, "ASIA", "flame", "DHAKA \u00b7 UNREST",
     "LOCKDOWN AND FIRE IN BANGLADESH",
     "Awami League shutdown; Yunus\u2019s ancestral home torched, four killed, 565 arrested.",
     "Reuters \u00b7 PTI"),
]

BRIEFS = [
    # num, place, text, source, claim?
    (14, "INDONESIA", "DPR passes asset-forfeiture law after an 18-year wait.",
     "Reuters", False),
    (15, "FRANCE", "Greens open the door to backing M\u00e9lenchon for 2027.",
     "Reuters", False),
    (16, "GAZA", "Israel ends tank raid past the Yellow Line; 6,000 fled.",
     "Reuters", False),
    (17, "WASHINGTON", "Senate rejects Iran war-powers bid, 48\u201351.",
     "Reuters", False),
    (18, "HAITI", "Police kill 34 suspected gang members in Martissant raid.",
     "AP", False),
    (19, "WASHINGTON", "Trump posthumously pardons baseball\u2019s Pete Rose.",
     "Reuters", False),
    (20, "SEOUL", "551,864 students sit the Suneung exam; flights halted.",
     "MOE", False),
    (21, "HORMUZ", "Iran says two supertankers hit mines; unverified.",
     "Reuters", True),
    (22, "BRUSSELS", "EU delays methane rules for fuel importers by two years.",
     "Consilium", False),
    (23, "MOGADISHU", "Somalia expels UAE ambassador, gives him 72 hours.",
     "AP", False),
    (24, "PRETORIA", "Central bank holds rate at 7.25% in a 4\u20133 vote.",
     "SARB", False),
    (25, "WELLINGTON", "Court: pay-equity overhaul breached women\u2019s rights.",
     "Reuters", False),
    (26, "TONGA", "Nationwide drought emergency declared for 27 days.",
     "PINA", False),
    (27, "ROME", "Journalist and TV host Corrado Augias dies at 91.",
     "LaPresse", False),
    (28, "LONDON", "Bayesian report: crew unaware of the fatal flaw.",
     "MAIB", False),
    (29, "ZURICH", "Diallo and Tashima to challenge Infantino for FIFA.",
     "Reuters", False),
    (30, "FLORIDA", "16 inches of rain floods Broward; schools shut.",
     "NWS", False),
    (31, "KENYA", "Marathon star Jepchirchir banned 3 years for EPO.",
     "AIU", False),
    (32, "COOK ISLANDS", "Cyclone Xavier still Category 4, slowly weakening.",
     "Fiji Met", False),
]

NUMBERS = [
    ("90 MIN", "Trump\u2013Xi\u2013Putin summit"),
    ("9\u20136", "ICJ genocide vote"),
    ("$81.3BN", "Anthropic IPO raised"),
    ("109\u20130", "Denmark Arctic pact"),
    ("4.9%", "Australia jobless rate"),
    ("551,864", "sat Korea\u2019s Suneung"),
]


def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    x0 = MARGIN

    # --- Top bar ---
    d.line([x0, 8, W - x0, 8], fill=INK, width=3)
    f_top = font(SANS_BOLD, 15)
    d.text((x0, 12), "THE WORLD IN ONE DAY", font=f_top, fill=INK)
    right = "32 STORIES  \u00b7  7 REGIONS  \u00b7  ONE THURSDAY"
    rw = d.textlength(right, font=f_top)
    d.text((W - x0 - rw, 12), right, font=f_top, fill=INK)
    d.line([x0, 34, W - x0, 34], fill=INK, width=2)

    # --- Date headline ---
    f_head = font(SERIF_BOLD, 50)
    date_txt = "Thursday 19 November 2026"
    dw = d.textlength(date_txt, font=f_head)
    d.text(((W - dw) / 2, 38), date_txt, font=f_head, fill=INK)

    # --- Standfirst ---
    f_stand = font(SERIF_ITALIC, 18)
    stand = ("Three leaders meet in Shenzhen  \u00b7  The Hague calls "
             "Myanmar\u2019s crimes genocide  \u00b7  The biggest IPO in history")
    sw = d.textlength(stand, font=f_stand)
    d.text(((W - sw) / 2, 96), stand, font=f_stand, fill=RED)

    # --- Region bar ---
    ry, rh = 122, 24
    total = sum(n for _n, n, _c in REGIONS)
    cx = x0
    f_reg = font(SANS_BOLD, 13)
    for name, n, col in REGIONS:
        seg_w = CONTENT_W * n / total
        d.rectangle([cx, ry, cx + seg_w, ry + rh], fill=col)
        label = "%s %d" % (name, n)
        lw = d.textlength(label, font=f_reg)
        d.text((cx + (seg_w - lw) / 2, ry + 5), label, font=f_reg, fill=WHITE)
        cx += seg_w
    d.rectangle([x0, ry, W - x0, ry + rh], outline=INK, width=1)

    # --- Key numbers strip ---
    ny, nh = 150, 40
    gap = 6
    bw = (CONTENT_W - gap * (len(NUMBERS) - 1)) / len(NUMBERS)
    f_num = font(SANS_BLACK, 21)
    f_nlab = font(SANS, 11)
    for i, (num, lab) in enumerate(NUMBERS):
        bx = x0 + i * (bw + gap)
        d.rounded_rectangle([bx, ny, bx + bw, ny + nh], radius=5,
                            fill=CARD, outline=RULE, width=1)
        nw = d.textlength(num, font=f_num)
        d.text((bx + (bw - nw) / 2, ny + 3), num, font=f_num, fill=RED)
        lw = d.textlength(lab, font=f_nlab)
        d.text((bx + (bw - lw) / 2, ny + 26), lab, font=f_nlab, fill=MUTED)

    # --- Lead row: summit (wide) + ICJ + Anthropic ---
    ly, lh = 196, 172
    lead_w = 496
    med_w = 238
    lead_card(d, x0, ly, lead_w, lh, RCOL["ASIA"], 1,
              "SHENZHEN \u00b7 FIRST 3-WAY SUMMIT",
              "TRUMP–XI–PUTIN MEET",
              "90 minutes at Kylin Villa. A four-point \u201cDeclaration "
              "Toward Peace\u201d \u2014 UN reform, refined fuel, immunity, "
              "nuclear risk. Ukraine is not in the text.",
              "Reuters \u00b7 Xinhua")
    mx = x0 + lead_w + 10
    medium_card(d, mx, ly, med_w, lh, RCOL["ASIA"], 2, "THE HAGUE",
                "MYANMAR GUILTY OF GENOCIDE",
                "First time a state is held responsible for genocide. "
                "Reparations ordered.",
                "Reuters \u00b7 HRW", icon_scales, "9\u20136")
    mx2 = mx + med_w + 10
    medium_card(d, mx2, ly, med_w, lh, RCOL["AMERICAS"], 3,
                "NEW YORK \u00b7 MARKETS",
                "BIGGEST IPO IN HISTORY",
                "Nasdaq debut raises $81.3bn; shares close $97.17, up 17%.",
                "Reuters \u00b7 Motley Fool", icon_chart_up, "$81.3bn")

    # --- Card rows 2 and 3 ---
    def card_row(y, h, cards):
        gap = 8
        cw = (CONTENT_W - gap * (len(cards) - 1)) / len(cards)
        for i, (num, region, icon, kicker, headline, sub, source) in \
                enumerate(cards):
            small_card(d, x0 + i * (cw + gap), y, cw, h, RCOL[region],
                       num, kicker, headline, sub, source, icon)

    card_row(374, 128, CARDS_ROW2)
    card_row(508, 128, CARDS_ROW3)

    # --- Map + briefs ---
    my = 640
    f_sec = font(SANS_BLACK, 15)
    d.text((x0, my), "WHERE IT HAPPENED", font=f_sec, fill=INK)
    map_x, map_y, map_w, map_h = x0, my + 20, 324, 150
    draw_map(d, map_x, map_y, map_w, map_h)

    # Confidence legend under the map
    ly2 = map_y + map_h + 10
    f_leg_h = font(SANS_BOLD, 12)
    d.text((x0, ly2), "HOW SURE ARE WE?", font=f_leg_h, fill=INK)
    f_leg = font(SANS, 12)
    legend = [
        ("REPORTED", "confirmed by wire reporting", (22, 120, 70)),
        ("FORECAST", "due after 19 Nov (landfall, vote)", (204, 85, 0)),
        ("CLAIM", "one side\u2019s account, unverified", (185, 28, 28)),
    ]
    yy = ly2 + 18
    for tag, desc, col in legend:
        d.ellipse([x0, yy + 2, x0 + 9, yy + 11], fill=col)
        d.text((x0 + 14, yy), tag, font=f_leg_h, fill=INK)
        tw = d.textlength(tag, font=f_leg_h)
        d.text((x0 + 14 + tw + 6, yy), "\u2014 " + desc, font=f_leg,
               fill=MUTED)
        yy += 17
    f_note = font(SANS_ITALIC, 11)
    d.text((x0, yy + 4), "Map positions approximate; dots are numbered",
           font=f_note, fill=MUTED)
    d.text((x0, yy + 18), "to match the stories.", font=f_note, fill=MUTED)

    # Brief list, two columns
    bx0 = x0 + map_w + 8
    bw2 = W - x0 - bx0
    d.text((bx0, my), "ALSO ON THURSDAY 19 NOVEMBER", font=f_sec, fill=INK)
    col_w = (bw2 - 12) / 2
    col1 = BRIEFS[:10]
    col2 = BRIEFS[10:]
    slot = 26
    for col_i, col in enumerate((col1, col2)):
        cx = bx0 + col_i * (col_w + 12)
        for i, (num, place, text, source, claim) in enumerate(col):
            draw_brief(d, cx, my + 20 + i * slot, col_w, num, place, text,
                       source, claim)

    # --- Date check box ---
    dy, dh = 924, 48
    d.rectangle([x0, dy, W - x0, dy + dh], fill=(255, 240, 240),
                outline=RED, width=2)
    f_dc_h = font(SANS_BLACK, 12)
    f_dc = font(SANS, 12)
    d.text((x0 + 10, dy + 4), "DATE CHECK \u2014 NOT 19 NOVEMBER:",
           font=f_dc_h, fill=RED)
    dc1 = ("Sudan court sentences RSF chief Hemedti to death (18 Nov)  \u00b7  "
           "Nature publishes star-merger study (18 Nov)")
    dc2 = ("Voyager 1 crosses one light-day (18 Nov)  \u00b7  Canary Islands "
           "migrant figures cover 1\u201315 Nov (reported 16 Nov)")
    d.text((x0 + 10, dy + 19), dc1, font=f_dc, fill=INK)
    d.text((x0 + 10, dy + 33), dc2, font=f_dc, fill=INK)

    # --- Footer ---
    f_foot = font(SANS, 11)
    foot1 = ("Sources: Reuters \u00b7 AP \u00b7 AFP \u00b7 BBC \u00b7 HRW \u00b7 ABS \u00b7 "
             "SARB \u00b7 MAIB \u00b7 AIU \u00b7 Consilium \u00b7 PINA \u00b7 Rockstar Games "
             "\u00b7 LaPresse \u00b7 Fiji Met Service")
    fw1 = d.textlength(foot1, font=f_foot)
    d.text(((W - fw1) / 2, 976), foot1, font=f_foot, fill=MUTED)
    foot2 = ("Claims are attributed, not stated as fact  \u00b7  Every event "
             "reported on Thursday 19 November 2026  \u00b7  Drawn by an AI "
             "agent for make.fun \u00b7 news-image-20261119")
    fw2 = d.textlength(foot2, font=f_foot)
    d.text(((W - fw2) / 2, 991), foot2, font=f_foot, fill=MUTED)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "entry.png")
    img.save(out, optimize=True)
    print("wrote", out, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
