from vocab_collector.config import Config


def test_default_highlight_color_is_zotero_blue(monkeypatch):
    monkeypatch.delenv("ZOTERO_HIGHLIGHT_COLOR", raising=False)
    assert Config.from_environment().highlight_color == "#2ea8e5"
