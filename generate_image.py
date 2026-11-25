#!/usr/bin/env python3
"""Generate the 1024x1024 newspaper front-page entry.png for news-image-20261125."""

import math
import os
from PIL import Image, ImageDraw, ImageFont

CANVAS_SIZE = 1024
MAX_BYTES = 1048576

BG_COLOR = "#F7F3E8"
INK_COLOR = "#111111"
RED_COLOR = "#A31621"

FONT_BOLD_PATH = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_REG_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf"

MASTHEAD_TITLE = "THE WORLD IN ONE PICTURE"
MASTHEAD_DATE = "WEDNESDAY \u00b7 25 NOVEMBER 2026"

PANELS = [
    {
        "tag": "TECH",
        "headline": "NVIDIA SLIDES 7% AFTER HUANG'S 31% COMEBACK",
        "subline": "Lawmakers demand answers; Schumer alleges export violations",
        "motif": "chip_arrow",
    },
    {
        "tag": "WAR",
        "headline": "ZELENSKYY CONFIRMS UKRAINE SANK RUSSIAN SHIP",
        "subline": "Two vessels struck off Libya; Putin warns retaliation 'inevitable'",
        "motif": "sinking_ship",
    },
    {
        "tag": "MIDDLE EAST",
        "headline": "HOUTHIS HIT RIYADH'S TALLEST TOWER",
        "subline": "11 wounded in drone attack, Saudi civil defense says",
        "motif": "tower_drone",
    },
    {
        "tag": "AMERICA",
        "headline": "TRUMP AWARDS GIULIANI MEDAL OF FREEDOM",
        "subline": "Ex-mayor honoured at White House ceremony",
        "motif": "medal_ribbon",
    },
]

FOOTER_TEXT = (
    "ALSO TODAY \u2014 CIA AND ODNI SUFFER CYBER BREACH \u00b7 "
    "HUAWEI GUILTY OF TRADE-SECRET THEFT \u00b7 "
    "NATO EYES EARLY-WARNING JETS FOR POLAND"
)


def measure_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int, int, int]:
    """Return (width, height, left_offset, top_offset) for text measured with textbbox."""
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top, left, top


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    """Word-wrap text using draw.textbbox so every line fits within max_width."""
    words = text.split()
    if not words:
        return []

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        w, _, _, _ = measure_text(draw, candidate, font)
        if w <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)

    for line in lines:
        w, _, _, _ = measure_text(draw, line, font)
        if w > max_width:
            raise ValueError(f"Line overflows max_width ({w} > {max_width}): {line!r}")
    return lines


def draw_aligned_text(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str,
    ref_top_offset: int | None = None,
) -> tuple[int, int, int, int]:
    """Draw text with visual left at x and visual top aligned to y (or ref_top_offset)."""
    w, h, left_off, top_off = measure_text(draw, text, font)
    use_top = top_off if ref_top_offset is None else ref_top_offset
    draw.text((x - left_off, y - use_top), text, font=font, fill=fill)
    actual_top = y + (top_off - use_top)
    return (x, actual_top, x + w, actual_top + h)


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    center_x: int,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str,
    ref_top_offset: int | None = None,
) -> tuple[int, int, int, int]:
    """Draw text centered horizontally at center_x with visual top at y."""
    w, _, _, _ = measure_text(draw, text, font)
    x = round(center_x - w / 2)
    return draw_aligned_text(draw, x, y, text, font, fill, ref_top_offset=ref_top_offset)


def render_supersampled_motif(
    target_img: Image.Image,
    box: tuple[int, int, int, int],
    draw_fn,
    scale: int = 4,
) -> None:
    """Render a motif at high resolution for crisp anti-aliased Pillow shapes."""
    x0, y0, x1, y1 = box
    w = x1 - x0
    h = y1 - y0
    assert w > 0 and h > 0, f"Invalid motif box: {box}"

    hi = Image.new("RGBA", (w * scale, h * scale), (0, 0, 0, 0))
    d = ImageDraw.Draw(hi)
    draw_fn(d, w * scale, h * scale, scale)
    lo = hi.resize((w, h), Image.Resampling.LANCZOS)
    target_img.paste(lo, (x0, y0), lo)


