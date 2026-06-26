"""Claude Code transcript adapter.

Reads ~/.claude/projects/<namespace>/<uuid>.jsonl. Each line is a JSON event
with type=user|assistant, message.{role,content,usage}, timestamp, isMeta. This
is one concrete adapter; the GenericJsonlSource covers OpenAI-style logs, and any
other agent is a ~40-line subclass.
"""
import datetime
import glob
import json
import os
import re
from typing import Iterable, Optional, Set

from .base import SessionSource
from ..model import Session


def _text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            b.get("text", "") for b in content
            if isinstance(b, dict) and b.get("type") == "text"
        )
    return ""


class ClaudeCodeSource(SessionSource):
    name = "claude-code"

    def __init__(self, root=None, namespace_pattern=None, **_opts):
        # root defaults to the standard Claude Code projects dir
        self.root = root or os.path.join(
            os.path.expanduser("~"), ".claude", "projects"
        )
        # optional regex to prettify the raw dir name (e.g. drop a path prefix)
        self.namespace_pattern = (
            re.compile(namespace_pattern) if namespace_pattern else None
        )

    def _namespace(self, dirname):
        if self.namespace_pattern:
            return self.namespace_pattern.sub("", dirname) or dirname
        return dirname

    def iter_sessions(self, dates):
        # type: (Set[str]) -> Iterable[Session]
        if not os.path.isdir(self.root):
            return
        for f in glob.glob(os.path.join(self.root, "*", "*.jsonl")):
            try:
                mt = datetime.datetime.fromtimestamp(os.path.getmtime(f))
            except OSError:
                continue
            if mt.strftime("%Y-%m-%d") not in dates:
                continue
            s = self._parse_file(f)
            if s is not None:
                yield s

    def _parse_file(self, path):
        # type: (str) -> Optional[Session]
        ns = self._namespace(os.path.basename(os.path.dirname(path)))
        conv = os.path.basename(path)[:8]
        first_prompt = None
        intok = outtok = edits = commits = human = 0
        try:
            fh = open(path, encoding="utf-8", errors="replace")
        except OSError:
            return None
        with fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                msg = o.get("message") or {}
                t = o.get("type")
                if t == "user" and msg.get("role") == "user" and not o.get("isMeta"):
                    c = msg.get("content")
                    is_tr = isinstance(c, list) and any(
                        isinstance(b, dict) and b.get("type") == "tool_result"
                        for b in c
                    )
                    if not is_tr:
                        human += 1
                        if first_prompt is None:
                            txt = re.sub(r"<[^>]+>", " ", _text_of(c))
                            txt = " ".join(txt.split())
                            if txt:
                                first_prompt = txt[:140]
                elif t == "assistant" and msg.get("role") == "assistant":
                    c = msg.get("content")
                    if isinstance(c, list):
                        for b in c:
                            if isinstance(b, dict) and b.get("type") == "tool_use":
                                nm = b.get("name", "")
                                if nm in ("Write", "Edit", "NotebookEdit"):
                                    edits += 1
                                elif nm == "Bash":
                                    cmd = str((b.get("input") or {}).get("command", ""))
                                    if re.search(r"git\s+commit", cmd):
                                        commits += 1
                    u = msg.get("usage") or {}
                    intok += (u.get("input_tokens", 0)
                              + u.get("cache_read_input_tokens", 0)
                              + u.get("cache_creation_input_tokens", 0))
                    outtok += u.get("output_tokens", 0)
        return Session(
            id=conv, namespace=ns, first_prompt=first_prompt,
            input_tokens=intok, output_tokens=outtok,
            edits=edits, commits=commits, human_turns=human,
        )
