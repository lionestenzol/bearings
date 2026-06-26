from bearings.model import BranchState, Commit, Report, Session
from bearings.render import render_json, render_md


def _report():
    return Report(
        repo="/x/demo",
        dates=["2026-06-25"],
        commits=[Commit(hash="abc1234", when="t", author="a",
                        subject="feat(api): add endpoint", ctype="feat", scope="api",
                        files=[("api/server.py", 120, 0, "product"),
                               ("package-lock.json", 5000, 0, "generated")],
                        ins=5120, dele=0)],
        branch=BranchState(branch="feat/x", ahead="10", behind="0", dirty=2),
        sessions=[Session(id="conv1", namespace="demo", first_prompt="where am I",
                          input_tokens=2_000_000, output_tokens=10_000,
                          edits=0, commits=0, kind="oriented")],
        loc={"product": 120, "generated": 5000},
        by_type={"feat": 1},
        source_name="claude-code",
    )


def test_render_md_has_sections():
    md = render_md(_report())
    assert "# BEARINGS — demo — 2026-06-25" in md
    assert "## Commits (1)" in md
    assert "real product code**: 120" in md
    assert "generated / vendored bloat**: 5,000" in md
    assert "## Sessions (1 via claude-code)" in md
    assert "## Orientation tax" in md
    assert "feat(api): add endpoint" in md


def test_render_md_git_only_omits_sessions():
    r = _report()
    r.sessions = []
    md = render_md(r)
    assert "## Sessions" not in md
    assert "## Orientation tax" not in md
    assert "## Commits (1)" in md  # core still renders


def test_render_json_roundtrips():
    import json
    data = json.loads(render_json(_report()))
    assert data["branch"]["branch"] == "feat/x"
    assert data["by_type"]["feat"] == 1
