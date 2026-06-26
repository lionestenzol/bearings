"""bearings — deterministic, model-agnostic orientation digest for git repos.

Answers "what did I do / where am I" by a pure PARSE of git history (always-on
core) plus optional, pluggable agent-session adapters. No LLM is required; an
optional, provider-agnostic narration layer can summarize on top of any
OpenAI-compatible endpoint.
"""

__version__ = "0.1.0"

from .model import Report, Commit, Session  # noqa: F401
from .core import build  # noqa: F401