def draw_motif_chip_arrow(d: ImageDraw.ImageDraw, w: int, h: int, s: int) -> None:
    """Computer chip (filled square with pin lines on all four sides) + bold downward arrow."""
    cy = int(h * 0.53)
    chip_size = int(min(h * 0.58, w * 0.22))
    pin_len = int(chip_size * 0.22)
    pin_w = max(2 * s, int(chip_size * 0.075))

    # Position chip left-of-center and downward arrow right-of-center
    gap = int(w * 0.11)
    arrow_w = int(chip_size * 0.85)
    total_w = (chip_size + 2 * pin_len) + gap + arrow_w
    start_x = (w - total_w) // 2

    chip_x0 = start_x + pin_len
    chip_y0 = cy - chip_size // 2
    chip_x1 = chip_x0 + chip_size
    chip_y1 = chip_y0 + chip_size

    # Pin lines on all four sides (5 pins per side)
    num_pins = 5
    margin = int(chip_size * 0.16)
    span = chip_size - 2 * margin
    for i in range(num_pins):
        offset = margin + int(round(i * span / (num_pins - 1)))
        # Top pins
        px = chip_x0 + offset
        d.line([(px, chip_y0 - pin_len), (px, chip_y0)], fill=INK_COLOR, width=pin_w)
        # Bottom pins
        d.line([(px, chip_y1), (px, chip_y1 + pin_len)], fill=INK_COLOR, width=pin_w)
        # Left pins
        py = chip_y0 + offset
        d.line([(chip_x0 - pin_len, py), (chip_x0, py)], fill=INK_COLOR, width=pin_w)
        # Right pins
        d.line([(chip_x1, py), (chip_x1 + pin_len, py)], fill=INK_COLOR, width=pin_w)

    # Filled chip square + subtle inner silicon die framing
    d.rectangle([chip_x0, chip_y0, chip_x1, chip_y1], fill=INK_COLOR)
    inner_pad = int(chip_size * 0.18)
    d.rectangle(
        [chip_x0 + inner_pad, chip_y0 + inner_pad, chip_x1 - inner_pad, chip_y1 - inner_pad],
        outline=BG_COLOR,
        width=max(2 * s, int(chip_size * 0.055)),
    )
    core_pad = int(chip_size * 0.36)
    d.rectangle(
        [chip_x0 + core_pad, chip_y0 + core_pad, chip_x1 - core_pad, chip_y1 - core_pad],
        fill=BG_COLOR,
    )

    # Bold deep-red downward arrow beside the chip
    arrow_cx = chip_x1 + pin_len + gap + arrow_w // 2
    arrow_top = chip_y0 - int(pin_len * 0.45)
    arrow_bot = chip_y1 + int(pin_len * 0.45)
    arrow_h = arrow_bot - arrow_top
    shaft_half_w = int(arrow_w * 0.21)
    head_half_w = int(arrow_w * 0.50)
    head_y = arrow_top + int(arrow_h * 0.52)

    arrow_poly = [
        (arrow_cx - shaft_half_w, arrow_top),
        (arrow_cx + shaft_half_w, arrow_top),
        (arrow_cx + shaft_half_w, head_y),
        (arrow_cx + head_half_w, head_y),
        (arrow_cx, arrow_bot),
        (arrow_cx - head_half_w, head_y),
        (arrow_cx - shaft_half_w, head_y),
    ]
    d.polygon(arrow_poly, fill=RED_COLOR)


