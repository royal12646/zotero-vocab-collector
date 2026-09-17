from pathlib import Path

from vocab_collector.enrich import Enricher


def test_rich_translation_includes_multiple_meanings(tmp_path: Path):
    enricher = Enricher("", tmp_path / "cache.json")
    enricher._translation_candidates = lambda text: ["实用的", "adj. 实际的、可行的"]
    result = enricher._rich_translation("practical")
    assert result.startswith("常用义：实用的")
    assert "其他释义：adj. 实际的、可行的" in result
