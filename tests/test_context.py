from vocab_collector.context import containing_sentence, page_index


def test_extracts_sentence_containing_term():
    text = "A first sentence. The model is susceptible to noise. A final sentence."
    sentence, status = containing_sentence(text, "susceptible")
    assert sentence == "The model is susceptible to noise."
    assert status == "ok"


def test_marks_repeated_term_for_review():
    sentence, status = containing_sentence("A model works. Another model fails.", "model")
    assert sentence == "A model works."
    assert status == "multiple-matches-first-used"


def test_reads_page_index_from_json():
    assert page_index('{"pageIndex": 4, "rects": []}') == 4

