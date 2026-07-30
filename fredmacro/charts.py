"""Chart construction: one function that turns a dict of series into a PNG."""

from __future__ import annotations

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from .fred import get_series
from .style import MUTED, PALETTE, RECESSION, add_footer, add_titles

_recession_cache: pd.Series | None = None


def recession_periods(start: str = "1948-01-01") -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """NBER recession dates, as start/end pairs, from FRED series USREC.

    USREC is a monthly 0/1 dummy. We convert runs of 1s into shaded spans.
    """
    global _recession_cache
    if _recession_cache is None:
        _recession_cache = get_series("USREC", start=start)
    flag = _recession_cache
    spans, run_start = [], None
    for date, value in flag.items():
        if value == 1 and run_start is None:
            run_start = date
        elif value == 0 and run_start is not None:
            spans.append((run_start, date))
            run_start = None
    if run_start is not None:
        spans.append((run_start, flag.index[-1]))
    return spans


def _place_end_labels(ax, entries: list[tuple[str, pd.Series, str]]) -> None:
    """Draw the marker + label at the end of each line, nudging labels apart
    vertically when two series finish close together so text never overlaps.
    """
    if not entries:
        return

    ymin, ymax = ax.get_ylim()
    # Minimum vertical gap between label centres, in data units. ~9% of the
    # visible range reads as "two separate rows of text" without excess space.
    min_gap = (ymax - ymin) * 0.09

    items = sorted(
        [
            {"label": label, "x": s.index[-1], "y": s.iloc[-1], "colour": colour}
            for label, s, colour in entries
        ],
        key=lambda d: d["y"],
    )
    # Text is aligned to the right-most series so the labels form a tidy column,
    # but each marker stays on its own line's true final point. This matters when
    # a chart mixes frequencies — a daily series ends weeks after a monthly one.
    x_text = max(item["x"] for item in items)

    for item in items:
        item["y_label"] = item["y"]
    for i in range(1, len(items)):
        floor = items[i - 1]["y_label"] + min_gap
        if items[i]["y_label"] < floor:
            items[i]["y_label"] = floor

    for item in items:
        colour, x_true, y_true = item["colour"], item["x"], item["y"]
        ax.plot([x_true], [y_true], marker="o", markersize=4.5, color=colour, zorder=5)
        ax.annotate(
            f"{item['label']}\n{y_true:,.1f}",
            xy=(x_true, y_true),
            xytext=(x_text, item["y_label"]),
            textcoords="data",
            va="center",
            ha="left",
            fontsize=10,
            color=colour,
            fontweight="semibold",
            linespacing=1.4,
        )


def line_chart(
    series: dict[str, pd.Series],
    title: str,
    subtitle: str | None = None,
    ylabel: str | None = None,
    source: str = "FRED, Federal Reserve Bank of St. Louis",
    note: str | None = None,
    hline: float | None = None,
    hline_label: str | None = None,
    zero_line: bool = False,
    shade_recessions: bool = True,
    ylim: list | tuple | None = None,
    outpath: str | Path | None = None,
):
    """Draw one chart. `series` maps display label -> pandas Series."""
    fig, ax = plt.subplots()

    if shade_recessions:
        earliest = min(s.index[0] for s in series.values())
        for span_start, span_end in recession_periods():
            if span_end >= earliest:
                ax.axvspan(max(span_start, earliest), span_end,
                           color=RECESSION, alpha=0.06, linewidth=0, zorder=0)

    if zero_line:
        ax.axhline(0, color=MUTED, linewidth=1.0, alpha=0.6, zorder=1)

    if hline is not None:
        ax.axhline(hline, color=MUTED, linewidth=1.2, linestyle=(0, (4, 3)), zorder=1)
        if hline_label:
            ax.annotate(hline_label, xy=(0.005, hline), xycoords=("axes fraction", "data"),
                        xytext=(0, 5), textcoords="offset points",
                        fontsize=9, color=MUTED)

    label_entries = []
    for i, (label, s) in enumerate(series.items()):
        colour = PALETTE[i % len(PALETTE)]
        ax.plot(s.index, s.values, color=colour, zorder=3,
                linewidth=1.6 if i == 0 else 1.3)
        label_entries.append((label, s, colour))

    # Leave room on the right for the direct labels.
    ax.margins(x=0.02)
    xmin, xmax = ax.get_xlim()
    ax.set_xlim(xmin, xmax + (xmax - xmin) * 0.16)

    # A manual y-range clips outliers so recent detail stays readable. Matplotlib
    # clips the lines at the axes boundary, so an excluded spike simply runs off
    # the edge — say so in `note:` rather than letting a reader assume the series
    # never went further. Set before labelling, since label spacing is computed
    # from the visible axis range.
    if ylim:
        ax.set_ylim(float(ylim[0]), float(ylim[1]))

    # Labels are placed after xlim/ylim are finalised, so the collision-check
    # math and the x-position of the label both line up with what's drawn.
    _place_end_labels(ax, label_entries)

    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=5, maxticks=9))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    if ylabel:
        ax.set_ylabel(ylabel)

    add_titles(ax, title, subtitle)
    latest = max(s.index[-1] for s in series.values()).strftime("%b %Y")
    add_footer(ax, source, note=f"Latest observation: {latest}"
               + (f" · {note}" if note else ""))

    if outpath:
        outpath = Path(outpath)
        outpath.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(outpath)
        plt.close(fig)
    return fig, ax
