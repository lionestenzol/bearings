"""Prove the loop reader parses a fixture correctly AND stays zero-LLM.

The whole value of bearings is that orientation is a parse, not a model call,
so this test pins both the parse result and the absence of any network/LLM import
in loop.py (two independent angles: source-text scan + AST import scan)."""
import ast
import os

from bearings.loop import LoopState, build_loop_state

BANNED = {"requests", "urllib", "httpx", "anthropic", "openai", "socket"}

_TASK_TWO_OPEN = """# Task

## Done When
- [ ] first unproven thing
- [x] this one is proven
- [ ] second unproven thing
"""

_TASK_ONE_OPEN = """# Task

## Done When
- [x] already done
- [ ] one more to prove
"""


def _make_fixture(tmp_path):
    """festival-project root: two active festivals (3 unchecked total) + 1 capsule."""
    active = tmp_path / "festivals" / "active"
    f1 = active / "alpha-fest-AL0001"
    f2 = active / "beta-fest-BE0001"
    f1.mkdir(parents=True)
    f2.mkdir(parents=True)
    (f1 / "01_task.md").write_text(_TASK_TWO_OPEN, encoding="utf-8")   # 2 unchecked
    (f2 / "01_task.md").write_text(_TASK_ONE_OPEN, encoding="utf-8")   # 1 unchecked
    (tmp_path / "MASTERY_CAPSULE_2026-06-28.md").write_text("# capsule\n", encoding="utf-8")
    return tmp_path


def test_open_festival_count(tmp_path):
    root = _make_fixture(tmp_path)
    state = build_loop_state(str(root))
    assert isinstance(state, LoopState)
    assert len(state.open_festivals) == 2
    assert state.open_festivals == ("alpha-fest-AL0001", "beta-fest-BE0001")


def test_unproven_dod_count(tmp_path):
    root = _make_fixture(tmp_path)
    state = build_loop_state(str(root))
    # 2 unchecked in alpha + 1 in beta = 3; the "- [x]" lines must NOT count.
    assert state.unproven_dod == 3


def test_newest_capsule_found(tmp_path):
    root = _make_fixture(tmp_path)
    state = build_loop_state(str(root))
    assert state.newest_capsule == "MASTERY_CAPSULE_2026-06-28.md"
    assert state.newest_capsule_mtime is not None


def test_missing_root_is_empty_not_raising(tmp_path):
    state = build_loop_state(str(tmp_path / "does-not-exist"))
    assert state.open_festivals == ()
    assert state.unproven_dod == 0
    assert state.newest_capsule is None


def _loop_source_path():
    import bearings.loop as loop_mod
    return loop_mod.__file__


def test_zero_llm_guard_source_scan():
    """Angle 1: the raw source text of loop.py names no banned module import."""
    src = open(_loop_source_path(), "r", encoding="utf-8").read()
    for mod in BANNED:
        assert ("import %s" % mod) not in src, "loop.py must not import %s" % mod
        assert ("from %s" % mod) not in src, "loop.py must not import from %s" % mod


def test_zero_llm_guard_ast_scan():
    """Angle 2: an AST walk of loop.py finds no banned module in any import node."""
    src = open(_loop_source_path(), "r", encoding="utf-8").read()
    tree = ast.parse(src)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module.split(".")[0])
    leaked = imported & BANNED
    assert not leaked, "loop.py imports banned network/LLM modules: %s" % sorted(leaked)
