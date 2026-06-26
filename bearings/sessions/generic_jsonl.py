"""Generic JSONL chat-log adapter — config-driven, provider-neutral.

Point it at any directory of .jsonl files where each line is a chat message in
roughly the OpenAI shape ({"role": "...", "content": "...", "usage": {...}}).
Field names are configurable so it fits other agent CLIs without code changes.

Example (Codex/OpenAI-style logs):
  bearings --source generic-jsonl \
           --sessions-root ~/.codex/sessions \
           --opt role_field=role --opt content_field=content
"""
import datetime
import glob
import json
import os
from typing import Iterable, Optional, Set

from .base import SessionSource
from ..model import Session


class GenericJsonlSource(SessionSource):
    name = "generic-jsonl"

    def __init__(self, root=None, role_field="role", content_field="content",
                 user_role="user", assistant_role="assistant",
                 usage_field="usage", input_field="prompt_tokens",
                 output_field="completion_tokens", **_opts):
        self.root = os.path.expanduser(root) if root else None
        self.role_field = role_field
        self.content_field = content_field
        self.user_role = user_role
        self.assistant_role = assistant_role
        self.usage_field = usage_field
        self.input_field = input_field
        self.output_field = output_field

    def iter_sessions(self, dates):
        # type: (Set[str]) -> Iterable[Session]
        if not self.root or not os.path.isdir(self.root):
            return
        for f in glob.glob(os.path.join(self.root, "**", "*.jsonl"), recursive=True):
            try:
                mt = datetime.datetime.fromtimestamp(os.path.getmtime(f))
            except OSError:
                continue
            if mt.strftime("%Y-%m-%d") not in dates:
                continue
            s = self._parse_file(f)
            if s is not None:
                yield s

    @staticmethod
    def _as_text(content):
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for b in content:
                if isinstance(b, dict):
                    parts.append(b.get("text") or b.get("content") or "")
                elif isinstance(b, str):
                    parts.append(b)
            return " ".join(parts)
        return ""

    def _parse_file(self, path):
        # type: (str) -> Optional[Session]
        ns = os.path.relpath(os.path.dirname(path), self.root)
        if ns == ".":
            ns = os.path.basename(self.root)
        conv = os.path.basename(path)[:8]
        first_prompt = None
        intok = outtok = human = 0
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
                role = o.get(self.role_field)
                if role == self.user_role:
                    human += 1
                    if first_prompt is None:
                        txt = " ".join(self._as_text(o.get(self.content_field)).split())
                        if txt:
                            first_prompt = txt[:140]
                elif role == self.assistant_role:
                    u = o.get(self.usage_field) or {}
                    intok += u.get(self.input_field, 0) or 0
                    outtok += u.get(self.output_field, 0) or 0
        return Session(
            id=conv, namespace=ns, first_prompt=first_prompt,
            input_tokens=intok, output_tokens=outtok, human_turns=human,
        )
