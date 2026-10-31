#!/usr/bin/env python3
"""Generate a playful blue dolphin banner GIF for the Linux README."""
from __future__ import annotations

import math
import os
from PIL import Image, ImageDraw, ImageFilter

W, H = 1200, 360
SS = 2
FW, FH = W * SS, H * SS

BG_TOP = (228, 245, 255)
BG_BOTTOM = (250, 253, 255)
BODY_TOP = (24, 98, 206)
BODY_MID = (58, 150, 236)
BODY_BOTTOM = (176, 228, 255)
FIN_DARK = (18, 78, 172)
FIN_MID = (42, 124, 218)
OUTLINE = (12, 56, 126)

# Side profile, clockwise from the rostrum tip.
DOLPHIN_BASE = [
    (850, 199), (846, 195), (830, 192), (812, 191), (800, 190),
    (792, 182), (782, 170), (770, 158),
    (740, 146), (700, 138), (650, 133), (600, 132),
    (540, 136), (480, 146), (430, 160), (390, 176), (355, 186), (335, 190),
    (340, 198), (370, 208), (410, 220), (460, 232), (520, 242),
    (590, 248), (650, 248), (710, 240), (755, 226), (785, 214),
    (800, 208), (815, 207), (830, 205), (844, 203), (848, 201),
]
TAIL = (335, 190)


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return tuple(int(round(lerp(c1[i], c2[i], t))) for i in range(3))


def vertical_gradient(size, top, bottom):
    w, h = size
    img = Image.new("RGB", (1, h))
    px = img.load()
    for y in range(h):
        px[0, y] = mix(top, bottom, y / max(1, h - 1))
    return img.resize((w, h))


def smooth_closed(points, samples_per_segment=16):
    n = len(points)
    out = []
    for i in range(n):
        p0, p1, p2, p3 = points[(i - 1) % n], points[i], points[(i + 1) % n], points[(i + 2) % n]
        for s in range(samples_per_segment):
            u = s / samples_per_segment
            u2, u3 = u * u, u * u * u
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * u
                       + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * u2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * u3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * u
                       + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * u2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * u3)
            out.append((x, y))
    return out


def bend(px, py, phase, bob):
    u = min(1.0, max(0.0, (px - TAIL[0]) / (862 - TAIL[0])))
    py += bob - 10 * math.sin(math.pi * u)
    py += 13 * math.sin(2 * math.pi * (u * 0.9 - phase)) * (0.12 + 0.88 * (1 - u))
    return px, py


