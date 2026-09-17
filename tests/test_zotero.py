from vocab_collector.zotero import ZoteroClient


def test_annotations_are_loaded_in_small_pages():
    client = ZoteroClient()
    calls = []

    def fake_json(path, params):
        calls.append((path, params.copy()))
        if params["start"] == 0:
            return [{"key": str(index)} for index in range(50)]
        return [{"key": "last"}]

    client._json = fake_json

    assert len(client.annotations()) == 51
    assert [params["start"] for _, params in calls] == [0, 50]
    assert all(params["limit"] == 50 for _, params in calls)
