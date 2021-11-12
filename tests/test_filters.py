from pdh.filters import Filter
from pdh.transformations import Transformation

apple = {
    "intfield": 42,
    "strfield": "apple",
    "afield": "this is apple",
}
kiwi = {
    "intfield": 8,
    "strfield": "kiwi",
    "afield": "this is kiwi",
}
orange = {
    "intfield": 23,
    "strfield": "orange",
    "afield": "this is orange",
}

ilist = [apple, kiwi, orange]
transformations = {"intfield": Transformation.identity("intfield"), "strfield": Transformation.identity("strfield"), "afield": Transformation.identity("afield")}


def test_filter_eq():
    result = Filter.objects(ilist, transformations, [Filter.eq("intfield", 23)])
    assert len(result) == 1
    assert result[0] == orange


def test_filter_lt():
    result = Filter.objects(ilist, transformations, [Filter.lt("intfield", 9)])
    assert len(result) == 1
    assert result[0] == kiwi


def test_filter_le():
    result = Filter.objects(ilist, transformations, [Filter.le("intfield", 8)])
    assert len(result) == 1
    assert result[0] == kiwi


def test_filter_ge():
    result = Filter.objects(ilist, transformations, [Filter.ge("intfield", 23)])
    assert len(result) == 2
    assert result == [apple, orange]


def test_filter_gt():
    result = Filter.objects(ilist, transformations, [Filter.gt("intfield", 40)])
    assert len(result) == 1
    assert result[0] == apple


def test_filter_inList():
    result = Filter.objects(ilist, transformations, [Filter.inList("strfield", ["kiwi", "orange"])])
    assert len(result) == 2
    assert result == [kiwi, orange]


def test_filter_instr():
    result = Filter.objects(ilist, transformations, [Filter.inStr("afield", "kiwi")])
    assert len(result) == 1
    assert result[0] == kiwi


def test_filter_ieq():
    result = Filter.objects(ilist, transformations, [Filter.ieq("strfield", "APPLE")])
    assert len(result) == 1
    assert result[0] == apple


def test_filter_regexp():
    result = Filter.objects(ilist, transformations, [Filter.regexp("afield", "this is .*")])
    assert len(result) == 3
    assert result == ilist


def test_transformation_extract_field():
    trans = {"afield": Transformation.extract_field("afield", check=False)}
    result = Filter.objects(ilist, trans, [Filter.regexp("afield", "this is .*")])
    assert len(result) == 3
    assert result == [
        {"afield": "this is apple"},
        {"afield": "this is kiwi"},
        {"afield": "this is orange"},
    ]
