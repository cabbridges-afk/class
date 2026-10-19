#!/usr/bin/env python3
"""Build a standalone HTML visualization from the generated annotation files."""

from __future__ import annotations

import html
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(
    "/Users/charlottebridges/Library/Mobile Documents/"
    "com~apple~CloudDocs/Desktop/corps"
)
FILES = ("P2-26sp", "P3-26sp", "P4-26sp")
FIELDS = (
    "Business judgment rule rebutted",
    "Potential duty involved",
    "DGCL § 102(b)(7) limited director liability",
)


def annotation_blocks(markdown: str) -> list[str]:
    return re.findall(
        r"> \*\*Corporate-law annotation.*?"
        r"(?=\n> \*\*Corporate-law annotation|\n--- Source PDF page|\Z)",
        markdown,
        re.DOTALL,
    )


def value(block: str, field: str) -> str:
    matched = re.search(rf"> - \*\*{re.escape(field)}:\*\* (.*)", block)
    return matched.group(1).strip() if matched else "unknown"


def source_metrics() -> dict[str, object]:
    documents: dict[str, object] = {}
    for stem in FILES:
        content = (ROOT / f"{stem}.annotated.md").read_text(encoding="utf-8")
        blocks = annotation_blocks(content)
        manual_end = content.find("\n---\n\n")
        manual = content[:manual_end] if manual_end >= 0 else ""
        documents[stem] = {
            "total": len(blocks),
            "inline": len(annotation_blocks(content[manual_end:])) if manual_end >= 0 else len(blocks),
            "manual": len(annotation_blocks(manual)),
            "counts": {
                field: dict(Counter(value(block, field) for block in blocks))
                for field in FIELDS
            },
        }
    return documents


def main() -> None:
    data = source_metrics()
    payload = json.dumps(data, ensure_ascii=False)
    output = ROOT / "corporate-law-annotation-dashboard.html"
    output.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Corporate-Law Annotation Dashboard</title>
  <style>
    :root {{
      --ink: #1f2937; --muted: #5b6474; --paper: #f8fafc; --card: #ffffff;
      --border: #d9e0ea; --accent: #285a90; --warning: #9a3412;
      --care: #6d4c8f; --loyalty: #1d7484; --both: #c06c25; --neither: #708090;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: var(--paper); color: var(--ink); font: 16px/1.5 system-ui, sans-serif; }}
    main {{ max-width: 1200px; padding: 42px 24px 64px; margin: auto; }}
    h1 {{ font-size: clamp(1.9rem, 4vw, 3rem); line-height: 1.1; margin: 0 0 8px; }}
    h2 {{ margin: 0 0 16px; font-size: 1.2rem; }}
    .subtitle, .note {{ color: var(--muted); margin: 0 0 24px; }}
    .warning {{ border-left: 5px solid var(--warning); background: #fff7ed; padding: 16px 18px; margin: 28px 0; }}
    .cards {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 28px 0; }}
    .card, .chart {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px #1720330a; }}
    .number {{ display: block; font-size: 2.1rem; font-weight: 750; line-height: 1.05; margin-bottom: 5px; }}
    .label {{ color: var(--muted); font-size: .9rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
    .chart {{ min-height: 290px; }}
    .bar-row {{ display: grid; grid-template-columns: 120px 1fr 30px; gap: 8px; align-items: center; margin: 11px 0; font-size: .88rem; }}
    .bar-track {{ height: 18px; background: #eaf0f6; border-radius: 99px; overflow: hidden; }}
    .bar {{ height: 100%; min-width: 2px; border-radius: inherit; background: var(--accent); }}
    .bar.care {{ background: var(--care); }} .bar.loyalty {{ background: var(--loyalty); }}
    .bar.both {{ background: var(--both); }} .bar.neither {{ background: var(--neither); }}
    .bar.yes {{ background: #26734d; }} .bar.no {{ background: #a34738; }}
    .bar.unclear {{ background: #c38523; }} .bar.not-addressed {{ background: #5b6b7a; }}
    .bar.not-applicable {{ background: #6680a0; }}
    footer {{ color: var(--muted); font-size: .85rem; margin-top: 30px; }}
    @media (max-width: 780px) {{ .cards, .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
<main>
  <h1>Corporate-Law Annotation Dashboard</h1>
  <p class="subtitle">Counts from automated annotations of P2, P3, and P4.</p>
  <aside class="warning"><strong>Provisional data only.</strong> The annotation audit found duplicate case labels, 66 labels that could not be placed inline, and incomplete rotated-text extraction in P3. These charts visualize model output; they do not establish legal conclusions.</aside>
  <section class="cards" id="summary"></section>
  <section class="grid">
    <article class="chart"><h2>Potential duty involved</h2><div id="duty"></div></article>
    <article class="chart"><h2>Business judgment rule rebutted</h2><div id="bjr"></div></article>
    <article class="chart"><h2>DGCL § 102(b)(7) limitation</h2><div id="exculpation"></div></article>
  </section>
  <footer>Generated from <code>P2-26sp.annotated.md</code>, <code>P3-26sp.annotated.md</code>, and <code>P4-26sp.annotated.md</code>. Open this file locally in any browser.</footer>
</main>
<script>
const documents = {payload};
const fields = {{
  duty: 'Potential duty involved',
  bjr: 'Business judgment rule rebutted',
  exculpation: 'DGCL § 102(b)(7) limited director liability'
}};
const label = s => s.replaceAll('-', ' ').replace(/\\b\\w/g, c => c.toUpperCase());
const css = s => s.toLowerCase().replaceAll(' ', '-');
const all = Object.values(documents);
document.querySelector('#summary').innerHTML = Object.entries(documents).map(([name, doc]) =>
  `<article class="card"><span class="number">${{doc.total}}</span><strong>${{name}}</strong><div class="label">${{doc.inline}} placed inline · ${{doc.manual}} need placement</div></article>`
).join('');
for (const [target, field] of Object.entries(fields)) {{
  const categories = [...new Set(all.flatMap(doc => Object.keys(doc.counts[field])))];
  const maximum = Math.max(...categories.map(category => Math.max(...all.map(doc => doc.counts[field][category] || 0))), 1);
  document.querySelector(`#${{target}}`).innerHTML = categories.map(category => {{
    const parts = Object.entries(documents).map(([name, doc]) => `${{name}}: ${{doc.counts[field][category] || 0}}`).join(' · ');
    const value = all.reduce((sum, doc) => sum + (doc.counts[field][category] || 0), 0);
    return `<div class="bar-row" title="${{parts}}"><span>${{label(category)}}</span><div class="bar-track"><div class="bar ${{css(category)}}" style="width:${{100 * value / (maximum * all.length)}}%"></div></div><strong>${{value}}</strong></div>`;
  }}).join('');
}}
</script>
</body>
</html>""",
        encoding="utf-8",
    )
    print(output)


if __name__ == "__main__":
    main()
