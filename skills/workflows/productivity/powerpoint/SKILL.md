---
name: powerpoint
description: "Create, edit, validate, and convert PowerPoint (.pptx) files programmatically inside Linux containers. Builds decks from scratch with pptxgenjs (title slides, bullets, tables, charts, images, reusable masters), edits existing decks with python-pptx (replace placeholder text, add slides from template layouts, set speaker notes), and renders headless PDF and PNG previews with LibreOffice. Use when asked to create a PowerPoint, make slides, generate or edit a .pptx, populate a presentation template, or convert a presentation to PDF."
license: Apache-2.0
---

<!-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# PowerPoint Deck Authoring and Conversion

Build, edit, and render .pptx files with no Office application installed.
Everything runs on plain Linux container images: Node.js for generation,
Python for template surgery, LibreOffice headless for PDF and PNG output.

## Tool selection

| Need | Use | Why |
| ---- | --- | --- |
| New deck from scratch with rich slides (charts, tables, images) | pptxgenjs | Declarative slide spec; native OOXML output |
| Read or modify an existing deck; template placeholder fills | python-pptx | Full object model over slides, shapes, notes |
| Precise low-level control (theme parts, raw relationships) | python-pptx with zipfile and lxml | Every XML part is reachable when the object model stops |
| pptx to PDF; slide thumbnails | LibreOffice headless | Renders fonts and layouts with no GUI |

Rule of thumb: new deck -> pptxgenjs; changing someone else's deck ->
python-pptx; making either viewable -> LibreOffice.

## Install (Linux containers)

Pinned packages only; pick the branch matching the base image. No
curl-pipe-bash, no macOS package managers, no GUI layer beyond what Impress needs.

```bash
# Node 18+ base (e.g. node:20-slim)
npm install pptxgenjs@3.12.0

# Python 3.9+ base (e.g. python:3.12-slim)
pip install --no-cache-dir python-pptx==1.0.2

# Debian/Ubuntu: renderer plus fonts
apt-get update && apt-get install -y --no-install-recommends \
  libreoffice-impress fonts-liberation

# RHEL/UBI minimal base (as root)
microdnf install -y libreoffice-impress liberation-fonts

# Optional: one-shot per-page PDF rasterization
apt-get install -y poppler-utils
```

## Create a deck with pptxgenjs

Coordinates are inches (13.33 x 7.5 is widescreen 16:9), fontSize is points,
and colors are 6-digit hex without `#`. The example produces a five-slide deck.

### Complete example

Save as `build-deck.js`, then run `node build-deck.js`.