def draw_dolphin(draw, img, phase, bob):
    sp = lambda point: (point[0] * SS, point[1] * SS)
    base = [sp(bend(x, y, phase, bob)) for x, y in DOLPHIN_BASE]
    body = smooth_closed(base, 14)

    mask = Image.new("L", (FW, FH), 0)
    ImageDraw.Draw(mask).polygon(body, fill=255)
    img.paste(vertical_gradient((FW, FH), BODY_TOP, BODY_BOTTOM), (0, 0), mask)

    # Soft belly sheen, clipped to the body so no edge shows.
    sheen = Image.new("L", (FW, FH), 0)
    ImageDraw.Draw(sheen).ellipse([FW * 0.34, FH * 0.52, FW * 0.70, FH * 0.78], fill=190)
    sheen = sheen.filter(ImageFilter.GaussianBlur(26 * SS))
    from PIL import ImageChops
    sheen = ImageChops.multiply(sheen, mask)
    img.paste(Image.new("RGB", (FW, FH), (226, 247, 255)), (0, 0), sheen)

    draw.line(body + [body[0]], fill=OUTLINE, width=4, joint="curve")

    # Soft highlight along the back.
    highlight = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
    hd = ImageDraw.Draw(highlight)
    hd.line([sp(bend(590, 146, phase, bob)), sp(bend(650, 140, phase, bob)),
             sp(bend(710, 148, phase, bob)), sp(bend(755, 162, phase, bob))],
            fill=(190, 230, 255, 110), width=7 * SS, joint="curve")
    highlight = highlight.filter(ImageFilter.GaussianBlur(4 * SS))
    img.paste(highlight, (0, 0), highlight)

    # Dorsal fin: falcate, swept back.
    fin_base = [(662, 136), (612, 132), (566, 136)]
    fin_tip = (600, 64)
    fin = [sp(bend(660, 136, phase, bob)), sp(bend(638, 104, phase, bob)), sp(bend(606, 72, phase, bob)),
           sp(bend(588, 92, phase, bob)), sp(bend(570, 134, phase, bob))]
    draw.polygon(smooth_closed(fin), fill=FIN_DARK, outline=OUTLINE)

    # Pectoral fin.
    flap = 12 * math.sin(phase * 2 * math.pi + 0.8)
    pec = [sp(bend(758, 222, phase, bob)), sp(bend(742, 242, phase, bob)),
           sp(bend(712, 258 + flap, phase, bob)), sp(bend(706, 238, phase, bob)),
           sp(bend(730, 226, phase, bob))]
    draw.polygon(smooth_closed(pec), fill=FIN_MID, outline=OUTLINE)

    # Tail flukes rotate around the tail stock.
    tx, ty = sp(bend(*TAIL, phase, bob))
    angle = math.radians(30 * math.sin(phase * 2 * math.pi + 0.4))
    ca, sa = math.cos(angle), math.sin(angle)

    def rot(px, py):
        dx, dy = px - TAIL[0], py - TAIL[1]
        return (tx + (dx * ca - dy * sa) * SS, ty + (dx * sa + dy * ca) * SS)

    upper = [rot(340, 188), rot(300, 166), rot(252, 150), rot(266, 178), rot(322, 189)]
    lower = [rot(340, 192), rot(302, 216), rot(258, 230), rot(272, 204), rot(324, 192)]
    draw.polygon(smooth_closed(upper), fill=FIN_DARK, outline=OUTLINE)
    draw.polygon(smooth_closed(lower), fill=FIN_MID, outline=OUTLINE)

    # Eye just behind the beak base.
    ex, ey = sp(bend(786, 170, phase, bob))
    eye = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
    ed = ImageDraw.Draw(eye)
    ed.ellipse([ex - 15 * SS, ey - 20 * SS, ex + 15 * SS, ey + 10 * SS], fill=(255, 255, 255, 255), outline=OUTLINE, width=3)
    ed.ellipse([ex - 6 * SS, ey - 14 * SS, ex + 8 * SS, ey + 1 * SS], fill=(16, 44, 88, 255))
    ed.ellipse([ex + 1 * SS, ey - 12 * SS, ex + 7 * SS, ey - 6 * SS], fill=(255, 255, 255, 255))
    img.paste(eye, (0, 0), eye)

    # Mouth line along the lower jaw.
    mouth = [sp(bend(848, 201, phase, bob)), sp(bend(836, 203, phase, bob)),
             sp(bend(822, 204, phase, bob)), sp(bend(808, 203, phase, bob))]
    draw.line(mouth, fill=OUTLINE, width=3, joint="curve")

    # Blush
    bx, by = sp(bend(772, 194, phase, bob))
    blush = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
    ImageDraw.Draw(blush).ellipse([bx - 22 * SS, by - 4 * SS, bx + 8 * SS, by + 16 * SS], fill=(255, 140, 164, 80))
    img.paste(blush, (0, 0), blush)

    # Blowhole droplets above the melon.
    hx, hy = sp(bend(762, 156, phase, bob))
    lift = 10 * math.sin(phase * 2 * math.pi)
    for i, (dx, dy, r) in enumerate([(0, -30, 7), (-18, -54, 5), (12, -66, 4)]):
        cy = hy + dy * SS + lift * (0.5 + i * 0.2) * SS
        cx = hx + dx * SS + 5 * math.sin(phase * 2 * math.pi + i) * SS
        draw.ellipse([cx - r * SS, cy - r * SS, cx + r * SS, cy + r * SS], fill=(214, 244, 255),
                     outline=(118, 198, 244), width=2 * SS)


