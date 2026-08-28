# -*- coding: utf-8 -*-
"""生成 Vortex 主题 logo：深色圆角底 + 翡翠绿旋涡"""
import math
from PIL import Image, ImageDraw, ImageFilter

S = 512
CENTER = S / 2

# 配色：从亮绿到青色
C_IN = (210, 255, 235)    # 旋涡中心（近白绿）
C_MID = (74, 222, 178)    # 主题翠绿
C_OUT = (20, 120, 100)    # 外圈深绿
BG = (13, 18, 24)         # 深色底


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient_color(t):
    """t: 0(中心) -> 1(外圈)"""
    if t < 0.5:
        return lerp(C_IN, C_MID, t * 2)
    return lerp(C_MID, C_OUT, (t - 0.5) * 2)


def rounded_mask(size, radius):
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return m


# ---- 底层：深色圆角方块 ----
img = Image.new("RGB", (S, S), BG)

# 中心辉光
glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.ellipse([CENTER - 150, CENTER - 150, CENTER + 150, CENTER + 150], fill=(74, 222, 178, 60))
glow = glow.filter(ImageFilter.GaussianBlur(70))
img = Image.alpha_composite(img.convert("RGBA"), glow)

# ---- 旋涡：3 条对数螺旋臂 ----
spiral = Image.new("RGBA", (S, S), (0, 0, 0, 0))
sd = ImageDraw.Draw(spiral)

ARMS = 2
TURNS = 1.75         # 螺旋圈数
R_MAX = 210          # 最大半径
STEPS = 260

for arm in range(ARMS):
    offset = arm * (2 * math.pi / ARMS)
    pts = []
    for i in range(STEPS):
        t = i / (STEPS - 1)                     # 0 中心 -> 1 外圈
        theta = offset + t * TURNS * 2 * math.pi
        r = R_MAX * (t ** 0.7)
        x = CENTER + r * math.cos(theta)
        y = CENTER + r * math.sin(theta)
        pts.append((x, y, t))
    # 分段画线，粗细和颜色随半径变化
    for i in range(1, len(pts)):
        x0, y0, t0 = pts[i - 1]
        x1, y1, t1 = pts[i]
        w = int(3 + 15 * (1 - t1))              # 中心粗、外圈细
        sd.line([(x0, y0), (x1, y1)], fill=(*gradient_color(t1), 235), width=w)

# 中心亮点
sd.ellipse([CENTER - 26, CENTER - 26, CENTER + 26, CENTER + 26], fill=(*C_IN, 255))

# 旋涡整体加一点辉光
spiral_glow = spiral.filter(ImageFilter.GaussianBlur(6))
img = Image.alpha_composite(img, spiral_glow)
img = Image.alpha_composite(img, spiral)

# ---- 应用圆角蒙版 ----
mask = rounded_mask(S, 110)
out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
out.paste(img, (0, 0), mask)

out.save("static/img/avatar.png")
print("avatar.png saved")