```js
const pptxgen = require("pptxgenjs");

const pptx = new pptxgen();
pptx.defineLayout({ name: "WIDE169", width: 13.33, height: 7.5 });
pptx.layout = "WIDE169";

// One master owns recurring furniture: brand bar, footer text, slide number.
pptx.defineSlideMaster({
  title: "BRAND",
  background: { color: "FFFFFF" },
  objects: [
    { rect: { x: 0, y: 7.1, w: "100%", h: 0.4, fill: { color: "76B900" } } },
    {
      text: {
        text: "Platform Status",
        options: { x: 0.4, y: 7.14, w: 6, h: 0.32, fontSize: 10, color: "FFFFFF" },
      },
    },
  ],
  slideNumber: { x: 12.7, y: 7.14, fontSize: 10, color: "FFFFFF" },
});
const slide = () => pptx.addSlide({ masterName: "BRAND" });

// 1) Title slide
slide().addText("Kubernetes Platform Weekly", {
  x: 0.6, y: 2.4, w: 12, h: 1.2, fontSize: 40, bold: true, color: "1A1A1A",
});
slide().addText("Fleet status and capacity plan", {
  x: 0.6, y: 3.6, w: 10, h: 0.8, fontSize: 22, color: "555555",
});

// 2) Bullet content slide
const findings = slide();
findings.addText("Incident summary", { x: 0.5, y: 0.4, w: 12, h: 0.9, fontSize: 28, bold: true });
findings.addText(
  [
    { text: "Three node failures traced to firmware push 2.14", options: { bullet: true, breakLine: true } },
    { text: "Mitigated by rollback to 2.13 within 37 minutes", options: { bullet: true, breakLine: true } },
    { text: "Runbook updated; no measurable customer impact", options: { bullet: true } },
  ],
  { x: 0.6, y: 1.6, w: 12, h: 3.5, fontSize: 20, color: "333333" }
);
findings.addNotes("Timeline: 14:02 alert, 14:11 rollback, 14:39 clean.");

// 3) Table slide
const tbl = slide();
tbl.addText("Node fleet by pool", { x: 0.5, y: 0.4, w: 12, h: 0.9, fontSize: 28, bold: true });
const th = { bold: true, color: "FFFFFF", fill: { color: "333333" } };
tbl.addTable(
  [
    [{ text: "Pool", options: th }, { text: "Nodes", options: th }, { text: "vGPU ready", options: th }],
    ["inference-prod", "412", "91%"],
    ["training-prod", "128", "84%"],
    ["sandbox", "57", "62%"],
  ],
  {
    x: 0.6, y: 1.6, w: 12.1,
    border: { type: "solid", pt: 1, color: "CCCCCC" },
    fontSize: 18, rowH: 0.5, valign: "middle",
  }
);

// 4) Chart slide
const trend = slide();
trend.addText("GPU allocation trend", { x: 0.5, y: 0.4, w: 12, h: 0.9, fontSize: 28, bold: true });
trend.addChart(
  pptx.ChartType.line,
  [
    { name: "allocated", labels: ["W1", "W2", "W3", "W4"], values: [310, 342, 366, 401] },
    { name: "requested", labels: ["W1", "W2", "W3", "W4"], values: [355, 361, 388, 425] },
  ],
  {
    x: 0.6, y: 1.6, w: 11.8, h: 4.8,
    showLegend: true, legendPos: "b",
    catAxisTitle: "week", showCatAxisTitle: true,
    valAxisTitle: "gpu count", showValAxisTitle: true,
  }
);

// 5) Image slide: path reads from disk, data takes "image/png;base64,<b64>"
const img = slide();
img.addText("Capacity heatmap", { x: 0.5, y: 0.4, w: 12, h: 0.9, fontSize: 28, bold: true });
img.addImage({ path: "heatmap.png", x: 2.6, y: 1.6, w: 8.0, h: 4.5 });

// Emit the file
pptx
  .writeFile({ fileName: "status-report.pptx" })
  .then((f) => console.log("wrote " + f))
  .catch((e) => { console.error(e); process.exit(1); });
```

### pptxgenjs gotchas

- Set `pptx.layout` before adding slides; geometry is fixed at add time, and
  elements render in call order (later calls stack on top).
- Give tables an explicit `w` and `colW` or column widths come out
  unpredictable.
- Charts are native OOXML charts, editable later in PowerPoint, not pictures.
- Invalid values usually surface at `writeFile` time; fail the process on the
  promise rejection.
- ESM containers work the same: `import pptxgen from "pptxgenjs";`.

## Edit an existing deck with python-pptx

Typical job: open a branded template, swap `{{TOKEN}}` placeholders, add a
status slide that inherits the template look, set notes, save, verify.

### update-deck.py

Run with `python update-deck.py`.

```python
#!/usr/bin/env python3
import sys
from pptx import Presentation
from pptx.util import Pt

SRC, DST = "template.pptx", "status-report.pptx"
MAPPING = {"{{DATE}}": "2026-09-03", "{{OWNER}}": "Platform Reliability"}

def replace_tokens(frame, mapping):
    for para in frame.paragraphs:
        for run in para.runs:
            for old, new in mapping.items():
                if old in run.text:
                    run.text = run.text.replace(old, new)

prs = Presentation(SRC)
print(f"opened {SRC}: {len(prs.slides)} slides, {len(prs.slide_layouts)} layouts")

# 1) Replace placeholder text in shapes and table cells
for slide in prs.slides:
    for shape in slide.shapes:
        if shape.has_text_frame:
            replace_tokens(shape.text_frame, MAPPING)
        if getattr(shape, "has_table", False):
            for row in shape.table.rows:
                for cell in row.cells:
                    replace_tokens(cell.text_frame, MAPPING)

# 2) Speaker notes on the first slide
prs.slides[0].notes_slide.notes_text_frame.text = (
    "Open with the rollback win, then capacity asks."
)

# 3) Add a slide that inherits the template branding
layout = next(
    (lyt for lyt in prs.slide_layouts if lyt.name == "Title and Content"),
    prs.slide_layouts[-1],
)
new = prs.slides.add_slide(layout)
new.shapes.title.text = "Next steps"
for ph in new.placeholders:
    if ph.placeholder_format.idx == 1:  # body/content placeholder
        tf = ph.text_frame
        tf.text = "Canary the firmware push across pools"
        for line in ("Keep 2.13 pinned in the registry", "Close out runbook actions"):
            tf.add_paragraph().text = line
        for para in tf.paragraphs:
            para.font.size = Pt(20)

prs.save(DST)

# 4) Validate by reopening: slide count and unresolved tokens
check = Presentation(DST)
assert len(check.slides) == len(prs.slides), "slide count mismatch"
stray = [
    sh.text_frame.text
    for s in check.slides
    for sh in s.shapes
    if sh.has_text_frame and "{{" in sh.text_frame.text
]
assert not stray, f"unresolved placeholders: {stray}"
print(f"OK: {len(check.slides)} slides -> {DST}")
sys.exit(0)
```

