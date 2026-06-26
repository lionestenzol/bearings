"""The always-on core: git history → a normalized Report. No LLM, no network."""
import collections
import datetime
import os
import subprocess
from typing import List, Sequence

from .classify import classify_commit, classify_kind, classify_path
from .model import BranchState, Commit, Report
from .sessions.base import SessionSource
from .sessions.null import NullSource


def _git(repo, *args):
    try:
        out = subprocess.run(
            ["git", "-C", repo, *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        return out.stdout
    except Exception:
        return ""


def git_commits(repo, since, until, extra_generated=()):
    # type: (str, str, str, Sequence[str]) -> List[Commit]
    fmt = "@@C@@%h|%ai|%an|%s"
    raw = _git(repo, "log", "--since=%s" % since, "--until=%s" % until,
               "--numstat", "--pretty=format:%s" % fmt, "--no-merges")
    commits = []
    cur = None
    for line in raw.splitlines():
        if line.startswith("@@C@@"):
            if cur:
                commits.append(cur)
            h, ai, an, subj = line[len("@@C@@"):].split("|", 3)
            ctype, scope = classify_commit(subj)
            cur = Commit(hash=h, when=ai, author=an, subject=subj,
                         ctype=ctype, scope=scope)
        elif line.strip() and cur is not None:
            parts = line.split("\t")
            if len(parts) == 3:
                a, d, path = parts
                ins = int(a) if a.isdigit() else 0
                dele = int(d) if d.isdigit() else 0
                cur.files.append((path, ins, dele, classify_path(path, extra_generated)))
                cur.ins += ins
                cur.dele += dele
    if cur:
        commits.append(cur)
    return commits


def branch_state(repo, base="main"):
    # type: (str, str) -> BranchState
    head = _git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip() or "?"
    ahead = _git(repo, "rev-list", "--count", "%s..HEAD" % base).strip() or "?"
    behind = _git(repo, "rev-list", "--count", "HEAD..%s" % base).strip() or "?"
    dirty = len([l for l in _git(repo, "status", "--porcelain").splitlines() if l.strip()])
    return BranchState(branch=head, ahead=ahead, behind=behind, dirty=dirty, base=base)


def date_range(end_date, days):
    # type: (datetime.date, int) -> List[str]
    return [(end_date - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(days)][::-1]


def build(repo, dates, source=None, base="main", extra_generated=()):
    # type: (str, List[str], SessionSource, str, Sequence[str]) -> Report
    """Assemble a Report from git (+ optional session source). Pure parse."""
    repo = os.path.abspath(repo)
    source = source or NullSource()
    since = min(dates) + " 00:00:00"
    until = (datetime.datetime.strptime(max(dates), "%Y-%m-%d")
             + datetime.timedelta(days=1)).strftime("%Y-%m-%d") + " 00:00:00"

    commits = git_commits(repo, since, until, extra_generated)
    bs = branch_state(repo, base)

    try:
        sessions = list(source.iter_sessions(set(dates)))
    except Exception:
        sessions = []  # a broken adapter must never sink the git core
    for s in sessions:
        s.kind = classify_kind(s.first_prompt, s.edits, s.commits)
    sessions.sort(key=lambda s: -s.input_tokens)

    loc = collections.Counter()
    by_type = collections.Counter()
    for c in commits:
        by_type[c.ctype] += 1
        for _path, ins, _d, cat in c.files:
            loc[cat] += ins

    return Report(repo=repo, dates=list(dates), commits=commits, branch=bs,
                  sessions=sessions, loc=dict(loc), by_type=dict(by_type),
                  source_name=getattr(source, "name", "none"))
