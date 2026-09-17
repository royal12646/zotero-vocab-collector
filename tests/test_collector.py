from vocab_collector.collector import Collector


class FakeZotero:
    def annotations(self):
        return [{"data": {
            "key": "ANN1", "itemType": "annotation", "annotationType": "highlight",
            "annotationColor": "#a28ae5", "annotationText": "susceptible",
            "annotationPageLabel": "3", "annotationPosition": '{"pageIndex": 2}',
            "parentItem": "PDF1",
        }}]

    def item(self, key):
        if key == "PDF1":
            return {"data": {"key": key, "title": "paper.pdf", "parentItem": "PAPER1"}}
        return {"data": {"key": key, "title": "Research Paper"}}

    def attachment_path(self, key):
        return None


def test_collects_only_matching_highlights():
    rows = Collector(FakeZotero(), "#a28ae5").collect()
    assert len(rows) == 1
    assert rows[0].term == "susceptible"
    assert rows[0].paper == "Research Paper"
    assert rows[0].page == "3"
    assert rows[0].annotation_key == "ANN1"


def test_filters_by_selected_paper():
    assert Collector(FakeZotero(), "#a28ae5").collect("OTHER_PAPER") == []
