#!/usr/bin/env python3
"""Assemble the year's defining structural-heart items into an English HTML email.

Usage:  python3 pulse/make_yearly.py [YYYY]
        (defaults to the year of the latest day in manifest)

Reads pulse/data/*.json, selects every item of that calendar year, ranks them
(journal impact + weight + type, same scoring as the share card), and writes:
    pulse/yearly/YYYY.html   — the email body (inline-styled, email-client-safe)
laid out as: the story of the year, then the top items per topic section.
Prints a suggested subject line to stdout as `SUBJECT: ...`.

No secrets, no network. The yearly cloud agent runs this, then POSTs the HTML
to Buttondown with its API key (see pulse/AGENT-YEARLY.md).
"""
import json, os, sys, html as _html
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # website/
DATA = os.path.join(ROOT, "pulse", "data")
OUT = os.path.join(ROOT, "pulse", "yearly")
os.makedirs(OUT, exist_ok=True)

# palette (light editorial — safest across email clients)
PAPER = "#F7F5EF"; INK = "#1A1B1E"; MUTED = "#6E6E66"; SEAL = "#B23A28"; HAIR = "#DED9CE"
SUPPORT_URL = "https://buy.stripe.com/aFa6oJ91Ab7v88i38icEw00"

JBOOST = {"NEJM":40,"Lancet":40,"JAMA Cardiology":26,"JAMA":34,"Circulation":30,
          "EHJ":30,"JACC: Cardiovascular Interventions":18,"JACC: Cardiovascular Imaging":18,
          "JACC: Case Reports":6,"JACC":26,"EuroIntervention":14,"New York Valves":8}
TBOOST = {"journal":8,"guideline":9,"conference":7,"regulatory":6,"industry":3,"news":4,"social":2}
def score(it):
    s = it.get("source","")
    jb = max([v for k,v in JBOOST.items() if k in s] + [0])
    return (it.get("weight",2))*20 + jb + TBOOST.get(it.get("type","news"),4)

TOPIC_ORDER = ["TAVI", "Mitral", "Tricuspid", "LAA", "Imaging", "Other"]
TOPIC_LABEL = {"TAVI":"Aortic / TAVI", "Mitral":"Mitral", "Tricuspid":"Tricuspid",
               "LAA":"LAA &amp; stroke prevention", "Imaging":"Imaging &amp; AI",
               "Other":"Structural / other"}
PER_TOPIC = 5

def esc(t): return _html.escape(t or "", quote=True)

def load_days():
    m = json.load(open(os.path.join(DATA, "manifest.json")))
    return sorted(m.get("days", []))

def target_year(arg, days):
    if arg:
        return int(arg[:4])
    if days:
        return datetime.strptime(days[-1], "%Y-%m-%d").date().year
    raise SystemExit("no data days available")

def gather(days, year):
    items, ndays = [], 0
    for ds in days:
        d = datetime.strptime(ds, "%Y-%m-%d").date()
        if d.year == year:
            ndays += 1
            day = json.load(open(os.path.join(DATA, ds + ".json")))
            for it in day.get("items", []):
                it["_date"] = ds
                items.append(it)
    items.sort(key=score, reverse=True)
    return items, ndays

def lead_block(it):
    topic = esc((it.get("topic") or "").upper())
    pill = (f'<span style="display:inline-block;background:{SEAL};color:#fff;'
            f'font:600 11px/1 Arial,sans-serif;letter-spacing:.12em;'
            f'padding:5px 9px;border-radius:3px;">{topic} &nbsp;·&nbsp; STORY OF THE YEAR</span>' if topic else "")
    return f"""
    <tr><td style="padding:8px 0 0;">{pill}</td></tr>
    <tr><td style="padding:10px 0 0;">
      <a href="{esc(it.get('url'))}" style="text-decoration:none;color:{INK};">
        <span style="font:600 27px/1.15 Georgia,'Times New Roman',serif;color:{INK};">{esc(it.get('title'))}</span>
      </a>
    </td></tr>
    <tr><td style="padding:8px 0 0;font:400 13px/1 Arial,sans-serif;color:{MUTED};letter-spacing:.02em;">
      {esc(it.get('source'))} &nbsp;·&nbsp; {esc(it.get('_date'))}
    </td></tr>
    <tr><td style="padding:12px 0 0;font:400 16px/1.6 Georgia,serif;color:#33332e;">
      {esc(it.get('summary_en') or it.get('summary_zh'))}
    </td></tr>
    <tr><td style="padding:16px 0 0;">
      <a href="{esc(it.get('url'))}" style="font:600 14px/1 Arial,sans-serif;color:{SEAL};text-decoration:none;">Read the source &rsaquo;</a>
    </td></tr>
    """

