#!/usr/bin/env python3
"""Rebuild every chart defined in config/series.yaml.

    python update.py                  # all charts
    python update.py cpi_inflation    # just one, while you iterate

Outputs:
    charts/<id>.png   the chart
    data/<id>.csv     the exact data behind it, so results are auditable
    README.md         chart gallery + timestamp refreshed in place
"""

from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path

import yaml
from dotenv import load_dotenv

from fredmacro.charts import line_chart
from fredmacro.fred import get_metadata, get_series
from fredmacro.style import apply_style
from fredmacro.transform import TRANSFORMS

ROOT = Path(__file__).parent
CONFIG = ROOT / "config" / "series.yaml"
CHARTS_DIR = ROOT / "charts"
DATA_DIR = ROOT / "data"

START_MARKER = "<!-- CHARTS:START -->"
END_MARKER = "<!-- CHARTS:END -->"


def build_chart(spec: dict, defaults: dict) -> dict:
    """Fetch, transform and plot one chart. Returns a summary for the README."""
    chart_id = spec["id"]
    start = spec.get("start", defaults.get("start", "1995-01-01"))
    default_transform = spec.get("transform", "level")

    lines: dict = {}
    for member in spec["series"]:
        fred_id = member["fred_id"]
        label = member.get("label", fred_id)
        transform_name = member.get("transform", default_transform)

        raw = get_series(fred_id, start=start)
        meta = get_metadata(fred_id)
        transform = TRANSFORMS[transform_name]
        lines[label] = transform(raw, meta["frequency"])

        DATA_DIR.mkdir(exist_ok=True)
        raw.to_csv(DATA_DIR / f"{fred_id}.csv", header=[fred_id])

    outpath = CHARTS_DIR / f"{chart_id}.png"
    line_chart(
        lines,
        title=spec["title"],
        subtitle=spec.get("subtitle"),
        ylabel=spec.get("ylabel"),
        note=spec.get("note"),
        hline=spec.get("hline"),
        hline_label=spec.get("hline_label"),
        zero_line=spec.get("zero_line", False),
        shade_recessions=spec.get("shade_recessions", defaults.get("shade_recessions", True)),
        ylim=spec.get("ylim"),
        outpath=outpath,
    )

    latest_label, latest_series = next(iter(lines.items()))
    return {
        "id": chart_id,
        "section": spec.get("section", "Charts"),
        "title": spec["title"],
        "path": f"charts/{chart_id}.png",
        "latest_date": latest_series.index[-1].strftime("%b %Y"),
        "latest_value": f"{latest_series.iloc[-1]:.1f}",
        "latest_label": latest_label,
    }


def refresh_readme(summaries: list[dict]) -> None:
    """Rewrite the gallery block between the markers, leaving prose untouched.

    Charts are grouped under their `section:` heading. Sections appear in the
    order they first show up in series.yaml, so reordering the config reorders
    the README — no code change needed.
    """
    readme = ROOT / "README.md"
    if not readme.exists():
        return
    text = readme.read_text()
    if START_MARKER not in text or END_MARKER not in text:
        return

    # dict preserves insertion order, which is config order
    sections: dict[str, list[dict]] = {}
    for item in summaries:
        sections.setdefault(item["section"], []).append(item)

    stamp = datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC")
    block = [START_MARKER, f"_Last rebuilt {stamp}._", ""]
    for section_name, items in sections.items():
        block += [f"## {section_name}", ""]
        for item in items:
            block += [
                f"### {item['title']}",
                f"`{item['latest_label']}` — latest **{item['latest_value']}** "
                f"({item['latest_date']})",
                "",
                f"![{item['title']}]({item['path']})",
                "",
            ]
    block.append(END_MARKER)

    head, _, rest = text.partition(START_MARKER)
    _, _, tail = rest.partition(END_MARKER)
    readme.write_text(head + "\n".join(block) + tail)


def main() -> int:
    load_dotenv()
    apply_style()
    CHARTS_DIR.mkdir(exist_ok=True)

    config = yaml.safe_load(CONFIG.read_text())
    defaults = config.get("defaults", {})
    wanted = set(sys.argv[1:])

    summaries, failures = [], []
    for spec in config["charts"]:
        if wanted and spec["id"] not in wanted:
            continue
        try:
            summaries.append(build_chart(spec, defaults))
            print(f"  ok    {spec['id']}")
        except Exception as exc:  # keep going; one dead series shouldn't kill the run
            failures.append((spec["id"], exc))
            print(f"  FAIL  {spec['id']}: {exc}")

    if summaries and not wanted:
        refresh_readme(summaries)

    print(f"\n{len(summaries)} chart(s) written to {CHARTS_DIR}/")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
