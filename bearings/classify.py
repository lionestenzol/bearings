"""Deterministic classifiers — the honest LOC split, commit typing, session kind.

All pure functions. The default rule-sets are overridable so the tool isn't
opinionated about one stack: pass extra markers/extensions to tune for your repo.
"""
import os
import re
from typing import Optional, Sequence

# --- LOC category: real product code vs generated/vendored bloat ------------
DEFAULT_GENERATED_MARKERS = (
    "node_modules/", "/dist/", "/build/", ".min.js", ".min.css",
    "vendor/", "vendored", "cytoscape", "package-lock.json", "yarn.lock",
    "pnpm-lock.yaml", "poetry.lock", "cargo.lock", "go.sum", ".lock",
    "/__snapshots__/", ".snap", "/generated/", ".pb.go", "_pb2.py",
    "/migrations/", ".bundle.js",
)
DOC_EXTS = (".md", ".mdx", ".rst", ".txt", ".adoc")
DATA_EXTS = (".json", ".yaml", ".yml", ".csv", ".html", ".xml", ".toml", ".ini")
PRODUCT_EXTS = (".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".go",
                ".rs", ".java", ".kt", ".rb", ".php", ".c", ".cc", ".cpp",
                ".h", ".hpp", ".cs", ".swift", ".css", ".scss", ".sh", ".ps1",
                ".sql", ".vue", ".svelte")


def classify_path(path, extra_generated=()):
    # type: (str, Sequence[str]) -> str
    """Return one of: product | docs | data | generated | other."""
    p = path.lower()
    for m in tuple(DEFAULT_GENERATED_MARKERS) + tuple(extra_generated):
        if m in p:
            return "generated"
    _, ext = os.path.splitext(p)
    if ext in DOC_EXTS:
        return "docs"
    if ext in PRODUCT_EXTS:
        return "product"
    if ext in DATA_EXTS:
        return "data"
    return "other"


# --- Conventional commits ----------------------------------------------------
_CC_RE = re.compile(r"^(\w+)(?:\(([^)]+)\))?(!)?:\s*(.*)$")


def classify_commit(subject):
    # type: (str) -> tuple
    """Parse a conventional-commit subject into (type, scope). Falls back to ('other', None)."""
    m = _CC_RE.match(subject.strip())
    if not m:
        return ("other", None)
    return (m.group(1).lower(), m.group(2))


# --- Session intent ----------------------------------------------------------
DEFAULT_ORIENT_HINTS = (
    "where am i", "where are we", "wtf", "idek", "what did we", "what have i",
    "gather my", "bearings", "recap", "what's left", "whats left",
    "catch me up", "remind me", "summarize", "summarise", "what happened",
    "what's the state", "whats the state", "status of", "audit",
)


def is_orientation_prompt(first_prompt, hints=DEFAULT_ORIENT_HINTS):
    # type: (Optional[str], Sequence[str]) -> bool
    if not first_prompt:
        return False
    low = first_prompt.lower()
    return any(h in low for h in hints)


def classify_kind(first_prompt, edits, commits, hints=DEFAULT_ORIENT_HINTS):
    # type: (Optional[str], int, int, Sequence[str]) -> str
    """shipped (committed) | worked (edited, no commit) | oriented (asked 'where am I', produced nothing) | talked."""
    if commits > 0:
        return "shipped"
    if is_orientation_prompt(first_prompt, hints) and edits == 0:
        return "oriented"
    if edits > 0:
        return "worked"
    return "talked"
