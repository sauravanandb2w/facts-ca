#!/usr/bin/env python3
"""Build polity_article_index.js — every article → Part + title + Hindi hook."""
import json
import re
import string
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "polity_mini_constitution.html"
ORIG = ROOT / "polity_original_text.js"
OUT = ROOT / "polity_article_index.js"

PART_META = {
    "I": ("I", "The Union & its Territory"),
    "II": ("II", "Citizenship"),
    "III": ("III", "Fundamental Rights"),
    "IV": ("IV", "Directive Principles (DPSP)"),
    "IVA": ("IVA", "Fundamental Duties"),
    "V": ("V", "The Union"),
    "VI": ("VI", "The States"),
    "VII": ("VII", "Repealed (Part B States)"),
    "VIII": ("VIII", "Union Territories"),
    "IX": ("IX", "The Panchayats"),
    "IXA": ("IXA", "The Municipalities"),
    "IXB": ("IXB", "Co-operative Societies"),
    "X": ("X", "Scheduled & Tribal Areas"),
    "XI": ("XI", "Union–State Relations"),
    "XII": ("XII", "Finance, Property, Contracts"),
    "XIII": ("XIII", "Trade & Commerce"),
    "XIV": ("XIV", "Services (Union & States)"),
    "XIVA": ("XIVA", "Tribunals"),
    "XV": ("XV", "Elections"),
    "XVI": ("XVI", "Special Provisions (SC/ST/OBC)"),
    "XVII": ("XVII", "Official Language"),
    "XVIII": ("XVIII", "Emergency"),
    "XIX": ("XIX", "Miscellaneous"),
    "XX": ("XX", "Amendment"),
    "XXI": ("XXI", "Temporary & Special Provisions"),
    "XXII": ("XXII", "Short Title, Commencement, Repeals"),
}


def municipal_articles() -> list[str]:
    """243P through 243ZG (74th Amendment block)."""
    arts = []
    for c in string.ascii_uppercase[15:26]:  # P-Z
        arts.append(f"243{c}")
    for c in "ABCDEFG":
        arts.append(f"243Z{c}")
    return arts


def part_ixb_articles() -> list[str]:
    """243ZH through 243ZT."""
    return [f"243Z{c}" for c in string.ascii_uppercase[7:20]]


def ordered_articles() -> list[tuple[str, str]]:
    """Return [(artKey, partId), ...] in Constitution order."""
    seq: list[tuple[str, str]] = []

    def add_range(part: str, lo: int, hi: int, skip=()):
        for n in range(lo, hi + 1):
            if n in skip:
                continue
            seq.append((str(n), part))

    add_range("I", 1, 4)
    add_range("II", 5, 11)
    for n in range(12, 36):
        if n == 31:
            continue
        seq.append((str(n), "III"))
        if n == 21:
            seq.append(("21A", "III"))
    for n in range(36, 52):
        seq.append((str(n), "IV"))
        if n == 39:
            seq.append(("39A", "IV"))
        if n == 43:
            seq.append(("43A", "IV"))
            seq.append(("43B", "IV"))
        if n == 48:
            seq.append(("48A", "IV"))
    seq.append(("51A", "IVA"))
    add_range("V", 52, 151)
    add_range("VI", 152, 237)
    seq.append(("238", "VII"))
    for a in ["239", "239A", "239AA", "240", "241", "242"]:
        seq.append((a, "VIII"))
    seq.append(("243", "IX"))
    for c in string.ascii_uppercase[:15]:  # 243A–243O
        seq.append((f"243{c}", "IX"))
    for a in municipal_articles():
        seq.append((a, "IXA"))
    for a in part_ixb_articles():
        seq.append((a, "IXB"))
    seq.append(("244", "X"))
    seq.append(("244A", "X"))
    add_range("XI", 245, 263)
    for n in range(264, 301):
        seq.append((str(n), "XII"))
        if n == 300:
            seq.append(("300A", "XII"))
    add_range("XIII", 301, 307)
    add_range("XIV", 308, 323)
    seq.append(("323A", "XIVA"))
    seq.append(("323B", "XIVA"))
    for n in range(324, 330):
        seq.append((str(n), "XV"))
    for n in range(330, 343):
        seq.append((str(n), "XVI"))
        if n == 338:
            seq.append(("338A", "XVI"))
            seq.append(("338B", "XVI"))
        if n == 342:
            seq.append(("342A", "XVI"))
    add_range("XVII", 343, 351)
    add_range("XVIII", 352, 360)
    add_range("XIX", 361, 367)
    seq.append(("368", "XX"))
    for n in range(369, 393):
        seq.append((str(n), "XXI"))
    for suf in "ABCDEFGHIJ":
        seq.append((f"371{suf}", "XXI"))
    add_range("XXII", 393, 395)
    # extras often cited
    for a, p in [("134A", "V"), ("139A", "V"), ("246A", "XI"), ("269A", "XII"), ("279A", "XII")]:
        if (a, p) not in seq:
            seq.append((a, p))
    return seq


def load_titles(html: str, orig: str) -> dict[str, str]:
    stars = re.findall(r"\{a:'([^']+)',t:'([^']+)'", html)
    m = {a: t for a, t in stars}
    for match in re.finditer(r'"([^"]+)":\s*\{\s*title:\s*"([^"]+)"', orig):
        m[match.group(1)] = match.group(2)
    return m