def row_block(it):
    return f"""
    <tr><td style="padding:20px 0;border-top:1px solid {HAIR};">
      <div style="margin:0 0 5px;"><span style="font:400 11px/1 Arial,sans-serif;color:{MUTED};">{esc(it.get('source'))} · {esc(it.get('_date'))}</span></div>
      <a href="{esc(it.get('url'))}" style="text-decoration:none;color:{INK};">
        <span style="font:600 18px/1.3 Georgia,serif;color:{INK};">{esc(it.get('title'))}</span>
      </a>
      <div style="margin:6px 0 0;font:400 14px/1.55 Georgia,serif;color:#4a4a44;">{esc(it.get('summary_en') or it.get('summary_zh'))}</div>
    </td></tr>
    """

def section(topic, items):
    if not items: return ""
    hdr = (f'<tr><td style="padding:34px 0 4px;font:700 12px/1 Arial,sans-serif;'
           f'letter-spacing:.18em;color:{MUTED};text-transform:uppercase;">'
           f'{TOPIC_LABEL.get(topic, topic)}</td></tr>')
    return hdr + f'<tr><td><table role="presentation" width="100%" cellpadding="0" cellspacing="0">' \
               + "".join(row_block(it) for it in items) + '</table></td></tr>'

def build(items, ndays, year):
    lead = items[0] if items else None
    n = len(items)
    subject = f"The Year in Structural Heart — {year}"
    pre = (esc(lead.get('title')) if lead else "The year in structural heart") + \
          f" · {n} items curated in {year}, these defined the field"

    lead_html = lead_block(lead) if lead else \
        f'<tr><td style="padding:24px 0;font:400 16px/1.6 Georgia,serif;color:{MUTED};">No items curated this year.</td></tr>'
    by_topic = {}
    for it in items[1:]:
        by_topic.setdefault(it.get("topic") or "Other", []).append(it)
    sections = "".join(section(t, by_topic.get(t, [])[:PER_TOPIC]) for t in TOPIC_ORDER)
    stat = (f'<tr><td style="padding:14px 0 0;font:400 13px/1.5 Arial,sans-serif;color:{MUTED};">'
            f'{n} items curated across {ndays} days in {year}. These are the ones that defined the field.</td></tr>'
            if n else "")

    return subject, f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:{PAPER};">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{pre}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{PAPER};">
<tr><td align="center" style="padding:32px 16px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:600px;max-width:600px;background:{PAPER};">

  <!-- masthead -->
  <tr><td style="padding:0 0 6px;">
    <span style="display:inline-block;width:16px;height:16px;background:{SEAL};border-radius:3px;vertical-align:middle;"></span>
    <span style="font:700 12px/1 Arial,sans-serif;letter-spacing:.2em;color:{MUTED};vertical-align:middle;padding-left:8px;">RYO · STRUCTURAL HEART FOCUS</span>
  </td></tr>
  <tr><td style="padding:14px 0 0;border-bottom:2px solid {INK};">
    <span style="font:600 15px/1 Georgia,serif;color:{INK};">The Year in Structural Heart</span>
    <span style="font:400 13px/1 Arial,sans-serif;color:{MUTED};float:right;padding-top:2px;">{year}</span>
  </td></tr>
  {stat}

  <!-- story of the year -->
  <tr><td style="padding:22px 0 0;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{lead_html}</table></td></tr>

  <!-- topic sections -->
  {sections}

  <!-- footer -->
  <tr><td style="padding:34px 0 0;border-top:2px solid {INK};">
    <div style="font:400 14px/1.6 Georgia,serif;color:{MUTED};padding-top:16px;">
      Curated from inside the Zurich hybrid room by <b style="color:{INK};">Dr. Mi Chen</b> — structural heart interventionist, cardiac surgeon, co-founder of CardioAI.
    </div>
    <div style="padding:16px 0 0;">
      <a href="https://www.kmryo.com" style="font:600 14px/1 Arial,sans-serif;color:{SEAL};text-decoration:none;">kmryo.com &rsaquo;</a>
      <span style="font:400 13px/1 Arial,sans-serif;color:{MUTED};">&nbsp; the AI-curated structural-heart front page, updated daily</span>
    </div>
    <div style="padding:18px 0 0;">
      <a href="{SUPPORT_URL}" style="font:600 13px/1 Arial,sans-serif;color:{SEAL};text-decoration:none;">&#9749; Support this briefing &rsaquo;</a>
      <span style="font:400 12px/1 Arial,sans-serif;color:#9a968c;">&nbsp; it keeps the daily curation running</span>
    </div>
    <div style="padding:20px 0 0;font:400 12px/1.5 Arial,sans-serif;color:#9a968c;">
      You are receiving this because you subscribed at kmryo.com. Not medical advice.
      <a href="{{{{ unsubscribe_url }}}}" style="color:#9a968c;">Unsubscribe</a>.
    </div>
  </td></tr>

</table>
</td></tr>
</table>
</body></html>"""

def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    days = load_days()
    year = target_year(arg, days)
    items, ndays = gather(days, year)
    subject, doc = build(items, ndays, year)
    fname = f"{year}.html"
    with open(os.path.join(OUT, fname), "w") as f:
        f.write(doc)
    print(f"SUBJECT: {subject}")
    print(f"WROTE: pulse/yearly/{fname}  ({len(items)} items, {year})")

if __name__ == "__main__":
    main()