def draw_motif_sinking_ship(d: ImageDraw.ImageDraw, w: int, h: int, s: int) -> None:
    """Tilted dark warship hull half-submerged in wavy water + small drone boat with antenna."""
    water_y1 = int(h * 0.68)
    water_y2 = int(h * 0.81)
    water_y3 = int(h * 0.92)
    amp = int(h * 0.042)
    wave_period = w / 4.2

    def wave_y(base_y: int, x: float, phase: float = 0.0) -> float:
        return base_y + amp * math.sin((2 * math.pi * x / wave_period) + phase)

    # Tilted warship silhouette (bow plunging right-downward into the waves, fully inside box)
    pivot_x = int(w * 0.36)
    pivot_y = int(h * 0.65)
    angle = math.radians(22)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    def rot(lx: float, ly: float) -> tuple[float, float]:
        return (
            pivot_x + lx * cos_a - ly * sin_a,
            pivot_y + lx * sin_a + ly * cos_a,
        )

    unit = h * 0.0081
    # Main warship hull (stern elevated left, bow submerged right)
    hull_pts = [
        rot(-118 * unit, -12 * unit),
        rot(122 * unit, -12 * unit),
        rot(92 * unit, 28 * unit),
        rot(-96 * unit, 28 * unit),
    ]
    d.polygon(hull_pts, fill=INK_COLOR)

    # Superstructure / bridge
    bridge_pts = [
        rot(-42 * unit, -12 * unit),
        rot(26 * unit, -12 * unit),
        rot(18 * unit, -38 * unit),
        rot(-34 * unit, -38 * unit),
    ]
    d.polygon(bridge_pts, fill=INK_COLOR)

    # Upper funnel / mast block
    upper_pts = [
        rot(-20 * unit, -38 * unit),
        rot(8 * unit, -38 * unit),
        rot(4 * unit, -52 * unit),
        rot(-16 * unit, -52 * unit),
    ]
    d.polygon(upper_pts, fill=INK_COLOR)

    # Mast pole & radar crossbar
    d.line(
        [rot(-6 * unit, -52 * unit), rot(-6 * unit, -74 * unit)],
        fill=INK_COLOR,
        width=max(2 * s, int(3.8 * unit)),
    )
    d.line(
        [rot(-18 * unit, -64 * unit), rot(6 * unit, -64 * unit)],
        fill=INK_COLOR,
        width=max(2 * s, int(2.8 * unit)),
    )

    # Stern turret silhouette
    turret_pts = [
        rot(-84 * unit, -12 * unit),
        rot(-58 * unit, -12 * unit),
        rot(-62 * unit, -22 * unit),
        rot(-80 * unit, -22 * unit),
    ]
    d.polygon(turret_pts, fill=INK_COLOR)

    # Mask below top wavy waterline with BG_COLOR so hull is genuinely half-submerged
    wave_left = int(w * 0.05)
    wave_right = int(w * 0.95)
    step = max(2, s * 2)
    top_wave = [(x, wave_y(water_y1, x, 0.0)) for x in range(wave_left, wave_right + 1, step)]
    mask_poly = [(wave_left, h)] + top_wave + [(wave_right, h)]
    d.polygon(mask_poly, fill=BG_COLOR)

    # Small unmanned drone boat sitting flat on the water to the right
    drone_cx = int(w * 0.79)
    drone_w = int(w * 0.145)
    drone_h = int(h * 0.115)
    drone_base_y = int(wave_y(water_y1, drone_cx, 0.0)) + int(h * 0.01)
    dx0 = drone_cx - drone_w // 2
    dx1 = drone_cx + drone_w // 2
    dy0 = drone_base_y - drone_h
    d.polygon(
        [
            (dx0 + int(drone_w * 0.10), dy0),
            (dx1 - int(drone_w * 0.04), dy0),
            (dx1, drone_base_y),
            (dx0, drone_base_y),
        ],
        fill=INK_COLOR,
    )
    # Antenna mast + red beacon tip + crisp radio control signal arcs
    ant_x = drone_cx + int(drone_w * 0.18)
    ant_top = dy0 - int(h * 0.22)
    d.line([(ant_x, dy0), (ant_x, ant_top)], fill=INK_COLOR, width=max(2 * s, int(2.6 * s)))
    dot_r = int(4.2 * s)
    d.ellipse([ant_x - dot_r, ant_top - dot_r, ant_x + dot_r, ant_top + dot_r], fill=RED_COLOR)
    arc_w = max(2 * s, int(2.2 * s))
    for arc_r in (int(11 * s), int(18 * s)):
        d.arc(
            [ant_x - arc_r, ant_top - arc_r, ant_x + arc_r, ant_top + arc_r],
            start=150,
            end=215,
            fill=RED_COLOR,
            width=arc_w,
        )

    # Draw crisp wavy water lines over the waterline
    line_w = max(2 * s, int(3.0 * s))
    for base_y, phase in [(water_y1, 0.0), (water_y2, 1.3), (water_y3, 2.6)]:
        pts = [(x, wave_y(base_y, x, phase)) for x in range(wave_left, wave_right + 1, step)]
        d.line(pts, fill=INK_COLOR, width=line_w, joint="curve")


