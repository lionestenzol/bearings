"""SessionSource interface — implement this to teach bearings a new agent."""
from abc import ABC, abstractmethod
from typing import Iterable, Set

from ..model import Session


class SessionSource(ABC):
    #: short, CLI-selectable name, e.g. "claude-code"
    name = "base"

    @abstractmethod
    def iter_sessions(self, dates):
        # type: (Set[str]) -> Iterable[Session]
        """Yield one normalized Session per conversation active on any of `dates`
        (each a 'YYYY-MM-DD' string in local time). Return nothing if the source
        is unavailable — never raise to keep the git core working."""
        raise NotImplementedError
