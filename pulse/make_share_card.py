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
               "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"],
    "serifr": ["/System/Library/Fonts/Supplemental/Georgia.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"],
    "sans":   ["/System/Library/Fonts/Supplemental/Arial.ttf",
               "/System/Library/Fonts/Helvetica.ttc",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    "sansb":  ["/System/Library/Fonts/Supplemental/Arial Bold.ttf",
               "/System/Library/Fonts/Helvetica.ttc",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "cjk":    ["/System/Library/Fonts/PingFang.ttc",
               "/System/Library/Fonts/Supplemental/Songti.ttc",
               "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
               "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
               "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"],
}
HAS_CJK = any(os.path.exists(p) for p in FONTS["cjk"])
def font(kind, size):
    for p in FONTS[kind]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()

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

# ---- small-element line art (mirrors the ELEMENTS library in index.html) ----
# One anatomical/device element per story, matched by topic + type; drawn around a
# local (0,0) with radius <= 150, in thin cream linework with a muted topic tone.
TONES = {"TAVI":(196,137,123),"Mitral":(147,169,141),"Tricuspid":(138,157,179),
         "LAA":(191,164,127),"Imaging":(161,146,180),"Other":(169,156,140)}
TYPE_VARIANT = {"journal":0,"conference":0,"news":0,"guideline":2,"social":2,
                "regulatory":1,"industry":1}
LINE = CREAM + (232,)

def qbez(p0, p1, p2, n=28):
    return [(p0[0]*(1-t)**2 + 2*p1[0]*t*(1-t) + p2[0]*t*t,
             p0[1]*(1-t)**2 + 2*p1[1]*t*(1-t) + p2[1]*t*t)
            for t in (i/n for i in range(n+1))]

def cbez(p0, p1, p2, p3, n=32):
    return [(p0[0]*(1-t)**3 + 3*p1[0]*t*(1-t)**2 + 3*p2[0]*t*t*(1-t) + p3[0]*t**3,
             p0[1]*(1-t)**3 + 3*p1[1]*t*(1-t)**2 + 3*p2[1]*t*t*(1-t) + p3[1]*t**3)
            for t in (i/n for i in range(n+1))]

import math
def circle_pts(r, a0, a1, n=40):
    return [(r*math.cos(math.radians(a0+(a1-a0)*i/n)),
             r*math.sin(math.radians(a0+(a1-a0)*i/n))) for i in range(n+1)]

class Pen:
    """Draws in element-local coords (y down, like the SVG library) onto an RGBA layer."""
    def __init__(self, draw, cx, cy, s):
        self.d, self.cx, self.cy, self.s = draw, cx, cy, s
    def P(self, pts):
        return [(self.cx + x*self.s, self.cy + y*self.s) for x, y in pts]
    def line(self, pts, color=LINE, w=4):
        self.d.line(self.P(pts), fill=color, width=w, joint="curve")
    def dashed(self, pts, color, w=3, on=3, off=6):
        pts = self.P(pts)
        for i in range(0, len(pts)-1, on+off):
            seg = pts[i:i+on+1]
            if len(seg) > 1: self.d.line(seg, fill=color, width=w)
    def poly(self, pts, fill):
        self.d.polygon(self.P(pts), fill=fill)
    def dot(self, x, y, r, color):
        (X, Y), R = self.P([(x, y)])[0], r*self.s
        self.d.ellipse([X-R, Y-R, X+R, Y+R], fill=color)
    def ring(self, r, color=LINE, w=4, ry=None):
        (X, Y), R = self.P([(0, 0)])[0], r*self.s
        RY = (ry if ry else r)*self.s
        self.d.ellipse([X-R, Y-RY, X+R, Y+RY], outline=color, width=w)
    def dashed_ring(self, r, color, w=3, ry=None):
        rr = ry if ry else r
        pts = [(r*math.cos(math.radians(a)), rr*math.sin(math.radians(a))) for a in range(0, 361, 3)]
        self.dashed(pts, color, w=w, on=2, off=4)
    def rrect(self, x0, y0, x1, y1, rad, outline, w=4, fill=None):
        box = self.P([(x0, y0), (x1, y1)])
        self.d.rounded_rectangle([box[0][0], box[0][1], box[1][0], box[1][1]],
                                 radius=rad*self.s, outline=outline, width=w, fill=fill)

def art_tavi(p, tone, vi):
    faint, soft = tone + (30,), tone + (110,)
    if vi == 1:      # THV stent frame
        rail = LINE[:3] + (90,)
        p.line([(-90, -118), (-90, 118)], rail, 3); p.line([(90, -118), (90, 118)], rail, 3)
        for y0, y1 in ((-118, -59), (-59, 0), (0, 59), (59, 118)):
            for k in range(-3, 3):
                x = k*30
                p.line([(x, y0), (x+30, y1)], LINE, 3); p.line([(x, y1), (x+30, y0)], LINE, 3)
        p.line(qbez((-58, -70), (0, -22), (58, -70)), tone + (230,), 4)
    elif vi == 2:    # trial curves
        ax = LINE[:3] + (115,)
        p.line([(-120, -110), (-120, 110), (130, 110)], ax, 3)
        p.line([(-120, -72), (-64, -72), (-64, -60), (-6, -60), (-6, -44), (56, -44), (56, -34), (124, -34)], LINE, 4)
        p.line([(-120, -72), (-84, -72), (-84, -46), (-22, -46), (-22, -10), (38, -10), (38, 14), (124, 14)], tone + (235,), 4)
        p.dot(124, -34, 4.5, LINE); p.dot(124, 14, 4.5, tone + (255,))
    else:            # aortic valve, short axis
        p.poly(circle_pts(118, -90, 30) + [(0, 0)], faint)
        p.ring(118, LINE, 4); p.dashed_ring(140, LINE[:3] + (90,), 3)
        p.line(qbez((0, 0), (-16, -62), (0, -118)), LINE, 4)
        p.line(qbez((0, 0), (62, 20), (102, 59)), LINE, 4)
        p.line(qbez((0, 0), (-48, 44), (-102, 59)), LINE, 4)
        p.dot(0, 0, 5.5, LINE)

def art_mitral(p, tone, vi):
    faint = tone + (30,)
    if vi == 1:      # edge-to-edge clip
        p.line(qbez((-140, -52), (-64, -24), (-16, 14)), LINE, 4)
        p.line(qbez((140, -52), (64, -24), (16, 14)), LINE, 4)
        ghost = LINE[:3] + (90,)
        p.line(qbez((-124, -34), (-70, 6), (-26, 0)), ghost, 3)
        p.line(qbez((124, -34), (70, 6), (26, 0)), ghost, 3)
        p.line([(-16, 14), (-11, 32)], LINE, 3); p.line([(16, 14), (11, 32)], LINE, 3)
        p.rrect(-11, 20, 11, 72, 5, LINE, 3, fill=tone + (64,))
        p.line([(0, 72), (0, 112)], LINE[:3] + (128,), 3)
    elif vi == 2:    # annuloplasty ring
        pts = (qbez((-22, -102), (-110, -86), (-110, -8)) + qbez((-110, -8), (-108, 62), (-42, 84))
               + qbez((-42, 84), (32, 102), (86, 62)) + qbez((86, 62), (118, 32), (108, -24)))
        p.line(pts, LINE, 5)
        for x, y in ((-22, -102), (-82, -64), (-109, -8), (-88, 52), (-20, 92), (52, 88), (100, 40), (108, -24)):
            p.dot(x, y, 3.5, tone + (255,))
    else:            # mitral valve, short axis
        p.ring(132, LINE, 4, ry=98); p.dashed_ring(152, LINE[:3] + (80,), 3, ry=118)
        aml = qbez((-106, -18), (0, -70), (106, -18)) + qbez((106, -18), (0, 74), (-106, -18))
        p.poly(aml, faint)
        p.line(qbez((-106, -18), (0, -70), (106, -18)), LINE, 3)
        p.line(qbez((-106, -18), (0, 74), (106, -18)), LINE, 4)
        p.line([(-44, 46), (-35, 33)], LINE[:3] + (165,), 3); p.line([(35, 46), (44, 32)], LINE[:3] + (165,), 3)
        p.dot(-106, -18, 4, LINE); p.dot(106, -18, 4, LINE)

def art_tricuspid(p, tone, vi):
    if vi in (1, 2):  # tricuspid edge-to-edge
        p.line(qbez((-142, -58), (-64, -30), (-14, 8)), LINE, 4)
        p.line(qbez((142, -58), (66, -30), (20, 4)), LINE, 4)
        p.line(qbez((-24, 118), (-2, 60), (4, 26)), LINE, 4)
        p.line([(-14, 8), (-8, 26)], LINE, 3); p.line([(20, 4), (14, 24)], LINE, 3)
        p.rrect(-8, 16, 13, 64, 5, LINE, 3, fill=tone + (64,))
        p.line(qbez((2, 64), (2, 96), (22, 112)), LINE[:3] + (128,), 3)
    else:             # tricuspid valve, short axis
        p.poly(circle_pts(118, -105, 25) + [(6, -4)], tone + (30,))
        p.ring(118, LINE, 4); p.dashed_ring(140, LINE[:3] + (90,), 3)
        p.line(qbez((6, -4), (-8, -60), (-31, -114)), LINE, 4)
        p.line(qbez((6, -4), (60, 14), (107, 50)), LINE, 4)
        p.line(qbez((6, -4), (-44, 40), (-97, 68)), LINE, 4)
        for x, y in ((-31, -114), (107, 50), (-97, 68)): p.dot(x, y, 4, LINE)

def art_laa(p, tone, vi):
    if vi in (1, 2):  # occluder plug
        (X, Y) = p.P([(0, -44)])[0]
        R, RY = 86*p.s, 20*p.s
        p.d.ellipse([X-R, Y-RY, X+R, Y+RY], outline=LINE, width=4, fill=tone + (38,))
        p.line(qbez((-86, -44), (-92, 34), (-46, 58)), LINE, 4)
        p.line(qbez((86, -44), (92, 34), (46, 58)), LINE, 4)
        p.line(qbez((-46, 58), (0, 74), (46, 58)), LINE, 4)
        for x, y, dx, dy in ((-80, 6, -11, 6), (80, 6, 11, 6), (-62, 40, -9, 10), (62, 40, 9, 10)):
            p.line([(x, y), (x+dx, y+dy)], LINE, 3)
        p.line([(0, -66), (0, -46)], LINE, 3); p.dot(0, -73, 5, LINE)
    else:             # appendage windsock
        sock = (qbez((-124, 16), (-136, -78), (-44, -104)) + qbez((-44, -104), (52, -128), (96, -74))
                + qbez((96, -74), (130, -32), (100, -2)) + qbez((100, -2), (142, 22), (112, 62))
                + qbez((112, 62), (76, 106), (4, 92)) + qbez((4, 92), (-92, 118), (-124, 16)))
        p.poly(sock, tone + (26,)); p.line(sock, LINE, 4)
        comb = LINE[:3] + (115,)
        p.line(qbez((-84, -44), (-20, -58), (44, -66)), comb, 2)
        p.line(qbez((-78, -12), (-10, -22), (58, -28)), comb, 2)
        p.line(qbez((-66, 22), (0, 14), (62, 8)), comb, 2)
        p.line(qbez((-48, 54), (12, 48), (64, 40)), comb, 2)
        p.dashed(qbez((96, -74), (66, -8), (112, 62)), LINE[:3] + (128,), 3)

def art_imaging(p, tone, vi):
    if vi in (1, 2):  # spectral doppler + ECG lead
        ecg = LINE[:3] + (140,)
        p.line([(-130, -76), (-74, -76), (-62, -100), (-50, -58), (-42, -76), (130, -76)], ecg, 2)
        p.line([(-130, -20), (130, -20)], LINE[:3] + (128,), 3)
        for x0, alpha in ((-98, 90), (-18, 90), (62, 50)):
            env = qbez((x0, -20), (x0+12, 74), (x0+34, 78)) + qbez((x0+34, 78), (x0+52, 74), (x0+64, -20))
            p.poly(env, tone + (alpha,)); p.line(env, LINE[:3] + (160,), 3)
    else:             # echo sector with caliper
        sector = [(0, -128)] + qbez((-116, 92), (0, 132), (116, 92))[::-1] + [(0, -128)]
        p.poly(sector, tone + (20,))
        p.line([(-116, 92), (0, -128), (116, 92)], LINE[:3] + (150,), 3)
        p.line(qbez((-116, 92), (0, 132), (116, 92)), LINE[:3] + (150,), 3)
        p.line(qbez((-38, -56), (0, -38), (38, -56)), LINE[:3] + (128,), 3)
        p.line(qbez((-66, -8), (0, 24), (66, -8)), LINE[:3] + (82,), 3)
        p.line(qbez((-40, 42), (0, 14), (40, 42)), LINE, 4)
        p.dot(-40, 42, 4, LINE); p.dot(40, 42, 4, LINE)
        p.dashed([(-40+i*4, 42) for i in range(21)], LINE[:3] + (165,), 2)

def art_other(p, tone, vi):
    if vi == 1:      # J-tip guidewire
        p.dashed(qbez((-136, 64), (-30, 52), (30, 6)), LINE[:3] + (100,), 3)
        wire = (qbez((-136, 96), (-40, 84), (18, 40)) + qbez((18, 40), (84, -10), (76, -58))
                + qbez((76, -58), (70, -92), (38, -86)) + qbez((38, -86), (10, -80), (22, -54)))
        p.line(wire, LINE, 4)
        p.dot(22, -54, 4.5, LINE)
    elif vi == 2:    # small heart contour + ECG lead
        k = 0.55
        heart = (cbez((0, 122), (-122, 32), (-152, -60), (-82, -112)) + cbez((-82, -112), (-40, -142), (0, -112), (0, -70))
                 + cbez((0, -70), (0, -112), (40, -142), (82, -112)) + cbez((82, -112), (152, -60), (122, 32), (0, 122)))
        heart = [(x*k, y*k) for x, y in heart]
        p.poly(heart, tone + (36,)); p.line(heart, LINE, 4)
        p.line([(-140, 108), (-64, 108), (-38, 62), (-6, 132), (18, 108), (140, 108)], LINE[:3] + (205,), 3)
    else:            # arterial pressure trace
        p.line([(-130, 60), (130, 60)], LINE[:3] + (78,), 2)
        beat = lambda dx: (cbez((-96+dx, 58), (-88+dx, 58), (-86+dx, -52), (-66+dx, -52))
                           + cbez((-66+dx, -52), (-52+dx, -52), (-54+dx, -6), (-44+dx, -2))
                           + cbez((-44+dx, -2), (-40+dx, 0), (-38+dx, -14), (-30+dx, -12))
                           + qbez((-30+dx, -12), (-16+dx, -6), (-8+dx, 42)) + [(-4+dx, 58)])
        p.line([(-130, 58), (-96, 58)] + beat(0) + [(22, 58)] + beat(118) + [(130, 58)], LINE, 4)
        p.dot(-44, -2, 4, tone + (255,)); p.dot(74, -2, 4, tone + (255,))

ART = {"TAVI": art_tavi, "Mitral": art_mitral, "Tricuspid": art_tricuspid,
       "LAA": art_laa, "Imaging": art_imaging, "Other": art_other}

# Morandi still-life panel: two-tone colour field, the topic's bottle with the element
# printed on its glaze, and the element "poured out" beside it (mirrors index.html).
PALS = {  # field, table, vessel, ink, accent
    "TAVI":      ((216,199,189),(194,171,158),(176,141,127),(95,74,65),(165,106,88)),
    "Mitral":    ((212,215,200),(188,194,172),(150,164,136),(78,90,71),(117,135,106)),
    "Tricuspid": ((205,212,217),(178,191,199),(140,160,174),(70,84,95),(95,122,140)),
    "LAA":       ((223,213,192),(203,185,149),(180,160,120),(99,86,64),(150,129,79)),
    "Imaging":   ((214,207,219),(191,179,201),(158,144,178),(81,73,101),(122,108,147)),
    "Other":     ((216,211,202),(193,186,174),(166,157,143),(87,80,70),(126,116,102)),
}
BOTTLE_PTS = {
    "TAVI": [(-58,0),(-58,-118)] + qbez((-58,-118),(-58,-146),(-30,-156),12)
            + [(-16,-162),(-16,-222)] + qbez((-16,-222),(-16,-230),(-8,-230),6) + [(8,-230)]
            + qbez((8,-230),(16,-230),(16,-222),6) + [(16,-162),(30,-156)]
            + qbez((30,-156),(58,-146),(58,-118),12) + [(58,0)],
    "Mitral": qbez((-33,-148),(-84,-136),(-84,-76)) + qbez((-84,-76),(-84,-20),(-44,-6))
              + qbez((-44,-6),(-24,0),(0,0)) + qbez((0,0),(24,0),(44,-6))
              + qbez((44,-6),(84,-20),(84,-76)) + qbez((84,-76),(84,-136),(33,-148))
              + [(33,-172)] + qbez((33,-172),(33,-180),(25,-180),6) + [(-25,-180)]
              + qbez((-25,-180),(-33,-180),(-33,-172),6),
    "Tricuspid": [(-62,0),(-70,-120)] + qbez((-70,-120),(-72,-152),(-38,-160),12)
                 + [(-20,-164),(-20,-196)] + qbez((-20,-196),(-20,-204),(-10,-204),6) + [(14,-204)]
                 + qbez((14,-204),(22,-204),(20,-196),6) + [(16,-164),(34,-158)]
                 + qbez((34,-158),(66,-150),(64,-118),12) + [(56,0)],
    "LAA": [(-88,0)] + qbez((-88,0),(-96,-8),(-96,-52),8) + qbez((-96,-52),(-96,-118),(-48,-132))
           + [(-30,-136),(-30,-148)] + qbez((-30,-148),(-30,-154),(-22,-154),6) + [(22,-154)]
           + qbez((22,-154),(30,-154),(30,-148),6) + [(30,-136),(48,-132)]
           + qbez((48,-132),(96,-118),(96,-52)) + qbez((96,-52),(96,-8),(88,0),8),
    "Imaging": [(-74,0),(-20,-160),(-20,-192)] + qbez((-20,-192),(-20,-200),(-12,-200),6)
                + [(12,-200)] + qbez((12,-200),(20,-200),(20,-192),6) + [(20,-160),(74,0)],
    "Other": [(-52,0),(-52,-158)] + qbez((-52,-158),(-52,-170),(-42,-170),6) + [(42,-170)]
             + qbez((42,-170),(52,-170),(52,-158),6) + [(52,0)],
}
BOTTLE_EXTRA = {
    "Tricuspid": qbez((20,-196),(66,-188),(62,-142)) + qbez((62,-142),(60,-122),(42,-118)),
    "Other": [(-52,-140),(52,-140)],
}
BOTTLE_BELLY = {"TAVI":(0,-84,0.38),"Mitral":(0,-78,0.44),"Tricuspid":(0,-84,0.36),
                "LAA":(0,-66,0.48),"Imaging":(0,-60,0.3),"Other":(0,-78,0.36)}

def render_element(topic, vi, s):
    layer = Image.new("RGBA", (480, 480), (0, 0, 0, 0))
    p = Pen(ImageDraw.Draw(layer), 240, 240, s)
    ART[topic](p, TONES.get(topic, TONES["Other"]), vi)
    return layer

def tint(layer, color, alpha=1.0):
    a = layer.split()[3]
    if alpha < 1: a = a.point(lambda v: int(v*alpha))
    out = Image.new("RGBA", layer.size, color + (0,))
    out.putalpha(a)
    return out

def draw_panel_art(card, it, panel_x):
    from PIL import ImageChops
    topic = it.get("topic") or "Other"
    if topic not in ART: topic = "Other"
    vi = TYPE_VARIANT.get(it.get("type") or "news", 0)
    field, table, vessel, ink, accent = PALS[topic]
    d = ImageDraw.Draw(card)
    TABLE_Y = 430
    d.rectangle([panel_x, 0, W, H], fill=field)
    d.rectangle([panel_x, TABLE_Y, W, H], fill=table)
    bx, by, s = 968, TABLE_Y + 6, 1.15
    pts = [(bx + x*s, by + y*s) for x, y in BOTTLE_PTS[topic]]
    over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(over)
    hw = max(x for x, _ in BOTTLE_PTS[topic])
    od.ellipse([bx-(hw+28)*s, by-13, bx+(hw+34)*s, by+15], fill=ink + (34,))
    od.polygon(pts, fill=vessel + (255,))
    od.line(pts + [pts[0]], fill=ink + (128,), width=4, joint="curve")
    if topic in BOTTLE_EXTRA:
        xpts = [(bx + x*s, by + y*s) for x, y in BOTTLE_EXTRA[topic]]
        od.line(xpts, fill=ink + (128,), width=6 if topic == "Tricuspid" else 3, joint="curve")
    card.paste(over, (0, 0), over)
    # glaze print, clipped to the bottle
    bex, bey, ps = BOTTLE_BELLY[topic]
    el = tint(render_element(topic, vi, ps*s), ink, 0.62)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    canvas.paste(el, (int(bx + bex*s) - 240, int(by + bey*s) - 240))
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    canvas.putalpha(ImageChops.multiply(canvas.split()[3], mask))
    card.paste(canvas, (0, 0), canvas)
    # the element, poured out onto the wall beside the bottle
    poured = tint(render_element(topic, vi, 0.6), ink, 0.9)
    card.paste(poured, (int(bx - 185) - 240, 230 - 240), poured)
    # a few drops along the pour
    mouth_y = by + min(y for _, y in BOTTLE_PTS[topic])*s
    drops = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(drops)
    for i, (fx, fy, r) in enumerate(((0.3, 0.35, 6), (0.55, 0.6, 5), (0.78, 0.85, 4))):
        x = bx + (bx - 185 - bx)*fx
        y = mouth_y + (230 - mouth_y)*fy + 26*i
        col = accent if i == 1 else ink
        dd.ellipse([x-r, y-r, x+r, y+r], fill=col + (200,))
    card.paste(drops, (0, 0), drops)

def main():
    date = sys.argv[1] if len(sys.argv) > 1 else None
    picked = pick_day(date)
    card = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(card)
    if not picked:
        d.text((64, 280), "Structural Heart Focus", font=font("serif", 54), fill=CREAM)
        card.save(os.path.join(OUT, "card.png")); return
    day, it = picked

    # right illustration panel — small-element line art matched to topic + type
    PANEL_X = 690
    draw_panel_art(card, it, PANEL_X)
    d.line([(PANEL_X+18, 0), (PANEL_X+18, H)], fill=(60,60,66), width=1)

    LX = 64
    # brand row: seal + wordmark
    d.rounded_rectangle([LX, 60, LX+34, 94], radius=6, fill=SEAL_DEEP)
    if HAS_CJK:
        d.text((LX+17, 77), "觅", font=font("cjk", 22), fill=CREAM, anchor="mm")
    else:
        d.text((LX+17, 76), "R", font=font("serif", 20), fill=CREAM, anchor="mm")
    bx = LX+48
    if HAS_CJK:
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
