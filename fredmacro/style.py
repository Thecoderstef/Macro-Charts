"""House style.

Charts that "look nice" are mostly the result of five decisions, not talent:

1. Remove the frame. Keep a soft horizontal grid, drop vertical gridlines.
2. Label lines directly at their right-hand end. Legends make the reader's
   eye bounce; direct labels don't.
3. Use a small palette with one clear protagonist colour.
4. Put a real subtitle under the title ("Year-over-year % change") so the
   axis needs no explaining, and a source footer so the chart survives being
   screenshotted into a slide deck.
5. Give it room: generous margins, one idea per chart.

Everything below is just those five ideas written as matplotlib settings.
"""

from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt

# One protagonist (INK/ACCENT) plus muted supporting colours.
PALETTE = [
    "#1f3a5f",  # deep navy   – the main series
    "#c9622a",  # burnt orange – the contrast series
    "#4a8a7b",  # teal
    "#8b6bb1",  # muted purple
    "#a3a3a3",  # grey        – context / background series
]

INK = "#1a1a1a"
MUTED = "#6b6b6b"
GRID = "#dcdcdc"
RECESSION = "#000000"


def apply_style() -> None:
    """Call once before plotting anything."""
    mpl.rcParams.update(
        {
            # Type. DejaVu Sans ships with matplotlib so this works on any
            # machine and inside GitHub Actions. If you want a more distinctive
            # look, install Inter or Source Sans 3 and put it first in this list.
            "font.family": "sans-serif",
            "font.sans-serif": ["Inter", "Source Sans 3", "Helvetica Neue", "DejaVu Sans"],
            "font.size": 11,
            "text.color": INK,
            # Figure
            "figure.figsize": (10, 5.6),
            "figure.dpi": 110,
            "savefig.dpi": 200,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.35,
            # Axes: no box, no vertical grid
            "axes.facecolor": "white",
            "axes.edgecolor": GRID,
            "axes.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": False,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "axes.labelcolor": MUTED,
            "axes.labelsize": 10,
            "axes.titlesize": 15,
            "axes.titleweight": "semibold",
            "axes.titlelocation": "left",
            "axes.prop_cycle": mpl.cycler(color=PALETTE),
            "grid.color": GRID,
            "grid.linewidth": 0.7,
            "grid.alpha": 0.9,
            # Ticks: minimal
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "xtick.major.size": 4,
            "ytick.major.size": 0,
            "xtick.direction": "out",
            # Lines
            "lines.linewidth": 2.0,
            "lines.solid_capstyle": "round",
            "legend.frameon": False,
        }
    )


def add_titles(ax, title: str, subtitle: str | None = None) -> None:
    """Title in bold, subtitle in grey underneath — the newspaper convention."""
    if subtitle:
        ax.set_title(subtitle, loc="left", fontsize=11, color=MUTED,
                     fontweight="normal", pad=10)
        ax.figure.suptitle(title, x=0.005, y=1.0, ha="left",
                           fontsize=15, fontweight="semibold", color=INK)
    else:
        ax.set_title(title, loc="left", pad=12)


def add_footer(ax, source: str, note: str | None = None) -> None:
    text = f"Source: {source}"
    if note:
        text += f"   ·   {note}"
    ax.figure.text(0.005, -0.04, text, ha="left", fontsize=9, color=MUTED)
