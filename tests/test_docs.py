import re
from pathlib import Path

DOCS = Path(__file__).parent.parent / "docs"
KEYS = ("tema", "tipo", "proyecto", "creada", "actualizada", "estado", "aliases", "tags")


def _frontmatter(text):
    assert text.startswith("---\n"), "missing frontmatter"
    head = text.split("\n---\n", 1)[0]
    out = {}
    for line in head.splitlines()[1:]:
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip()
    return out


def _md():
    return sorted(DOCS.rglob("*.md"))


def test_frontmatter():
    files = _md()
    assert files
    for p in files:
        fm = _frontmatter(p.read_text(encoding="utf-8"))
        assert all(k in fm for k in KEYS), p
        assert fm["tipo"] in ("índice", "nota"), p


def test_every_dir_has_index():
    dirs = [DOCS] + [d for d in DOCS.rglob("*") if d.is_dir()]
    for d in dirs:
        assert (d / "index.md").exists(), d


def test_names():
    for p in _md():
        assert re.match(r"^[a-z0-9]+([.-][a-z0-9]+)*\.md$", p.name), p
    for d in DOCS.rglob("*"):
        if d.is_dir():
            assert re.match(r"^[0-9]{2}\.[0-9]{2}-[a-z0-9-]+$", d.name), d


def test_index_content():
    assert "Source of truth" in (DOCS / "index.md").read_text(encoding="utf-8")
    for p in DOCS.rglob("index.md"):
        text = p.read_text(encoding="utf-8")
        for sib in p.parent.glob("*.md"):
            if sib.name != "index.md":
                assert f"]({sib.name})" in text, (p, sib)
        for d in p.parent.iterdir():
            if d.is_dir():
                assert f"]({d.name}/index.md)" in text, (p, d)


def test_notes_link_back():
    for p in _md():
        text = p.read_text(encoding="utf-8")
        if p.name != "index.md":
            assert "](index.md)" in text, p
        elif p.parent != DOCS:
            assert "](../index.md)" in text, p


def test_no_wikilinks():
    for p in _md():
        assert "[" + "[" not in p.read_text(encoding="utf-8"), p


def test_relative_links_resolve():
    for p in _md():
        for target in re.findall(r"\]\(([^)\s]+)\)", p.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = target.split("#", 1)[0]
            assert (p.parent / target).resolve().exists(), (p, target)


def test_every_cited_source_is_listed():
    sources_text = (DOCS / "43.01-research" / "sources.md").read_text(encoding="utf-8")
    listed = set(re.findall(r"^- \*\*([EL][0-9]+)\b", sources_text, re.M))
    for p in (DOCS / "43.01-research").glob("*.md"):
        if p.name == "sources.md":
            continue
        for sid in re.findall(r"\b([EL][0-9]{1,2})\b", p.read_text(encoding="utf-8")):
            assert sid in listed, (p, sid)


def test_zai_note():
    z = (DOCS / "43.01-research" / "zai.md").read_text(encoding="utf-8")
    assert "GB 45438" in z and "91110108MA01KP2T5U" in z
    assert "](zai.md)" in (DOCS / "43.01-research" / "index.md").read_text(encoding="utf-8")


def test_a_note_without_frontmatter_is_caught():
    import pytest

    with pytest.raises(AssertionError):
        _frontmatter("# no frontmatter\n")
