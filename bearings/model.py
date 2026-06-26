"""Plain data structures shared across the package. No logic, no I/O."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class Commit:
    hash: str
    when: str
    author: str
    subject: str
    ctype: str                       # conventional-commit type (feat/fix/...)
    scope: Optional[str]
    files: List[Tuple[str, int, int, str]] = field(default_factory=list)  # (path, ins, del, category)
    ins: int = 0
    dele: int = 0


@dataclass
class Session:
    """One agent/assistant conversation, normalized across providers.

    Every field is provider-agnostic. Adapters fill what they can; missing
    values stay at their zero defaults rather than guessing.
    """
    id: str
    namespace: str = ""              # project / workspace / repo the session belonged to
    first_prompt: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    edits: int = 0                   # file writes/edits the session made
    commits: int = 0                 # git commits the session made
    human_turns: int = 0
    kind: str = ""                   # classified later: shipped/worked/oriented/talked


@dataclass
class BranchState:
    branch: str = "?"
    ahead: str = "?"
    behind: str = "?"
    dirty: int = 0
    base: str = "main"


@dataclass
class Report:
    repo: str
    dates: List[str]
    commits: List[Commit] = field(default_factory=list)
    branch: BranchState = field(default_factory=BranchState)
    sessions: List[Session] = field(default_factory=list)
    loc: Dict[str, int] = field(default_factory=dict)        # category -> inserted lines
    by_type: Dict[str, int] = field(default_factory=dict)    # commit type -> count
    source_name: str = "none"
