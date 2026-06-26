"""The git-only source — no agent transcripts, just version control."""
from .base import SessionSource


class NullSource(SessionSource):
    name = "none"

    def __init__(self, **_opts):
        pass

    def iter_sessions(self, dates):
        return []
