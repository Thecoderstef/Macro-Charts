#!/usr/bin/env python3
"""Build an A4 portrait PDF of every chart, grouped by section.

    python export_pdf.py                    # writes exports/macro-pack.pdf
    python export_pdf.py --landscape        # one chart per landscape page

Layout: a cover page, then each section starts a fresh page with a heading and
stacks charts vertically. Portrait A4 suits the wide chart aspect ratio well —
two per page fills the width without dead space, and the reader gets a
scannable document rather than 25 sparse pages.

Requires reportlab. Add `reportlab>=4.0` to requirements.txt.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import yaml
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdfcanvas

ROOT = Path(__file__).parent
CHARTS = ROOT / "charts"
EXPORTS = ROOT / "exports"
CONFIG = ROOT / "config" / "series.yaml"

# Match the chart house style so the document reads as one piece.
INK = HexColor("#1a1a1a")
MUTED = HexColor("#6b6b6b")
RULE = HexColor("#dcdcdc")

MARGIN_X = 42
MARGIN_TOP = 52
MARGIN_BOTTOM = 46
CHART_GAP = 16
SECTION_HEADER_H = 34

DOC_TITLE = "Macro Monitor"


class Pack:
    """Thin wrapper over a reportlab canvas using a fixed slot grid.

    Charts are saved with matplotlib's tight bounding box, so each PNG has a
    slightly different aspect ratio depending on how much room its end labels
    needed. Flowing them down the page therefore gives ragged, inconsistent
    pages. Instead every page has a fixed number of equal slots, and each chart
    is scaled to fit its slot and centred — so the grid stays regular and only
    the chart width varies, by a few percent, which is invisible.
    """

    def __init__(self, outpath: Path, page_size, per_page: int) -> None:
        self.page_w, self.page_h = page_size
        self.canvas = pdfcanvas.Canvas(str(outpath), pagesize=page_size)
        self.canvas.setTitle(DOC_TITLE)
        self.page_no = 0
        self.per_page = per_page
        self.slot = 0
        self.content_w = self.page_w - 2 * MARGIN_X

        column_h = self.page_h - MARGIN_TOP - SECTION_HEADER_H - MARGIN_BOTTOM
        self.slot_h = (column_h - CHART_GAP * (per_page - 1)) / per_page
        self.column_top = self.page_h - MARGIN_TOP - SECTION_HEADER_H

    # -- page furniture ---------------------------------------------------

    def _footer(self) -> None:
        c = self.canvas
        c.setStrokeColor(RULE)
        c.setLineWidth(0.5)
        c.line(MARGIN_X, MARGIN_BOTTOM - 14, self.page_w - MARGIN_X, MARGIN_BOTTOM - 14)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 7.5)
        c.drawString(MARGIN_X, MARGIN_BOTTOM - 26,
                     "Source: FRED, Federal Reserve Bank of St. Louis")
        c.drawRightString(self.page_w - MARGIN_X, MARGIN_BOTTOM - 26, str(self.page_no))

    def new_page(self, section_name: str, continued: bool = False) -> None:
        if self.page_no > 0:
            self._footer()
            self.canvas.showPage()
        self.page_no += 1
        self.slot = 0
        self._section_header(section_name, continued)

    def cover(self) -> None:
        c = self.canvas
        mid = self.page_h / 2
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 30)
        c.drawString(MARGIN_X, mid + 40, DOC_TITLE)

        c.setFillColor(MUTED)
        c.setFont("Helvetica", 14)
        c.drawString(MARGIN_X, mid + 14, date.today().strftime("%B %Y"))

        c.setStrokeColor(RULE)
        c.setLineWidth(1)
        c.line(MARGIN_X, mid - 2, self.page_w - MARGIN_X, mid - 2)

        c.setFillColor(MUTED)
        c.setFont("Helvetica", 9)
        c.drawString(MARGIN_X, mid - 24, "United States  -  Switzerland  -  Euro area")
        c.setFont("Helvetica", 8)
        c.drawString(MARGIN_X, MARGIN_BOTTOM,
                     "Charts rebuilt automatically from the FRED API. "
                     "Underlying data in data/ as CSV.")
        c.showPage()

    def _section_header(self, name: str, continued: bool) -> None:
        # Strip the "1. " prefix that orders sections in the README.
        label = name.split(". ", 1)[-1] if ". " in name[:4] else name
        if continued:
            label += " (continued)"
        c = self.canvas
        top = self.page_h - MARGIN_TOP
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(MARGIN_X, top - 12, label)
        c.setStrokeColor(RULE)
        c.setLineWidth(0.8)
        c.line(MARGIN_X, top - 20, self.page_w - MARGIN_X, top - 20)

    # -- content ----------------------------------------------------------

    def add_chart(self, png: Path, section_name: str) -> None:
        if self.slot >= self.per_page:
            self.new_page(section_name, continued=True)

        px_w, px_h = ImageReader(str(png)).getSize()
        aspect = px_h / px_w

        # Fit to width unless that would overflow the slot, then fit to height.
        width = self.content_w
        height = width * aspect
        if height > self.slot_h:
            height = self.slot_h
            width = height / aspect

        slot_top = self.column_top - self.slot * (self.slot_h + CHART_GAP)
        x = MARGIN_X + (self.content_w - width) / 2          # centre horizontally
        y = slot_top - self.slot_h + (self.slot_h - height) / 2  # centre in slot

        self.canvas.drawImage(ImageReader(str(png)), x, y,
                              width=width, height=height, mask="auto")
        self.slot += 1

    def save(self) -> None:
        self._footer()
        self.canvas.save()


def build_pdf(outpath: Path | None = None, use_landscape: bool = False) -> Path:
    outpath = outpath or (EXPORTS / "macro-pack.pdf")
    outpath.parent.mkdir(parents=True, exist_ok=True)

    config = yaml.safe_load(CONFIG.read_text())

    # Group by section, preserving config order — same logic as the README.
    sections: dict[str, list[dict]] = {}
    for spec in config["charts"]:
        sections.setdefault(spec.get("section", "Charts"), []).append(spec)

    page_size = landscape(A4) if use_landscape else A4
    pack = Pack(outpath, page_size, per_page=1 if use_landscape else 2)
    pack.cover()

    added, missing = 0, []
    for section_name, specs in sections.items():
        available, absent = [], []
        for spec in specs:
            (available if (CHARTS / f"{spec['id']}.png").exists() else absent).append(spec)
        missing += [s["id"] for s in absent]
        if not available:
            continue
        pack.new_page(section_name)
        for spec in available:
            pack.add_chart(CHARTS / f"{spec['id']}.png", section_name)
            added += 1

    pack.save()

    if missing:
        print(f"  skipped, no PNG yet: {', '.join(missing)}")
    print(f"{added} chart(s) across {pack.page_no} page(s) -> {outpath}")
    return outpath


if __name__ == "__main__":
    build_pdf(use_landscape="--landscape" in sys.argv)