def draw_motif_tower_drone(d: ImageDraw.ImageDraw, w: int, h: int, s: int) -> None:
    """Tall narrow vertical tower with small windows + small drone with two rotor lines above it."""
    cx = w // 2
    ground_y = int(h * 0.94)

    # Focused architectural ground baseline
    d.line(
        [(int(w * 0.26), ground_y), (int(w * 0.74), ground_y)],
        fill=INK_COLOR,
        width=max(2 * s, int(3.0 * s)),
    )

    # Tall narrow vertical rectangle tower
    tower_w = int(w * 0.090)
    tower_h = int(h * 0.66)
    tx0 = cx - tower_w // 2
    tx1 = cx + tower_w // 2
    ty0 = ground_y - tower_h
    ty1 = ground_y

    d.rectangle([tx0, ty0, tx1, ty1], fill=INK_COLOR)

    # Small neatly arranged windows on the tower facade
    cols = 3
    rows = 8
    pad_x = int(tower_w * 0.16)
    pad_y_top = int(tower_h * 0.085)
    pad_y_bot = int(tower_h * 0.085)
    col_gap = int(tower_w * 0.10)
    win_w = (tower_w - 2 * pad_x - (cols - 1) * col_gap) // cols
    row_gap = int(tower_h * 0.042)
    win_h = (tower_h - pad_y_top - pad_y_bot - (rows - 1) * row_gap) // rows

    for r in range(rows):
        wy0 = ty0 + pad_y_top + r * (win_h + row_gap)
        for c in range(cols):
            wx0 = tx0 + pad_x + c * (win_w + col_gap)
            d.rectangle([wx0, wy0, wx0 + win_w, wy0 + win_h], fill=BG_COLOR)

    # Small drone hovering cleanly above the tower (tiny rectangle + two rotor lines)
    drone_cx = cx + int(w * 0.03)
    drone_cy = int(ty0 * 0.61)
    body_w = int(w * 0.092)
    body_h = int(h * 0.072)
    bx0 = drone_cx - body_w // 2
    bx1 = drone_cx + body_w // 2
    by0 = drone_cy - body_h // 2
    by1 = drone_cy + body_h // 2

    # Tiny rectangular drone body in deep red
    d.rectangle([bx0, by0, bx1, by1], fill=RED_COLOR)

    # Two rotor arms + two horizontal rotor lines above the drone
    arm_w = max(2 * s, int(2.6 * s))
    rotor_y = by0 - int(h * 0.068)
    rotor_half = int(body_w * 0.42)
    left_rx = bx0 - int(body_w * 0.16)
    right_rx = bx1 + int(body_w * 0.16)

    d.line([(bx0 + int(body_w * 0.15), by0), (left_rx, rotor_y)], fill=RED_COLOR, width=arm_w)
    d.line([(bx1 - int(body_w * 0.15), by0), (right_rx, rotor_y)], fill=RED_COLOR, width=arm_w)

    rotor_w = max(2 * s, int(3.0 * s))
    d.line([(left_rx - rotor_half, rotor_y), (left_rx + rotor_half, rotor_y)], fill=INK_COLOR, width=rotor_w)
    d.line([(right_rx - rotor_half, rotor_y), (right_rx + rotor_half, rotor_y)], fill=INK_COLOR, width=rotor_w)

    # Symmetric radial impact sparks near upper-right edge of tower
    impact_x = tx1 + int(w * 0.014)
    impact_y = ty0 + int(tower_h * 0.08)
    spark_w = max(2 * s, int(2.8 * s))
    for deg, r0, r1 in [(-42, 4 * s, 13 * s), (0, 5 * s, 16 * s), (42, 4 * s, 13 * s)]:
        ang = math.radians(deg)
        sx0 = impact_x + int(r0 * math.cos(ang))
        sy0 = impact_y + int(r0 * math.sin(ang))
        sx1 = impact_x + int(r1 * math.cos(ang))
        sy1 = impact_y + int(r1 * math.sin(ang))
        d.line([(sx0, sy0), (sx1, sy1)], fill=RED_COLOR, width=spark_w)


