"""Pluggable session sources — the agent-agnostic seam.

A SessionSource turns whatever an agent CLI persisted (transcripts, logs, an
API) into normalized `Session` objects. The git core works without any of
these; sources only enrich the digest with "what was happening" context.

Register a new agent in three steps:
  1. subclass `SessionSource`, implement `iter_sessions(dates)`
  2. add it to `BUILTIN`
  3. it's now selectable via `--source <name>`
"""
from typing import Dict, Type

from .base import SessionSource
from .null import NullSource
from .claude_code import ClaudeCodeSource
from .generic_jsonl import GenericJsonlSource

BUILTIN = {
    NullSource.name: NullSource,
    ClaudeCodeSource.name: ClaudeCodeSource,
    GenericJsonlSource.name: GenericJsonlSource,
}  # type: Dict[str, Type[SessionSource]]


def get_source(name, **opts):
    # type: (str, ...) -> SessionSource
    if name not in BUILTIN:
        raise KeyError(
            "unknown session source %r; available: %s"
            % (name, ", ".join(sorted(BUILTIN)))
        )
    return BUILTIN[name](**opts)
