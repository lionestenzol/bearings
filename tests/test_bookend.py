"""The loop bookend: bearings invoked at session start AND after any groundwork/fest
run, zero-config. The reader (loop.py) is tested in test_loop.py; here we pin the
INVOCATION contract — root resolution priority and that --bookend turns loop state on.

Priority: explicit --loop-root  >  $BEARINGS_LOOP_ROOT  >  the repo itself."""
import os

from bearings.cli import build_parser, resolve_loop_roots


def test_explicit_args_win_over_env():
    roots = resolve_loop_roots(["/a", "/b"], "/env/root", "/repo")
    assert roots == ["/a", "/b"]


def test_env_used_when_no_args():
    env = os.pathsep.join(["/x", "/y"])  # cross-platform separator (':' or ';')
    assert resolve_loop_roots(None, env, "/repo") == ["/x", "/y"]


def test_env_blanks_are_dropped():
    env = os.pathsep.join(["/x", "", "  "])
    assert resolve_loop_roots([], env, "/repo") == ["/x"]


def test_repo_fallback_when_no_args_no_env():
    assert resolve_loop_roots(None, None, "/repo") == ["/repo"]
    assert resolve_loop_roots([], "", "/repo") == ["/repo"]


def test_empty_when_nothing_at_all():
    assert resolve_loop_roots(None, None, "") == []


def test_bookend_flag_exists_and_defaults_false():
    args = build_parser().parse_args([])
    assert hasattr(args, "bookend")
    assert args.bookend is False
    assert build_parser().parse_args(["--bookend"]).bookend is True
