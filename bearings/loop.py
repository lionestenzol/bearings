"""Loop state as a pure file parse: open festivals, newest mastery capsule, and
unproven DoD checkboxes. No LLM, no network -- bearings' whole value. Reads only
the local filesystem, mirroring core.py's subprocess/file-read discipline."""
import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# Where active festivals live under a festival-project root, and the capsule glob.
_ACTIVE_REL = ("festivals", "active")
_CAPSULE_PREFIX = "MASTERY_CAPSULE_"
_CAPSULE_SUFFIX = ".md"
_UNCHECKED = "- [ ]"

# Heavyweight / vendored dirs to skip while walking -- keeps the parse fast over big
# trees (a festival-project can vendor node_modules, .git, build output). Pruning these
# is what stops the walk from taking seconds; bearings must stay snappy.
_SKIP_DIRS = frozenset({
    ".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
    ".next", "target", ".cache", ".mypy_cache", ".pytest_cache", "vendor",
})


def _prune(dirs):
    # type: (List[str]) -> None
    """In-place os.walk prune: drop skip-dirs so the walk never descends into them."""
    dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]


@dataclass(frozen=True)
class LoopState:
    """Frozen snapshot of where the loop stands. Pure-parse, immutable."""
    open_festivals: Tuple[str, ...] = ()                 # active festival dir names, sorted
    newest_capsule: Optional[str] = None                 # filename of newest MASTERY_CAPSULE_*.md
    newest_capsule_mtime: Optional[float] = None         # its mtime (epoch seconds)
    unproven_dod: int = 0                                # unchecked "- [ ]" lines across active tasks
    roots: Tuple[str, ...] = ()                          # absolute loop roots scanned


def _read_lines(path):
    # type: (str) -> List[str]
    """UTF-8 file read that never raises -- a bad file must not sink the parse."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read().splitlines()
    except Exception:
        return []


def _open_festivals(root):
    # type: (str) -> List[str]
    """Immediate sub-directories of <root>/festivals/active (each an open festival)."""
    active = os.path.join(root, *_ACTIVE_REL)
    try:
        entries = os.listdir(active)
    except Exception:
        return []
    fests = [e for e in entries if os.path.isdir(os.path.join(active, e))]
    return sorted(fests)


def _newest_capsule(root):
    # type: (str) -> Tuple[Optional[str], Optional[float]]
    """Newest MASTERY_CAPSULE_*.md found anywhere under root (name, mtime)."""
    best_name = None  # type: Optional[str]
    best_mtime = None  # type: Optional[float]
    for dirpath, dirs, files in os.walk(root):
        _prune(dirs)
        for name in files:
            if name.startswith(_CAPSULE_PREFIX) and name.endswith(_CAPSULE_SUFFIX):
                try:
                    mtime = os.path.getmtime(os.path.join(dirpath, name))
                except Exception:
                    continue
                if best_mtime is None or mtime > best_mtime:
                    best_name, best_mtime = name, mtime
    return best_name, best_mtime


def _unproven_dod(root):
    # type: (str) -> int
    """Count unchecked '- [ ]' lines across active festival task .md files."""
    active = os.path.join(root, *_ACTIVE_REL)
    count = 0
    for dirpath, dirs, files in os.walk(active):
        _prune(dirs)
        for name in files:
            if not name.endswith(".md"):
                continue
            for line in _read_lines(os.path.join(dirpath, name)):
                if line.lstrip().startswith(_UNCHECKED):
                    count += 1
    return count


def build_loop_state(loop_roots):
    # type: (object) -> LoopState
    """Assemble a LoopState from one or more festival-project roots. Pure parse.

    Accepts a single path string or an iterable of paths. Missing/unreadable
    roots contribute nothing rather than raising -- the digest stays robust.
    """
    if isinstance(loop_roots, str):
        roots = [loop_roots]
    else:
        roots = [r for r in (loop_roots or []) if r]
    roots = [os.path.abspath(r) for r in roots]

    open_fests = []  # type: List[str]
    unproven = 0
    newest_name = None  # type: Optional[str]
    newest_mtime = None  # type: Optional[float]
    for root in roots:
        open_fests.extend(_open_festivals(root))
        unproven += _unproven_dod(root)
        name, mtime = _newest_capsule(root)
        if name is not None and (newest_mtime is None or
                                 (mtime is not None and mtime > newest_mtime)):
            newest_name, newest_mtime = name, mtime

    return LoopState(
        open_festivals=tuple(sorted(open_fests)),
        newest_capsule=newest_name,
        newest_capsule_mtime=newest_mtime,
        unproven_dod=unproven,
        roots=tuple(roots),
    )
