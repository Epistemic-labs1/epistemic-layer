from benchmarks.ep001_dataset import build_ep001_dataset


def test_ep001_has_expected_shape():
    dataset = build_ep001_dataset()
    assert len(dataset) == 25
    assert len({item.id for item in dataset}) == 25
    assert {item.relation for item in dataset} == {
        "original",
        "exact_copy",
        "light_edit",
        "summary",
        "independent",
    }


def test_each_topic_has_one_of_each_relation():
    dataset = build_ep001_dataset()
    for topic in ("t01", "t02", "t03", "t04", "t05"):
        rows = [item for item in dataset if item.id.startswith(topic)]
        assert {item.relation for item in rows} == {
            "original",
            "exact_copy",
            "light_edit",
            "summary",
            "independent",
        }
