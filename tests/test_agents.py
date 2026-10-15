from pathlib import Path

ROOT = Path(__file__).parent.parent
TEXT = (ROOT / "AGENTS.md").read_text(encoding="utf-8")


def test_commands():
    for s in ("make install", "make test", "make vendored-verify", "make validate-real"):
        assert s in TEXT, s


def test_layout_lists_every_module():
    for p in (ROOT / "src" / "watermark_detector").glob("*.py"):
        if p.name != "__init__.py":
            assert f"`{p.name}`" in TEXT, p.name
    assert "providers/" in TEXT
    assert "trust/" in TEXT


def test_only_agents_md():
    assert not (ROOT / "CLAUDE.md").exists()