### Shape iteration cheat sheet

- `shape.shape_type` and `shape.name`: identify shapes; log them first when a
  template misbehaves.
- `shape.left/top/width/height`: EMU integers (914400 per inch); build values
  with `Inches(0.5)`.
- `text_frame.paragraphs[i].runs[j].text`: text lives on runs. Assigning
  `frame.text` replaces the run structure and its formatting.
- Placeholder idx 0 is the title; idx 1 is the body/content placeholder.
- `slide.shapes.add_picture("img.png", Inches(1), Inches(2), width=Inches(4))`
  drops an image onto an existing slide.

## Convert and preview with LibreOffice headless

### pptx to PDF and quick previews

```bash
# pptx -> PDF
soffice --headless --convert-to pdf --outdir out/ status-report.pptx

# First-slide PNG preview
soffice --headless --convert-to png --outdir preview/ status-report.pptx

# Concurrent conversions collide on the profile lock; isolate each run
soffice --headless -env:UserInstallation=file:///tmp/lo-$$ --convert-to pdf \
  --outdir out/ status-report.pptx
```

### PDF to per-page images

The PNG filter emits one page per invocation, so loop per page with the 7.4+
JSON filter-option syntax (count slides with python-pptx):

```bash
pages=$(python -c "from pptx import Presentation; print(len(Presentation('status-report.pptx').slides))")
for i in $(seq 1 "$pages"); do
  soffice --headless \
    --convert-to "png:draw_png_Export:{\"PageRange\":{\"type\":\"string\",\"value\":\"$i\"}}" \
    --outdir "tmp/p$i" out/status-report.pdf
  mv "tmp/p$i/status-report.png" "images/slide-$(printf '%02d' "$i").png"
done
```

With poppler-utils, `pdftoppm -png -r 150 out/status-report.pdf images/slide`
rasterizes the whole deck in one shot (slide-1.png onward).

Fidelity notes:

- Install the deck's fonts before converting, or text reflows into the wrong
  geometry.
- Transitions and some chart styling do not survive; treat the PDF as an
  approximation.

## Slide design basics

- One idea per slide: the title states the takeaway, the body proves it.
- Body text 18pt minimum (prefer 20-24); titles 28-40pt.
- 6x6 rule: at most six bullets of at most six words. Detail goes into
  speaker notes, not onto the slide.
- Contrast over decoration: 4.5:1 minimum text-to-background ratio; verify
  hex pairs instead of eyeballing.
- One master owns logos, footers, and slide numbers; never hand-place
  recurring furniture per slide.
- Tables: about six visible rows is the ceiling; push the rest to notes or an
  appendix slide.
- Keep content inside 0.5in margins of the 13.33 x 7.5in frame.

## Validation checklist

Run before declaring a deck done:

1. Reopen with python-pptx and confirm slide count (script above).
2. Scan reopened text for unresolved `{{TOKEN}}` placeholders.
3. Convert to PDF; a non-zero exit or missing output means broken XML.
4. Rasterize page 1 and look at it; font fallback and off-slide content only
   show up visually.
5. Sanity-check file size; a tiny deck usually lost its images.

## Non-goals

- No desktop Office automation: this skill never drives PowerPoint itself,
  COM, AppleScript, or Keynote. File-format manipulation only.
- No branding invention: applies the masters and layouts already in the
  template; output is a static file, not a collaborative document.
