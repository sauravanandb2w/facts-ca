#!/usr/bin/env python3
"""Strip Figma type labels from chart legends; wire event-sequence arrows."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = [ROOT / "un_system_master.html", ROOT / "international_organisations.html", ROOT / "un_environment_architecture.html"]

FIGMA_ACC_RE = re.compile(
    r"\n  <details class=\"hub-acc\" id=\"flowchart-types\">.*?</details>\n\n  <details class=\"hub-acc\" id=\"layer4-index\">",
    re.DOTALL,
)
LEGEND_RE = re.compile(
    r'<div class="afc-legend"><span>Type \d+ · [^<]*</span>\s*',
)
EVENTS_RE = re.compile(
    r'(<div class="afc-events afc-events--seq5">)(.*?)(</div>)',
    re.DOTALL,
)
EVENT_ONE_RE = re.compile(r'<div class="afc-event[^>]*>.*?</div>', re.DOTALL)


def wire_events(inner: str) -> str:
    events = EVENT_ONE_RE.findall(inner)
    if len(events) < 2:
        return inner
    parts: list[str] = []
    for i, ev in enumerate(events):
        if i:
            parts.append('<span class="afc-conn-h" aria-hidden="true"></span>')
        parts.append(ev)
    return "\n      ".join(parts)


def process(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if path.name == "un_system_master.html":
        text = FIGMA_ACC_RE.sub("\n  <details class=\"hub-acc\" id=\"layer4-index\">", text, count=1)
        text = text.replace(
            "Poster diagram = live SVG (Figma-style flow). To use <b>your</b> Figma art:",
            "Interactive organ poster (SVG). Custom art:",
        )
    text = LEGEND_RE.sub('<div class="afc-legend">', text)

    def events_sub(m: re.Match[str]) -> str:
        return m.group(1) + "\n      " + wire_events(m.group(2)) + "\n    " + m.group(3)

    text = EVENTS_RE.sub(events_sub, text)
    path.write_text(text, encoding="utf-8")
    print(f"updated {path.name}")


def main() -> None:
    for p in HTML:
        process(p)


if __name__ == "__main__":
    main()