def draw_motif_medal_ribbon(d: ImageDraw.ImageDraw, w: int, h: int, s: int) -> None:
    """Medal (filled circle with star inside) hanging from a ribbon (two angled strips)."""
    cx = w // 2
    medal_r = int(h * 0.30)
    medal_cy = h - medal_r - int(h * 0.05)

    # Ribbon attachment point just above top of medal
    clasp_y = medal_cy - medal_r - int(h * 0.03)
    ribbon_top_y = int(h * 0.07)
    strip_w = int(medal_r * 0.56)
    spread_top = int(medal_r * 1.18)
    spread_bot = int(medal_r * 0.14)

    # Left angled strip
    left_strip = [
        (cx - spread_top - strip_w // 2, ribbon_top_y),
        (cx - spread_top + strip_w // 2, ribbon_top_y),
        (cx - spread_bot + strip_w // 2, clasp_y),
        (cx - spread_bot - strip_w // 2, clasp_y),
    ]
    # Right angled strip
    right_strip = [
        (cx + spread_top - strip_w // 2, ribbon_top_y),
        (cx + spread_top + strip_w // 2, ribbon_top_y),
        (cx + spread_bot + strip_w // 2, clasp_y),
        (cx + spread_bot - strip_w // 2, clasp_y),
    ]
    d.polygon(left_strip, fill=RED_COLOR)
    d.polygon(right_strip, fill=RED_COLOR)

    # Crisp thin cream center stripe on each ribbon strip for ceremonial texture
    stripe_w = max(2 * s, int(strip_w * 0.16))
    d.line([(cx - spread_top, ribbon_top_y), (cx - spread_bot, clasp_y)], fill=BG_COLOR, width=stripe_w)
    d.line([(cx + spread_top, ribbon_top_y), (cx + spread_bot, clasp_y)], fill=BG_COLOR, width=stripe_w)

    # Small horizontal clasp bar joining ribbon and medal
    clasp_half_w = int(medal_r * 0.36)
    clasp_h = int(h * 0.055)
    d.rectangle(
        [cx - clasp_half_w, clasp_y - clasp_h // 2, cx + clasp_half_w, clasp_y + clasp_h // 2],
        fill=INK_COLOR,
    )

    # Medal filled circle
    d.ellipse(
        [cx - medal_r, medal_cy - medal_r, cx + medal_r, medal_cy + medal_r],
        fill=INK_COLOR,
    )
    # Subtle inner ring
    ring_r = int(medal_r * 0.84)
    d.ellipse(
        [cx - ring_r, medal_cy - ring_r, cx + ring_r, medal_cy + ring_r],
        outline=BG_COLOR,
        width=max(2 * s, int(2.2 * s)),
    )

    # 5-pointed star centered inside the medal circle
    outer_r = medal_r * 0.66
    inner_r = outer_r * 0.40
    star_pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * (math.pi / 5)
        rad = outer_r if i % 2 == 0 else inner_r
        star_pts.append((cx + rad * math.cos(ang), medal_cy + rad * math.sin(ang)))
    d.polygon(star_pts, fill=BG_COLOR)


MOTIF_DISPATCH = {
    "chip_arrow": draw_motif_chip_arrow,
    "sinking_ship": draw_motif_sinking_ship,
    "tower_drone": draw_motif_tower_drone,
    "medal_ribbon": draw_motif_medal_ribbon,
}


def build_image() -> Image.Image:
    img = Image.new("RGB", (CANVAS_SIZE, CANVAS_SIZE), BG_COLOR)
    draw = ImageDraw.Draw(img)

    font_masthead = ImageFont.truetype(FONT_BOLD_PATH, 64)
    font_date = ImageFont.truetype(FONT_BOLD_PATH, 30)
    font_tag = ImageFont.truetype(FONT_BOLD_PATH, 17)
    font_headline = ImageFont.truetype(FONT_BOLD_PATH, 44)
    font_subline = ImageFont.truetype(FONT_REG_PATH, 24)
    font_footer = ImageFont.truetype(FONT_REG_PATH, 23)

    outer_x = 18
    content_w = CANVAS_SIZE - 2 * outer_x
    center_x = CANVAS_SIZE // 2

    # --- Masthead ---
    title_bbox = draw_centered_text(draw, center_x, 20, MASTHEAD_TITLE, font_masthead, INK_COLOR)
    assert title_bbox[0] >= outer_x and title_bbox[2] <= CANVAS_SIZE - outer_x

    red_rule_y = title_bbox[3] + 10
    draw.rectangle([outer_x, red_rule_y, CANVAS_SIZE - outer_x, red_rule_y + 4], fill=RED_COLOR)

    date_bbox = draw_centered_text(draw, center_x, red_rule_y + 14, MASTHEAD_DATE, font_date, INK_COLOR)
    assert date_bbox[0] >= outer_x and date_bbox[2] <= CANVAS_SIZE - outer_x

    # --- 2x2 Panel Grid ---
    grid_top = date_bbox[3] + 13
    footer_rule_y = 934
    grid_bottom = footer_rule_y - 12

    gap_x = 14
    gap_y = 14
    panel_w = (content_w - gap_x) // 2
    panel_h = (grid_bottom - grid_top - gap_y) // 2

    pad_x = 16
    pad_top = 13
    pad_bottom = 12
    text_max_w = panel_w - 2 * pad_x

    # Reference typographic baselines so all four panels align consistently across columns
    _, hl_ref_h, _, hl_ref_top = measure_text(draw, "H", font_headline)
    _, sub_ref_h, _, sub_ref_top = measure_text(draw, "Hpg", font_subline)
    _, ft_ref_h, _, ft_ref_top = measure_text(draw, "H", font_footer)

    for idx, panel in enumerate(PANELS):
        row = idx // 2
        col = idx % 2
        px0 = outer_x + col * (panel_w + gap_x)
        py0 = grid_top + row * (panel_h + gap_y)
        px1 = px0 + panel_w
        py1 = py0 + panel_h

        # Thin black border
        draw.rectangle([px0, py0, px1 - 1, py1 - 1], outline=INK_COLOR, width=2)

        inner_left = px0 + pad_x
        inner_right = px1 - pad_x
        cursor_y = py0 + pad_top

        # Small deep-red category tag at top-left
        tag_w, tag_h, _, _ = measure_text(draw, panel["tag"], font_tag)
        tag_pad_x = 9
        tag_pad_y = 5
        tag_box = (
            inner_left,
            cursor_y,
            inner_left + tag_w + 2 * tag_pad_x,
            cursor_y + tag_h + 2 * tag_pad_y,
        )
        draw.rectangle(tag_box, fill=RED_COLOR)
        draw_aligned_text(
            draw,
            inner_left + tag_pad_x,
            cursor_y + tag_pad_y,
            panel["tag"],
            font_tag,
            BG_COLOR,
        )
        cursor_y = tag_box[3] + 11

        # BIG bold headline (>= 44px), word-wrapped with draw.textbbox
        headline_lines = wrap_text(draw, panel["headline"], font_headline, text_max_w)
        headline_pitch = 46
        for i, line in enumerate(headline_lines):
            bb = draw_aligned_text(
                draw,
                inner_left,
                cursor_y + i * headline_pitch,
                line,
                font_headline,
                INK_COLOR,
                ref_top_offset=hl_ref_top,
            )
            assert bb[0] >= inner_left and bb[2] <= inner_right, f"Headline overflow: {bb}"
        cursor_y = cursor_y + (len(headline_lines) - 1) * headline_pitch + hl_ref_h + 12

        # Sub-line (24px), word-wrapped with draw.textbbox
        sub_lines = wrap_text(draw, panel["subline"], font_subline, text_max_w)
        sub_pitch = 29
        for i, line in enumerate(sub_lines):
            bb = draw_aligned_text(
                draw,
                inner_left,
                cursor_y + i * sub_pitch,
                line,
                font_subline,
                INK_COLOR,
                ref_top_offset=sub_ref_top,
            )
            assert bb[0] >= inner_left and bb[2] <= inner_right, f"Subline overflow: {bb}"
        cursor_y = cursor_y + (len(sub_lines) - 1) * sub_pitch + sub_ref_h + 10

        # Remaining space for simple flat motif
        motif_box = (inner_left, cursor_y, inner_right, py1 - pad_bottom)
        assert motif_box[3] - motif_box[1] >= 90, f"Insufficient motif space in panel {idx + 1}: {motif_box}"
        render_supersampled_motif(img, motif_box, MOTIF_DISPATCH[panel["motif"]])

    # --- Footer Strip ---
    draw.rectangle([outer_x, footer_rule_y, CANVAS_SIZE - outer_x, footer_rule_y + 3], fill=INK_COLOR)

    footer_lines = wrap_text(draw, FOOTER_TEXT, font_footer, content_w)
    footer_pitch = 29
    footer_block_h = (len(footer_lines) - 1) * footer_pitch + ft_ref_h
    footer_avail_top = footer_rule_y + 3
    footer_avail_bot = CANVAS_SIZE - 14
    footer_start_y = footer_avail_top + (footer_avail_bot - footer_avail_top - footer_block_h) // 2

    for i, line in enumerate(footer_lines):
        bb = draw_centered_text(
            draw,
            center_x,
            footer_start_y + i * footer_pitch,
            line,
            font_footer,
            INK_COLOR,
            ref_top_offset=ft_ref_top,
        )
        assert bb[0] >= outer_x and bb[2] <= CANVAS_SIZE - outer_x, f"Footer overflow: {bb}"
        assert bb[3] <= CANVAS_SIZE - 8, f"Footer vertical overflow: {bb}"

    assert img.size == (CANVAS_SIZE, CANVAS_SIZE), f"Unexpected size: {img.size}"
    return img


def main() -> None:
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(repo_dir, "entry.png")
    img = build_image()
    assert img.size == (CANVAS_SIZE, CANVAS_SIZE), f"Image size mismatch: {img.size}"
    img.save(out_path, format="PNG", optimize=True)

    # Post-save verification
    byte_size = os.path.getsize(out_path)
    with Image.open(out_path) as check:
        dims = check.size
    assert dims == (CANVAS_SIZE, CANVAS_SIZE), f"Saved dimensions mismatch: {dims}"
    assert byte_size <= MAX_BYTES, f"File too large: {byte_size} > {MAX_BYTES}"
    print(f"Saved {out_path}")
    print(f"Dimensions: {dims[0]}x{dims[1]}")
    print(f"Byte size: {byte_size} bytes (limit: {MAX_BYTES} bytes, OK)")


if __name__ == "__main__":
    main()
