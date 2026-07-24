# -*- coding: utf-8 -*-
"""WiAnote アプリアイコン生成（noteシリーズ統一：紺方眼地＋文字＋オレンジ下線）。
出力：App/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png（1024x1024・アルファなし）。"""
import os
from PIL import Image, ImageDraw, ImageFont

S = 1024
NAVY   = (23, 35, 63)     # 背景の紺
NAVY2  = (34, 49, 84)     # 方眼線
CREAM  = (245, 240, 228)  # 文字
ORANGE = (240, 150, 54)   # 下線・アクセント
BLUE   = (74, 120, 190)   # サブ

img = Image.new("RGB", (S, S), NAVY)
d = ImageDraw.Draw(img)

# 方眼（グリッド）
step = S // 12
for x in range(0, S + 1, step):
    d.line([(x, 0), (x, S)], fill=NAVY2, width=2)
for y in range(0, S + 1, step):
    d.line([(0, y), (S, y)], fill=NAVY2, width=2)

def font(path_candidates, size):
    for p in path_candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

bold = ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/Arialbd.ttf"]
reg  = ["C:/Windows/Fonts/arial.ttf"]
f_wia  = font(bold, 300)
f_note = font(reg, 140)
f_tag  = font(bold, 74)

def center_text(text, f, cy, fill):
    bb = d.textbbox((0, 0), text, font=f)
    w = bb[2] - bb[0]; h = bb[3] - bb[1]
    d.text(((S - w) / 2 - bb[0], cy - h / 2 - bb[1]), text, font=f, fill=fill)
    return w

# 上部の小さなギア（自動化＝RPAのモチーフ）を簡易に描く
cx, cyg, rr = S // 2, 250, 60
import math
pts = []
teeth = 8
for i in range(teeth * 2):
    ang = math.pi * i / teeth
    r = rr if i % 2 == 0 else rr * 0.68
    pts.append((cx + r * math.cos(ang), cyg + r * math.sin(ang)))
d.polygon(pts, fill=ORANGE)
d.ellipse([cx - 24, cyg - 24, cx + 24, cyg + 24], fill=NAVY)

# メインワードマーク "WiA"
w_wia = center_text("WiA", f_wia, 480, CREAM)

# オレンジの手描き風アンダーライン（WiAの下・noteの上）
uw = int(w_wia * 0.92)
ux0 = (S - uw) // 2
uy = 626
d.rounded_rectangle([ux0, uy, ux0 + uw, uy + 26], radius=13, fill=ORANGE)

# "note"（下線の下）
center_text("note", f_note, 742, BLUE)

# 下部ラベル "RPA"
center_text("RPA", f_tag, 892, CREAM)

out = os.path.join(os.path.dirname(__file__), "..", "App", "Assets.xcassets",
                   "AppIcon.appiconset", "AppIcon-1024.png")
img = img.convert("RGB")  # アルファなし（App Store要件）
img.save(out, "PNG")
print("saved:", os.path.abspath(out), img.size, img.mode)
