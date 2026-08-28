# -*- coding: utf-8 -*-
"""生成博客头像和文章封面图（渐变 + 网格/线条装饰）"""
import math
import random
from PIL import Image, ImageDraw, ImageFilter

random.seed(42)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient(size, c1, c2, diagonal=True):
    w, h = size
    img = Image.new("RGB", size)
    px = img.load()
    for y in range(h):
        for x in range(w):
            t = (x / w + y / h) / 2 if diagonal else y / h
            px[x, y] = lerp(c1, c2, t)
    return img


def add_grid(img, color, step=46, width=1, alpha_color=None):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    w, h = img.size
    for x in range(0, w, step):
        d.line([(x, 0), (x, h)], fill=color, width=width)
    for y in range(0, h, step):
        d.line([(0, y), (w, y)], fill=color, width=width)
    base = img.convert("RGBA")
    base.alpha_composite(overlay)
    return base.convert("RGB")


def add_circuits(img, color, n=26):
    """随机折线，模拟电路走线"""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    w, h = img.size
    for _ in range(n):
        x, y = random.randint(0, w), random.randint(0, h)
        pts = [(x, y)]
        for _ in range(random.randint(2, 5)):
            if random.random() < 0.5:
                x += random.choice([-1, 1]) * random.randint(30, 160)
            else:
                y += random.choice([-1, 1]) * random.randint(30, 100)
            pts.append((x, y))
        d.line(pts, fill=color, width=2)
        d.ellipse([pts[-1][0] - 4, pts[-1][1] - 4, pts[-1][0] + 4, pts[-1][1] + 4], fill=color)
    base = img.convert("RGBA")
    base.alpha_composite(overlay)
    return base.convert("RGB")


def glow_ellipse(img, center, radius, color, blur=60):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    cx, cy = center
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=color)
    overlay = overlay.filter(ImageFilter.GaussianBlur(blur))
    base = img.convert("RGBA")
    base.alpha_composite(overlay)
    return base.convert("RGB")


# ---------- 头像：深底 + 霓虹绿盾牌 ----------
S = 300
avatar = gradient((S, S), (18, 24, 32), (10, 14, 20))
avatar = glow_ellipse(avatar, (S // 2, S // 2), 90, (46, 160, 124, 70))
d = ImageDraw.Draw(avatar)
# 盾牌轮廓
cx, cy = S // 2, S // 2 - 8
shield = [
    (cx, cy - 78), (cx + 62, cy - 52), (cx + 62, cy + 18),
    (cx + 40, cy + 62), (cx, cy + 88),
    (cx - 40, cy + 62), (cx - 62, cy + 18), (cx - 62, cy - 52),
]
d.line(shield + [shield[0]], fill=(74, 222, 178), width=6, joint="curve")
# 盾内锁
d.rounded_rectangle([cx - 22, cy - 8, cx + 22, cy + 40], radius=6, outline=(74, 222, 178), width=5)
d.arc([cx - 14, cy - 34, cx + 14, cy - 6], start=180, end=360, fill=(74, 222, 178), width=5)
d.ellipse([cx - 5, cy + 8, cx + 5, cy + 18], fill=(74, 222, 178))
d.line([(cx, cy + 18), (cx, cy + 28)], fill=(74, 222, 178), width=5)
avatar.save("static/img/avatar.png")

# ---------- 封面图 ----------
def cover(path, c1, c2, accent):
    img = gradient((1600, 640), c1, c2)
    img = add_grid(img, (*accent, 26), step=52)
    img = add_circuits(img, (*accent, 60))
    img = glow_ellipse(img, (1250, 180), 220, (*accent, 90), blur=90)
    img.save(path, quality=88)


# CTF WP 封面：深青 -> 墨绿，翠绿点缀
cover("content/post/ctf-wp/cover-ctf.png", (10, 25, 30), (14, 48, 44), (74, 222, 178))
# 笔记封面：深靛 -> 蓝紫，天蓝点缀
cover("content/post/notes/cover-note.png", (16, 20, 40), (32, 40, 78), (96, 165, 250))

print("done")
