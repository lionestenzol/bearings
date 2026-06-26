# bearings

**Deterministic, model-agnostic "where am I" digest for any git repo.**
Orientation should be a *parse*, not an LLM call.

`bearings` answers *"what did I do / where am I / catch me up"* by reading your
git history (and, optionally, your agent's session logs) and printing a digest:
commits grouped by type, an **honest LOC split** (real product code vs
generated/vendored bloat), and — if a session adapter is configured — which
conversations actually shipped vs just burned tokens re-deriving state.

It runs in ~1 second, needs **zero dependencies**, and uses **no LLM at all**.

```
# BEARINGS — my-repo — 2026-06-25

**Branch** `feat/x` · 139 ahead / 0 behind main · 9 dirty files

## Commits (37)
feat 13  ·  fix 7  ·  refactor 2  ·  test 2  ·  docs 8  ·  chore 4

- `a9f1a45` **feat(droplist)** +409/-48 — ship — harden write API, a11y pass
- ...

## LOC inserted — honest split
- **real product code**: 15,243 (11%)
- **docs**: 16,917 (12%)
- **config/data**: 98,088 (73%)
- **generated / vendored bloat**: 3,899 (2%)
- _total inserted: 134,310_
```

## Why "model-agnostic"?

Three layers, decoupled on purpose:

| Layer | What | LLM? |
|-------|------|------|
| **Core** | git history → commits, LOC split, branch state | **never** — pure `git` + stdlib |
| **Sessions** | optional adapters normalize *any* agent's logs into the digest | none — just parsing |
| **Narration** | optional prose summary over **any** OpenAI-compatible endpoint | optional, any provider |

The digest is complete and useful with **no model and no agent CLI**. Nothing
about it is tied to a specific vendor. If you *want* a prose summary, point it at
OpenAI, an Anthropic-compatible gateway, Ollama, vLLM, LM Studio, OpenRouter —
anything that speaks `/chat/completions`.

## Install

```bash
pipx install .          # or: pip install -e .
```

No runtime dependencies. Python 3.8+.

## Usage

```bash
bearings                                  # today, current repo, git-only
bearings --date 2026-06-25                # a specific day
bearings --days 7                         # last week
bearings --repo /path/to/other --base develop
bearings --json                           # machine-readable
bearings --ledger                         # also write the durable daily ledger
```

### With agent sessions

Enrich the digest with "what was happening" by selecting a session adapter:

```bash
# Claude Code transcripts (~/.claude/projects/*/*.jsonl)
bearings --source claude-code

# any OpenAI-style JSONL chat logs, field names configurable
bearings --source generic-jsonl --sessions-root ~/.codex/sessions \
         --opt role_field=role --opt content_field=content
```

Sessions are classified **shipped** (made commits) / **worked** (edited, no
commit) / **oriented** (asked "where am I", produced nothing) / **talked**, and
the digest reports the **orientation tax** — tokens spent re-deriving state that
git already held.

### Optional narration (any model)

```bash
export BEARINGS_LLM_BASE_URL=http://localhost:11434/v1   # Ollama
export BEARINGS_LLM_MODEL=llama3.1
bearings --narrate
```

```bash
export BEARINGS_LLM_BASE_URL=https://api.openai.com/v1
export BEARINGS_LLM_MODEL=gpt-4o-mini
export BEARINGS_LLM_API_KEY=sk-...
bearings --narrate
```

## Durable ledger

`--ledger` writes `~/.bearings/ledger/<repo>/<date>.md` (override with
`BEARINGS_LEDGER_ROOT`). Wire it into a `post-commit` git hook or your agent's
session-end hook so the **next** session reads orientation for free instead of
paying to rebuild it.

```bash
# .git/hooks/post-commit
bearings --source claude-code --ledger >/dev/null 2>&1 &
```

## Teaching it a new agent

A new session source is a ~40-line subclass:

```python
from bearings.sessions.base import SessionSource
from bearings.model import Session

class MyAgentSource(SessionSource):
    name = "my-agent"
    def iter_sessions(self, dates):
        for conv in my_logs(dates):
            yield Session(id=conv.id, namespace=conv.project,
                          first_prompt=conv.first_user_msg,
                          input_tokens=conv.in_tok, output_tokens=conv.out_tok,
                          edits=conv.file_edits, commits=conv.git_commits)
```

Register it in `bearings/sessions/__init__.py` and it's selectable via
`--source my-agent`. The git core never changes.

## Honest-LOC tuning

The classifier splits inserted lines into product / docs / config-data /
generated-vendored. Add repo-specific bloat markers without editing code:

```bash
bearings --generated festivals/ --generated system-index.json
```

## License

MIT.
