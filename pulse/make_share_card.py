#!/usr/bin/env python3
"""Compose a 1200x630 social share card (og:image) for the day's top story.

Usage: python3 pulse/make_share_card.py [YYYY-MM-DD]
Reads pulse/data/manifest.json (+ the day file), picks the top-scored item,
renders pulse/img/share/card.png. Run daily by the update agent after data is written.
Falls back gracefully if the topic illustration is missing.
"""
import json, os, sys, textwrap
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # website/
DATA = os.path.join(ROOT, "pulse", "data")
TOPICS = os.path.join(ROOT, "pulse", "img", "topics")
OUT = os.path.join(ROOT, "pulse", "img", "share")
os.makedirs(OUT, exist_ok=True)

W, H = 1200, 630
BG = (22, 23, 27)
CREAM = (236, 234, 227)
MUTED = (156, 156, 147)
FAINT = (110, 110, 103)
SEAL = (206, 74, 51)
SEAL_DEEP = (168, 54, 43)

FONTS = {
    "serif":  ["/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
               "/System/Library/Fonts/Supplemental/Georgia.ttf",
               "/Library/Fonts/Georgia.ttf"],
    "serifr": ["/System/Library/Fonts/Supplemental/Georgia.ttf"],
    "sans":   ["/System/Library/Fonts/Supplemental/Arial.ttf",
               "/System/Library/Fonts/Helvetica.ttc"],
    "sansb":  ["/System/Library/Fonts/Supplemental/Arial Bold.ttf",
               "/System/Library/Fonts/Helvetica.ttc"],
    "cjk":    ["/System/Library/Fonts/PingFang.ttc",
               "/System/Library/Fonts/Supplemental/Songti.ttc"],
}
def font(kind, size):
    for p in FONTS[kind]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()

TOPIC_IMG = {"TAVI":"aortic","Mitral":"mitral","Tricuspid":"tricuspid",
             "LAA":"laa","Imaging":"imaging","Other":"heart"}
JBOOST = {"NEJM":40,"Lancet":40,"JAMA Cardiology":26,"JAMA":34,"Circulation":30,
          "EHJ":30,"JACC: Cardiovascular Interventions":18,"JACC: Cardiovascular Imaging":18,
          "JACC: Case Reports":6,"JACC":26,"EuroIntervention":14,"New York Valves":8}
TBOOST = {"journal":8,"guideline":9,"conference":7,"regulatory":6,"industry":3,"news":4,"social":2}
def score(it):
    s = it.get("source","")
    jb = max([v for k,v in JBOOST.items() if k in s] + [0])
    return (it.get("weight",2))*20 + jb + TBOOST.get(it.get("type","news"),4)

def pick_day(date):
    m = json.load(open(os.path.join(DATA,"manifest.json")))
    days = sorted(m.get("days",[]))
    if not days: return None
    if date and date in days: d = date
    else: d = days[-1]
    day = json.load(open(os.path.join(DATA, d+".json")))
    items = sorted(day.get("items",[]), key=score, reverse=True)
    return (d, items[0]) if items else None

def wrap(draw, text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur+" "+w).strip()
        if draw.textlength(t, font=fnt) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def cover(img, bw, bh):
    iw, ih = img.size
    scale = max(bw/iw, bh/ih)
    nw, nh = int(iw*scale), int(ih*scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    x, y = (nw-bw)//2, (nh-bh)//2
    return img.crop((x, y, x+bw, y+bh))

def main():
    date = sys.argv[1] if len(sys.argv) > 1 else None
    picked = pick_day(date)
    card = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(card)
    if not picked:
        d.text((64, 280), "Structural Heart Focus", font=font("serif", 54), fill=CREAM)
        card.save(os.path.join(OUT, "card.png")); return
    day, it = picked

    # right illustration panel
    PANEL_X = 690
    topic_file = os.path.join(TOPICS, TOPIC_IMG.get(it.get("topic"), "heart") + ".png")
    if not os.path.exists(topic_file): topic_file = os.path.join(TOPICS, "heart.png")
    if os.path.exists(topic_file):
        art = cover(Image.open(topic_file).convert("RGB"), W-PANEL_X, H)
        card.paste(art, (PANEL_X, 0))
        # gradient blend on the seam so the light art melts into the dark card
        grad = Image.new("L", (160, H), 0)
        gd = ImageDraw.Draw(grad)
        for i in range(160): gd.line([(i,0),(i,H)], fill=int(255*(1-i/160)))
        dark = Image.new("RGB", (160, H), BG)
        card.paste(dark, (PANEL_X, 0), grad)
    d.line([(PANEL_X+158, 0), (PANEL_X+158, H)], fill=(60,60,66), width=1)

    LX = 64
    # brand row: seal + wordmark
    d.rounded_rectangle([LX, 60, LX+34, 94], radius=6, fill=SEAL_DEEP)
    d.text((LX+17, 77), "觅", font=font("cjk", 22), fill=CREAM, anchor="mm")
    bx = LX+48
    d.text((bx, 78), "千觅量子", font=font("cjk", 17), fill=MUTED, anchor="lm")
    bx += d.textlength("千觅量子", font=font("cjk", 17)) + 7
    d.text((bx, 77), "RYO · STRUCTURAL HEART FOCUS", font=font("sans", 17), fill=MUTED, anchor="lm")
    # topic kicker pill
    topic = (it.get("topic") or "").upper()
    if topic:
        kf = font("sansb", 15)
        tw = d.textlength(topic, font=kf)
        d.rounded_rectangle([LX, 128, LX+tw+26, 160], radius=4, fill=SEAL_DEEP)
        d.text((LX+13, 144), topic, font=kf, fill=CREAM, anchor="lm")
    # headline — auto-fit font size, cap at 4 lines with ellipsis
    title = it.get("title","")
    maxw = PANEL_X-LX-40
    size = 48
    for size in (48, 44, 40, 37):
        hf = font("serif", size)
        alllines = wrap(d, title, hf, maxw)
        if len(alllines) <= 4: break
    lines = alllines[:4]
    if len(alllines) > 4: lines[-1] = lines[-1].rstrip(" .,;:") + "…"
    lh = int(size*1.26)
    y = 205 if len(lines) >= 4 else 205 + (4-len(lines))*lh//2
    for ln in lines:
        d.text((LX, y), ln, font=hf, fill=CREAM); y += lh
    # source + date
    mf = font("sans", 20)
    src = it.get("source","")
    d.text((LX, y+16), f"{src}   ·   {day}", font=mf, fill=MUTED)
    # footer
    d.line([(LX, H-92), (PANEL_X-40, H-92)], fill=(60,60,66), width=1)
    d.text((LX, H-70), "kmryo.com", font=font("sansb", 22), fill=CREAM)
    d.text((LX+150, H-66), "· AI-curated structural-heart front page, daily",
           font=font("sans", 17), fill=FAINT)

    card.save(os.path.join(OUT, "card.png"), quality=92)
    print("wrote", os.path.join(OUT, "card.png"), "| top:", title[:60], "|", day)

if __name__ == "__main__":
    main()
