"""Renderers: Report -> markdown or JSON. Presentation only."""
import collections
import dataclasses
import json
import os
from typing import List

from .model import Report

_LOC_LABEL = {
    "product": "real product code",
    "docs": "docs",
    "data": "config/data",
    "generated": "generated / vendored bloat",
    "other": "other",
}
_KIND_ICON = {"shipped": "[SHIP]", "worked": "[work]",
              "oriented": "[??->]", "talked": "[talk]"}


def render_md(report, limit=18):
    # type: (Report, int) -> str
    L = []  # type: List[str]
    repo_name = os.path.basename(report.repo.rstrip("/\\")) or report.repo
    span = (report.dates[0] if len(report.dates) == 1
            else "%s..%s" % (report.dates[0], report.dates[-1]))
    L.append("# BEARINGS — %s — %s" % (repo_name, span))
    L.append("")
    bs = report.branch
    L.append("**Branch** `%s` · %s ahead / %s behind %s · %d dirty files"
             % (bs.branch, bs.ahead, bs.behind, bs.base, bs.dirty))
    L.append("")

    # Commits by category
    L.append("## Commits (%d)" % len(report.commits))
    if report.by_type:
        order = ["feat", "fix", "refactor", "test", "docs", "chore", "perf", "ci", "other"]
        chips = ["%s %d" % (t, report.by_type[t]) for t in order if report.by_type.get(t)]
        chips += ["%s %d" % (t, n) for t, n in report.by_type.items() if t not in order]
        L.append("  ·  ".join(chips))
    L.append("")
    for c in report.commits:
        scope = "(%s)" % c.scope if c.scope else ""
        L.append("- `%s` **%s%s** +%d/-%d — %s"
                 % (c.hash, c.ctype, scope, c.ins, c.dele, c.subject))
    L.append("")

    # Honest LOC split
    total = sum(report.loc.values()) or 1
    L.append("## LOC inserted — honest split")
    for cat in ("product", "docs", "data", "generated", "other"):
        v = report.loc.get(cat)
        if v:
            L.append("- **%s**: %s (%d%%)" % (_LOC_LABEL[cat], "{:,}".format(v), v * 100 // total))
    L.append("- _total inserted: %s_" % "{:,}".format(total))
    L.append("")

    # Sessions (only if a source provided any)
    if report.sessions:
        kinds = collections.Counter(s.kind for s in report.sessions)
        tin = sum(s.input_tokens for s in report.sessions)
        tout = sum(s.output_tokens for s in report.sessions)
        L.append("## Sessions (%d via %s)" % (len(report.sessions), report.source_name))
        L.append("shipped %d · worked %d · oriented %d · talked %d"
                 % (kinds.get("shipped", 0), kinds.get("worked", 0),
                    kinds.get("oriented", 0), kinds.get("talked", 0)))
        if tin:
            L.append("tokens: %.1fM in / %.0fk out (%.2f%% ratio)"
                     % (tin / 1e6, tout / 1e3, tout / tin * 100))
        L.append("")
        for s in report.sessions[:limit]:
            L.append("- %s `%s` %s · %.1fM · e%d/c%d · %s"
                     % (_KIND_ICON.get(s.kind, "·"), s.id, s.namespace,
                        s.input_tokens / 1e6, s.edits, s.commits,
                        s.first_prompt or "(none)"))
        if len(report.sessions) > limit:
            L.append("- _… %d more_" % (len(report.sessions) - limit))
        L.append("")

        # Orientation tax — the load-bearing number
        orient_in = sum(s.input_tokens for s in report.sessions if s.kind == "oriented")
        if tin and orient_in:
            L.append("## Orientation tax")
            L.append("**%.1fM tokens (%d%%)** spent on 'where am I' sessions that "
                     "produced no commits. This is what bearings makes free."
                     % (orient_in / 1e6, orient_in * 100 // tin))
            L.append("")

    # Loop state — open festivals, newest mastery capsule, unproven DoD (zero-LLM)
    lp = report.loop
    if lp is not None:
        L.append("## Loop state")
        L.append("**%d open festivals** · **%d unproven DoD** (unchecked `- [ ]`)"
                 % (len(lp.open_festivals), lp.unproven_dod))
        if lp.newest_capsule:
            L.append("newest capsule: `%s`" % lp.newest_capsule)
        else:
            L.append("newest capsule: _none found_")
        for fest in lp.open_festivals:
            L.append("- %s" % fest)
        L.append("")
    return "\n".join(L)


def render_json(report):
    # type: (Report) -> str
    return json.dumps(dataclasses.asdict(report), indent=2, default=str)