HIN_CHUNK = {
    "I": "भाग I — नक्शा: भारत संघ है; नए राज्य; सीमाएँ बदलना; यह 368 संशोधन नहीं।",
    "II": "भाग II — नागरिकता: शुरुआत में कौन नागरिक; पाकिस्तान से आए; विदेशी नागरित्व छोड़ो; संसद कानून बनाए।",
    "III": "भाग III — मूल अधिकार: 12 राज्य · 13 कानून रद्द · 14–18 समानता · 19–22 आज़ादी · 23–24 शोषण · 25–28 धर्म · 29–30 संस्कृति · 32–35 उपचार।",
    "IV": "भाग IV — DPSP 36–51: सरकार की इच्छा-सूची; 37 अदालत नहीं; समाजवादी-गाँधी-उदार अनुच्छेद।",
    "IVA": "भाग IVA — 51A (a)–(k) कर्तव्य: ABCDE FGHIJK।",
    "V": "भाग V — केंद्र महल: 52 मुकुट (राष्ट्रपति)… 74–75 असली सरकार… 79 संसद… 124 SC… 148 CAG नियुक्त · 149 CAG कर्तव्य · 150–151 हिसाब-रिपोर्ट।",
    "VI": "भाग VI — राज्य: 153–162 राज्यपाल · 163–167 सरकार · 168–212 विधानमंडल · 213 अध्यादेश · 214–237 उच्च न्यायालय।",
    "VII": "भाग VII — 238 हटा (पुराने Part-B राज्य)।",
    "VIII": "भाग VIII — 239–242 केंद्र शासित प्रदेश; 239AA दिल्ली।",
    "IX": "भाग IX — 243–243O पंचायत (73वें संशोधन)।",
    "IXA": "भाग IXA — 243P–243ZG नगरपालिका (74वें)।",
    "IXB": "भाग IXB — 243ZH–243ZT सहकारी (97वें)।",
    "X": "भाग X — 244–244A अनुसूचित/आदिवासी क्षेत्र (5वीं/6वीं अनुसूची)।",
    "XI": "भाग XI — 245–263 केंद्र-राज्य: कानून कौन बनाए; प्रशासन; अंतर्राज्य परिषद।",
    "XII": "भाग XII — 264–300A पैसा: वित्त आयोग 280; GST 279A; संपत्ति 300A।",
    "XIII": "भाग XIII — 301–307 व्यापार की आज़ादी।",
    "XIV": "भाग XIV — 308–323 लोक सेवा; UPSC 315; बर्खास्तगी 311।",
    "XIVA": "भाग XIVA — 323A–323B ट्रिब्यूनल।",
    "XV": "भाग XV — 324–329A चुनाव: ECI 324; मताधिकार 326।",
    "XVI": "भाग XVI — 330–342A SC/ST/OBC आरक्षण; आयोग 338–338B।",
    "XVII": "भाग XVII — 343–351 भाषा; 8वीं अनुसूची।",
    "XVIII": "भाग XVIII — 352 राष्ट्रीय · 356 राज्य · 360 वित्तीय आपात।",
    "XIX": "भाग XIX — 361–367 विविध: राष्ट्रपति/राज्यपाल संरक्षण।",
    "XX": "भाग XX — 368 संविधान बदलना।",
    "XXI": "भाग XXI — 369–392 विशेष: 370 इतिहास; 371 श्रृंखला।",
    "XXII": "भाग XXII — 393–395 नाम, शुरूआत, पुराना कानून रद्द।",
}


def hin_hook(part: str, key: str, title: str) -> str:
    t = title[:55] + ("…" if len(title) > 55 else "")
    return f"भाग {PART_META[part][0]} · {key}: {t}"


def main():
    html = HTML.read_text(encoding="utf-8")
    orig = ORIG.read_text(encoding="utf-8")
    titles = load_titles(html, orig)
    seq = ordered_articles()
    index = {}
    by_part: dict[str, list] = {k: [] for k in PART_META}
    seen = set()

    for key, part in seq:
        if key in seen:
            continue
        seen.add(key)
        title = titles.get(key) or titles.get(key.upper()) or f"Constitutional provision (Art. {key})"
        pn, pt = PART_META[part]
        row = {
            "a": key,
            "partId": part,
            "partNum": pn,
            "partTitle": pt,
            "title": title,
            "hin": hin_hook(part, key, title),
        }
        index[key] = row
        by_part[part].append(row)

    walks = []
    for part, (pn, pt) in PART_META.items():
        arts = by_part.get(part, [])
        if not arts:
            continue
        story_parts = [HIN_CHUNK.get(part, f"भाग {pn}")]
        # compact numeric walk for recall
        nums = []
        for r in arts:
            nums.append(r["a"])
        story_parts.append(
            "क्रम याद रखो: " + ", ".join(nums[:40]) + ("…" if len(nums) > 40 else "")
        )
        walks.append(
            {
                "partId": part,
                "partNum": pn,
                "partTitle": pt,
                "story": " ".join(story_parts),
                "articles": [{"a": r["a"], "title": r["title"], "hin": r["hin"]} for r in arts],
            }
        )

    js = (
        "// Auto-generated by scripts/build_polity_article_index.py — do not edit by hand\n"
        "window.POLITY_ART_INDEX = "
        + json.dumps(index, ensure_ascii=False)
        + ";\nwindow.POLITY_PART_WALKS = "
        + json.dumps(walks, ensure_ascii=False)
        + ";\n"
    )
    OUT.write_text(js, encoding="utf-8")
    print(f"Wrote {OUT} — {len(set(r['a'] for r in index.values()))} articles, {len(walks)} parts")


if __name__ == "__main__":
    main()
