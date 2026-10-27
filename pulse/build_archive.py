#!/usr/bin/env python3
"""Rebuild pulse/data/archive.json — the index of published weekly/monthly/yearly issues.

Usage:  python3 pulse/build_archive.py

Scans pulse/weekly/, pulse/monthly/, pulse/yearly/ and, for each HTML issue, records
its id, path, date-range label (from the email masthead) and lead headline (from the
preheader). The homepage's Weekly / Monthly / Yearly tabs read this file.

make_weekly.py / make_monthly.py / make_yearly.py call this automatically after writing
an issue, so the cloud routines only need to `git add pulse/data/archive.json` too.
Only writes archive.json — never touches manifest.json (owned by the daily routine).
"""
import json, os, re, html as _html
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # website/
PULSE = os.path.join(ROOT, "pulse")
OUT = os.path.join(PULSE, "data", "archive.json")

PRE = re.compile(r'<div style="display:none[^"]*">(.*?)</div>', re.S)
LABEL = re.compile(r'float:right[^"]*">([^<]+)</span>')
# "<lead> · plus 19 more from the week"  |  "<lead> · the September 2026 digest, 86 items curated"
MORE = re.compile(r'\s*·\s*(?:plus (\d+) more|.*?(\d+) items).*$', re.S)

def parse(path):
    txt = open(path, encoding="utf-8").read()
    lead, count = "", None
    m = PRE.search(txt)
    if m:
        pre = _html.unescape(m.group(1)).strip()
        mm = MORE.search(pre)
        if mm:
            count = int(mm.group(1)) + 1 if mm.group(1) else int(mm.group(2))
            pre = pre[:mm.start()].strip()
        lead = pre
    lm = LABEL.search(txt)
    label = _html.unescape(lm.group(1)).strip() if lm else ""
    return lead, label, count

def scan(kind):
    d = os.path.join(PULSE, kind)
    out = []
    if not os.path.isdir(d):
        return out
    for fn in sorted(os.listdir(d), reverse=True):
        if not fn.endswith(".html"):
            continue
        lead, label, count = parse(os.path.join(d, fn))
        out.append({"id": fn[:-5], "href": f"pulse/{kind}/{fn}",
                    "label": label, "lead": lead, "count": count})
    return out

def main():
    data = {"updated": date.today().isoformat(),
            "weeks": scan("weekly"), "months": scan("monthly"), "years": scan("yearly")}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"ARCHIVE: {len(data['weeks'])} weeks, {len(data['months'])} months, "
          f"{len(data['years'])} years -> pulse/data/archive.json")

if __name__ == "__main__":
    main()
