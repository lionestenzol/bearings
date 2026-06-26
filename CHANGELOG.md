# Changelog

All notable changes to `bearings` are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); versions follow SemVer.

## [0.1.0] — 2026-06-25

Initial release. Deterministic, model-agnostic "where am I" digest.

### Added
- **Git core** (`core.py`, `classify.py`) — commits-by-type, honest LOC split
  (product / docs / config-data / generated-vendored), branch ahead/behind. No LLM.
- **Pluggable session sources** (`sessions/`) — `SessionSource` ABC + registry with
  three adapters: `claude-code` (Claude Code JSONL), `generic-jsonl` (config-driven
  OpenAI-style logs), `none` (git-only). Sessions classified shipped/worked/oriented/talked.
- **Orientation tax** — reports tokens spent on no-output "where am I" sessions.
- **Optional narration** (`narrate.py`) — any OpenAI-compatible `/chat/completions`
  endpoint via stdlib `urllib`; off by default.
- **Durable ledger** (`--ledger`) — writes `~/.bearings/ledger/<repo>/<date>.md`.
- **CLI** — `--repo --date --days --base --source --sessions-root --opt
  --namespace-pattern --generated --json --ledger --narrate`.
- Markdown + JSON renderers. 13 tests. Zero runtime dependencies (Python 3.8+).

### Notes
- Distributed as a standalone package, extracted from the in-harness `/bearings` skill.
