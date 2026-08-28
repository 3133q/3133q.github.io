# -*- coding: utf-8 -*-
"""生成 10 张 CTF 风格封面图到 assets/covers/（深色终端风，不同色调）"""
import math
import random
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

random.seed(3133)
OUT = "assets/covers"
os.makedirs(OUT, exist_ok=True)

W, H = 1200, 500

# 10 种色调：(底色1, 底色2, 强调色)
PALETTES = [
    ((10, 25, 30),   (14, 48, 44),   (74, 222, 178)),   # 翠绿
    ((16, 20, 40),   (32, 40, 78),   (96, 165, 250)),   # 蓝
    ((24, 16, 40),   (48, 28, 72),   (192, 132, 252)),  # 紫
    ((30, 20, 14),   (56, 34, 16),   (251, 191, 36)),   # 琥珀
    ((30, 14, 18),   (58, 22, 30),   (248, 113, 113)),  # 红
    ((12, 28, 34),   (16, 50, 60),   (34, 211, 238)),   # 青
    ((20, 26, 16),   (34, 48, 24),   (163, 230, 53)),   # 青柠
    ((26, 18, 32),   (50, 30, 52),   (244, 114, 182)),  # 粉
    ((14, 22, 38),   (22, 40, 64),   (129, 140, 248)),  # 靛蓝
    ((20, 20, 22),   (36, 38, 42),   (156, 163, 175)),  # 灰白
]

HEX_CHARS = "0123456789abcdef"


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient(c1, c2):
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        for x in range(0, W, 2):  # 步进 2 加速，肉眼无差
            t = (x / W + y / H) / 2
            c = lerp(c1, c2, t)
            px[x, y] = c
            if x + 1 < W:
                px[x + 1, y] = c
    return img


def add_hexdump(img, accent):
    """左侧画几行十六进制转储，终端味"""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 20)
    except Exception:
        font = ImageFont.load_default()
    for row in range(random.randint(4, 7)):
        y = 40 + row * 34
        if y > H - 40:
            break
        addr = f"0x{random.randint(0, 0xffffff):06x}:"
        hexs = " ".join("".join(random.choice(HEX_CHARS) for _ in range(2)) for _ in range(8))
        d.text((36, y), f"{addr}  {hexs}", font=font, fill=(*accent, 46))
    base = img.convert("RGBA")
    base.alpha_composite(overlay)
    return base.convert("RGB")


def add_circuits(img, accent, n=22):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for _ in range(n):
        x, y = random.randint(0, W), random.randint(0, H)
        pts = [(x, y)]
        for _ in range(random.randint(2, 4)):
            if random.random() < 0.5:
                x += random.choice([-1, 1]) * random.randint(30, 150)
            else:
                y += random.choice([-1, 1]) * random.randint(25, 90)
            pts.append((x, y))
        d.line(pts, fill=(*accent, 55), width=2)
        d.ellipse([pts[-1][0] - 3, pts[-1][1] - 3, pts[-1][0] + 3, pts[-1][1] + 3], fill=(*accent, 80))
    base = img.convert("RGBA")
    base.alpha_composite(overlay)
    return base.convert("RGB")


def add_glow(img, accent):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    cx, cy = random.randint(int(W * 0.55), int(W * 0.9)), random.randint(60, int(H * 0.55))
    r = random.randint(140, 220)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*accent, 70))
    overlay = overlay.filter(ImageFilter.GaussianBlur(70))
    base = img.convert("RGBA")
    base.alpha_composite(overlay)
    return base.convert("RGB")


def add_scanlines(img):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for y in range(0, H, 4):
        d.line([(0, y), (W, y)], fill=(0, 0, 0, 16), width=1)
    base = img.convert("RGBA")
    base.alpha_composite(overlay)
    return base.convert("RGB")


for i, (c1, c2, accent) in enumerate(PALETTES, 1):
    img = gradient(c1, c2)
    img = add_circuits(img, accent)
    img = add_hexdump(img, accent)
    img = add_glow(img, accent)
    img = add_scanlines(img)
    img.save(f"{OUT}/{i:02d}.jpg", quality=85)
    print(f"{i:02d}.jpg done")
