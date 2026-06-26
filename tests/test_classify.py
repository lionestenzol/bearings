from bearings.classify import (classify_commit, classify_kind, classify_path,
                                is_orientation_prompt)


def test_classify_path_product():
    assert classify_path("services/api/server.py") == "product"
    assert classify_path("apps/web/src/App.tsx") == "product"


def test_classify_path_generated():
    assert classify_path("node_modules/react/index.js") == "generated"
    assert classify_path("vendor/cytoscape.min.js") == "generated"
    assert classify_path("package-lock.json") == "generated"


def test_classify_path_docs_and_data():
    assert classify_path("README.md") == "docs"
    assert classify_path("config/app.yaml") == "data"
    assert classify_path("page.html") == "data"


def test_classify_path_extra_generated():
    assert classify_path("src/widget.html", extra_generated=("widget.html",)) == "generated"


def test_classify_commit():
    assert classify_commit("feat(droplist): ship API") == ("feat", "droplist")
    assert classify_commit("fix: typo") == ("fix", None)
    assert classify_commit("just a message") == ("other", None)


def test_orientation_detection():
    assert is_orientation_prompt("wtf did I do today")
    assert is_orientation_prompt("gather my bearings")
    assert not is_orientation_prompt("ship the compiler core")


def test_classify_kind():
    assert classify_kind("ship X", 3, 2) == "shipped"      # committed
    assert classify_kind("ship X", 3, 0) == "worked"       # edited, no commit
    assert classify_kind("where am I", 0, 0) == "oriented"  # asked + produced nothing
    assert classify_kind("hello", 0, 0) == "talked"