def draw_background(img, draw, phase):
    img.paste(vertical_gradient((FW, FH), BG_TOP, BG_BOTTOM), (0, 0))

    glow = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([FW * 0.24, FH * 0.02, FW * 0.88, FH * 1.1], fill=(150, 220, 255, 64))
    glow = glow.filter(ImageFilter.GaussianBlur(58 * SS))
    img.paste(glow, (0, 0), glow)

    shadow = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse([FW * 0.28, FH * 0.76, FW * 0.78, FH * 0.94], fill=(18, 86, 150, 46))
    shadow = shadow.filter(ImageFilter.GaussianBlur(20 * SS))
    img.paste(shadow, (0, 0), shadow)

    bands = [
        (0.74, (198, 235, 255), 0.55, 9),
        (0.82, (150, 214, 250), 0.75, 13),
        (0.90, (100, 188, 240), 0.95, 17),
    ]
    for idx, (base, color, amp, speed) in enumerate(bands):
        pts = []
        for x in range(0, FW + 20, 16):
            xx = x / SS
            y = FH * base + math.sin((xx / W) * math.pi * 4 + phase * 2 * math.pi * (1 + idx * 0.35)) * amp * SS * 0.35
            pts.append((x, y))
        pts += [(FW, FH), (0, FH)]
        draw.polygon(pts, fill=color)

    for i in range(9):
        seed = i * 1.7
        bx = (140 + i * 118 + 26 * math.sin(seed)) % W
        speed = 0.16 + (i % 3) * 0.05
        by = H - ((phase * speed * 2.4 + i * 0.13) % 1.0) * (H * 0.78)
        r = 4 + (i % 4) * 2.5
        wob = 10 * math.sin(phase * 2 * math.pi + seed)
        x, y = (bx + wob) * SS, by * SS
        draw.ellipse([x - r * SS, y - r * SS, x + r * SS, y + r * SS],
                     outline=(255, 255, 255), width=3 * SS)
        draw.ellipse([x - r * SS * 0.35, y - r * SS * 0.55, x, y - r * SS * 0.15],
                     fill=(255, 255, 255))

    for i in range(7):
        seed = i * 2.3
        tx = (90 + i * 165 + 30 * math.sin(seed)) % W
        ty = 40 + (i * 47) % 160
        tw = max(0.0, math.sin(phase * 2 * math.pi * 2 + seed))
        if tw <= 0.05:
            continue
        r = (4 + 8 * tw) * SS
        x, y = tx * SS, ty * SS
        draw.line([x - r, y, x + r, y], fill=(255, 255, 255), width=2 * SS)
        draw.line([x, y - r, x, y + r], fill=(255, 255, 255), width=2 * SS)
        draw.ellipse([x - r * 0.28, y - r * 0.28, x + r * 0.28, y + r * 0.28], fill=(255, 255, 255))


def draw_ball(draw, img, phase):
    bob = 9 * math.sin(phase * 2 * math.pi + 1.2)
    cx, cy, r = 972 * SS, (218 + bob) * SS, 30 * SS
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255), outline=OUTLINE, width=4 * SS)
    colors = [(255, 118, 102), (64, 196, 198), (255, 205, 96)]
    for i, color in enumerate(colors):
        start = 200 + i * 120
        draw.pieslice([cx - r, cy - r, cx + r, cy + r], start, start + 78, fill=color)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=OUTLINE, width=4 * SS)
    draw.ellipse([cx - r * 0.48, cy - r * 0.62, cx - r * 0.05, cy - r * 0.20],
                 fill=(255, 255, 255, 255))
    # Ripple
    ry = cy + r + 12 * SS
    draw.arc([cx - r * 1.2, ry - 8 * SS, cx + r * 1.2, ry + 8 * SS], 200, 340,
             fill=(160, 220, 250), width=3 * SS)


def render_frame(index, frames):
    phase = index / frames
    bob = 7 * math.sin(phase * 2 * math.pi)
    img = Image.new("RGB", (FW, FH), BG_TOP)
    draw = ImageDraw.Draw(img)
    draw_background(img, draw, phase)
    draw_dolphin(draw, img, phase, bob)
    draw_ball(draw, img, phase)
    return img.resize((W, H), Image.LANCZOS)


def main():
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "docs", "assets")
    os.makedirs(out, exist_ok=True)
    frames = 60
    images = [render_frame(i, frames) for i in range(frames)]
    images[0].save(os.path.join(out, "dolphin-banner.gif"), save_all=True,
                   append_images=images[1:], duration=50, loop=0, optimize=True,
                   disposal=2)
    images[0].save(os.path.join(out, "dolphin-banner.png"))
    print("wrote", out)


if __name__ == "__main__":
    main()
