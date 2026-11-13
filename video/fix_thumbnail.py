#!/usr/bin/env python3
"""Fix the YouTube thumbnail badge geometry.

The skill's esl_brand.thumbnail draws the badge with a fixed 200pt font that
overlaps and overflows its box. This script reuses the skill's rendering for
everything else (badge=None) and redraws the badge with measured, centered
text on the 1280x720 result. Run after build.py thumbnail.
"""
import sys, importlib.util, json
from pathlib import Path
from PIL import Image, ImageDraw

spec = importlib.util.spec_from_file_location("esl_brand", str(Path("/mnt/c/Users/danie") / ".agents/skills/esl-demo-video/scripts/esl_brand.py"))
esl = importlib.util.module_from_spec(spec); spec.loader.exec_module(esl)

cfg = json.load(open("video.json"))
t = cfg["thumbnail"]
base = esl.thumbnail(t["title"], t.get("subtitle", ""), t.get("product", ""), badge=None)
d = ImageDraw.Draw(base)

badge = t["badge"]
box = (810, 347, 1240, 567)  # widened from the skill's 2/3-scale box so measured text fits
d.rounded_rectangle(box, radius=27, fill=esl.INK)

f_big = esl.font(48, True); f_arrow = esl.font(30, True); f_cap = esl.font(24)
w_from = d.textlength(badge["from"], font=f_big)
w_arrow = d.textlength("\u2192", font=f_arrow)
w_to = d.textlength(badge["to"], font=f_big)
gap = 14
total = w_from + gap + w_arrow + gap + w_to
x = box[0] + (box[2] - box[0] - total) / 2
y = box[1] + 40
d.text((x, y), badge["from"], font=f_big, fill=esl.AMBER)
d.text((x + w_from + gap, y + 12), "\u2192", font=f_arrow, fill="#ffffff")
d.text((x + w_from + gap + w_arrow + gap, y), badge["to"], font=f_big, fill=esl.BLUE)
cap = badge.get("caption", "")
if cap:
    w_cap = d.textlength(cap, font=f_cap)
    d.text((box[0] + (box[2] - box[0] - w_cap) / 2, box[1] + 150), cap, font=f_cap, fill="#ffffff")
base.save("output/youtube-thumbnail.jpg", quality=92)
print("thumbnail fixed:", base.size)
