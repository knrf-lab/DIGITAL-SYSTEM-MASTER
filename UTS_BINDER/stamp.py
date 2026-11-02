"""Post-process the printed PDF:
1. Locate @@ID|label@@ anchor tokens -> page numbers (dist/pages.json).
2. Stamp a footer on every page: section tab label + page number.
"""
import json
import re
import sys

import pymupdf

src, out = sys.argv[1], sys.argv[2]
doc = pymupdf.open(src)
pat = re.compile(r"@@([A-Za-z0-9_-]+)\|([^@]*)@@")
pages, labels = {}, {}
for i, page in enumerate(doc):
    for m in pat.finditer(page.get_text()):
        pages.setdefault(m.group(1), i + 1)
        if m.group(2):
            labels.setdefault(i + 1, m.group(2))
json.dump(pages, open("dist/pages.json", "w"), indent=1)

current = ""
for i, page in enumerate(doc):
    n = i + 1
    current = labels.get(n, current)
    w, h = page.rect.width, page.rect.height
    if n > 1:
        page.insert_text((28, h - 16), f"DigSys UTS Binder  ·  {current}", fontsize=7.5, color=(0.35, 0.35, 0.35))
        txt = f"p. {n}"
        tw = pymupdf.get_text_length(txt, fontsize=9, fontname="helv")
        page.insert_text((w - 28 - tw, h - 16), txt, fontsize=9, fontname="helv", color=(0, 0, 0))
doc.save(out, garbage=3, deflate=True)
print(f"pages={len(doc)} anchors={len(pages)}")
