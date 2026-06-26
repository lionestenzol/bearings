"""bearings CLI — `bearings [options]`. Deterministic by default; LLM only if asked."""
import argparse
import datetime
import os
import sys

from . import __version__
from .core import build, date_range
from .ledger import write_ledger
from .render import render_json, render_md
from .sessions import BUILTIN, get_source


def _parse_opts(pairs):
    """--opt k=v --opt a=b  ->  {'k':'v','a':'b'} (passed to the session source)."""
    out = {}
    for p in pairs or []:
        if "=" in p:
            k, v = p.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def build_parser():
    p = argparse.ArgumentParser(
        prog="bearings",
        description="Deterministic 'where am I' digest for a git repo. "
                    "Orientation as a parse, not an LLM call.",
    )
    p.add_argument("--repo", default=os.getcwd(), help="git repo (default: cwd)")
    p.add_argument("--date", default=None, help="local date YYYY-MM-DD (default: today)")
    p.add_argument("--days", type=int, default=1, help="look back N days (default: 1)")
    p.add_argument("--base", default="main", help="branch to compare ahead/behind (default: main)")
    p.add_argument("--source", default="none", choices=sorted(BUILTIN),
                   help="session source adapter (default: none = git-only)")
    p.add_argument("--sessions-root", default=None,
                   help="root dir the session source reads from")
    p.add_argument("--opt", action="append", metavar="K=V",
                   help="extra option for the session source (repeatable)")
    p.add_argument("--namespace-pattern", default=None,
                   help="regex stripped from session namespace labels (claude-code)")
    p.add_argument("--generated", action="append", metavar="MARKER",
                   help="extra path substring to count as generated/vendored (repeatable)")
    p.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    p.add_argument("--ledger", action="store_true", help="also write the durable daily ledger")
    p.add_argument("--ledger-root", default=None, help="override ledger directory")
    p.add_argument("--narrate", action="store_true",
                   help="append an LLM summary (needs --llm-* or BEARINGS_LLM_* env)")
    p.add_argument("--llm-base-url", default=None, help="OpenAI-compatible base URL")
    p.add_argument("--llm-model", default=None, help="model name for narration")
    p.add_argument("--version", action="version", version="bearings " + __version__)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)

    end = (datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
           if args.date else datetime.date.today())
    dates = date_range(end, max(1, args.days))

    src_opts = _parse_opts(args.opt)
    if args.sessions_root:
        src_opts["root"] = args.sessions_root
    if args.namespace_pattern:
        src_opts["namespace_pattern"] = args.namespace_pattern
    try:
        source = get_source(args.source, **src_opts)
    except KeyError as e:
        print(str(e), file=sys.stderr)
        return 2

    report = build(args.repo, dates, source=source, base=args.base,
                   extra_generated=tuple(args.generated or ()))

    if args.json:
        print(render_json(report))
        return 0

    md = render_md(report)
    print(md)

    if args.narrate:
        from . import narrate as _n
        try:
            summary = _n.narrate(md, base_url=args.llm_base_url, model=args.llm_model)
            print("\n## Narration (%s)\n\n%s"
                  % (args.llm_model or os.environ.get("BEARINGS_LLM_MODEL", "llm"), summary))
        except Exception as e:
            print("\n_narration skipped: %s_" % e, file=sys.stderr)

    if args.ledger:
        path = write_ledger(md, report.repo, dates[-1], root=args.ledger_root)
        print("\n_ledger → %s_" % path, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
