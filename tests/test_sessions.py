import json
import os

from bearings.sessions import get_source
from bearings.sessions.claude_code import ClaudeCodeSource
from bearings.sessions.null import NullSource


def test_null_source_yields_nothing():
    assert list(NullSource().iter_sessions({"2026-06-25"})) == []


def test_registry_unknown_raises():
    try:
        get_source("nope")
        assert False, "should raise"
    except KeyError:
        pass


def test_claude_code_adapter(tmp_path):
    proj = tmp_path / "C--demo"
    proj.mkdir()
    f = proj / "abcd1234-session.jsonl"
    lines = [
        {"type": "user", "isMeta": False,
         "message": {"role": "user", "content": "where am I today"}},
        {"type": "assistant",
         "message": {"role": "assistant",
                     "content": [{"type": "tool_use", "name": "Edit", "input": {}}],
                     "usage": {"input_tokens": 100, "output_tokens": 20}}},
        {"type": "assistant",
         "message": {"role": "assistant",
                     "content": [{"type": "tool_use", "name": "Bash",
                                  "input": {"command": "git commit -m x"}}],
                     "usage": {"input_tokens": 50, "cache_read_input_tokens": 10,
                               "output_tokens": 5}}},
    ]
    f.write_text("\n".join(json.dumps(x) for x in lines), encoding="utf-8")

    # set mtime to the target date
    target = "2026-06-25"
    import datetime, time
    epoch = time.mktime(datetime.datetime.strptime(target, "%Y-%m-%d").timetuple()) + 3600
    os.utime(str(f), (epoch, epoch))

    src = ClaudeCodeSource(root=str(tmp_path))
    sessions = list(src.iter_sessions({target}))
    assert len(sessions) == 1
    s = sessions[0]
    assert s.id == "abcd1234"
    assert s.namespace == "C--demo"
    assert s.first_prompt == "where am I today"
    assert s.edits == 1
    assert s.commits == 1
    assert s.input_tokens == 160  # 100 + (50+10)
    assert s.output_tokens == 25
    assert s.human_turns == 1
