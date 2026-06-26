"""Durable daily ledger — so the next session reads orientation instead of rebuilding it."""
import os
import re


def default_ledger_root():
    env = os.environ.get("BEARINGS_LEDGER_ROOT")
    if env:
        return os.path.expanduser(env)
    return os.path.join(os.path.expanduser("~"), ".bearings", "ledger")


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "repo"


def write_ledger(text, repo, date, root=None):
    # type: (str, str, str, str) -> str
    root = root or default_ledger_root()
    d = os.path.join(root, slug(os.path.basename(repo.rstrip("/\\"))))
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, date + ".md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text.rstrip() + "\n")
    return path
