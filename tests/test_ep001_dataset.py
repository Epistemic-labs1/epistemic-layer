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
