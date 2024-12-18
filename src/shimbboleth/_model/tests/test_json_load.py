import pytest
from typing import Literal, Annotated

from shimbboleth._model.model import Model
from shimbboleth._model.field_types import MatchesRegex, NonEmpty
from shimbboleth._model.json_load import load
from shimbboleth._model.field import field


def make_model(attrs, **kwargs):
    return type(Model)("MyModel", (Model,), attrs, **kwargs)


def str_to_int(value: str) -> int:
    return int(value)


@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        (bool, True),
        (bool, False),
        (int, 0),
        (int, 1),
        (str, "a string"),
        (str, ""),
        (None, None),
    ],
)
def test_simple__paassing(field_type, obj):
    assert load(objType=field_type, obj=obj) == obj


@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        (bool, 0),
        (bool, None),
        (int, True),
        (int, False),
    ],
)
def test_simple__invalid(field_type, obj):
    with pytest.raises(TypeError):
        load(objType=field_type, obj=obj)


@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        (dict[str, int], {}),
        (dict[str, int], {"key": 0}),
        (dict[str, int], {"key1": 0, "key2": 1}),
        (Annotated[dict[str, int], NonEmpty], {"key": 0}),
        (Annotated[dict[str, int], NonEmpty], {"": 0}),
        (Annotated[dict[Annotated[str, NonEmpty], int], NonEmpty], {"key": 0}),
    ],
)
def test_dict(field_type, obj):
    assert load(objType=field_type, obj=obj) == obj


@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        (dict[str, int], []),
        (dict[str, int], {0: 0}),
        (dict[str, int], {0: None}),
        (dict[str, int], {"key": False}),
        (dict[str, bool], {"key": 1}),
        (dict[str, int], {"key1": 0, "key2": "value"}),
    ],
)
def test_dict__invalid(field_type, obj):
    with pytest.raises(TypeError):
        load(objType=field_type, obj=obj)


@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        (list[int], []),
        (list[int], [1, 2, 3]),
        (list[str], ["a", "b", "c"]),
        (list[bool], [True, False]),
        (list[Annotated[str, NonEmpty]], [""]),
        (Annotated[list[str], NonEmpty], []),
    ],
)
def test_list(field_type, obj):
    assert load(objType=field_type, obj=obj) == obj


@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        (list[int], dict()),
        (list[int], [1, "2", 3]),
        (list[str], ["a", 1, "c"]),
        (list[int], [True]),
        (list[bool], [True, "False"]),
        (list[bool], [0]),
        (list[int], "not a list"),
    ],
)
def test_list__invalid(field_type, obj):
    with pytest.raises(TypeError):
        load(objType=field_type, obj=obj)


@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        (Literal["a", "b", "c"], "a"),
        (Literal["a", "b", "c"], "b"),
        (Literal["a", "b", "c"], "c"),
        (Literal[1, 2, 3], 1),
        (Literal[1, 2, 3], 2),
        (Literal[1, 2, 3], 3),
        (Literal[True, False, "true", "false"], True),
        (Literal[True, False, "true", "false"], "true"),
    ],
)
def test_literal(field_type, obj):
    assert load(objType=field_type, obj=obj) == obj


@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        (Literal["a", "b", "c"], "d"),
        (Literal["a", "b", "c"], 1),
        (Literal[True], 1),
        (Literal[1], True),
        (Literal[False], 0),
        (Literal[0], False),
    ],
)
def test_literal__invalid(field_type, obj):
    with pytest.raises(TypeError):
        load(objType=field_type, obj=obj)


@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        (int | str, 42),
        (int | str, "hello"),
        (bool | str, True),
        (bool | str, "true"),
        (list[str] | dict[str, int], ["1", "2", "3"]),
        (list[str] | dict[str, int], {"a": 1, "b": 2}),
    ],
)
def test_union(field_type, obj):
    assert load(objType=field_type, obj=obj) == obj


@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        (int | str, True),
        (int | str, []),
        (bool | str, 0),
        (bool | int, "string"),
        (list[str] | dict[str, int], set()),
        (list[str] | dict[str, int], "string"),
    ],
)
def test_union__invalid(field_type, obj):
    with pytest.raises(TypeError):
        load(objType=field_type, obj=obj)


@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        (Annotated[str, MatchesRegex(r"^.*$")], ""),
        (Annotated[str, MatchesRegex(r"^.*$")], "a"),
        (Annotated[str, MatchesRegex(r"^a{4}$")], "aaaa"),
        (Annotated[str, MatchesRegex(r"^a{4}$"), NonEmpty], "aaaa"),
    ],
)
def test_annotated(field_type, obj):
    assert load(objType=field_type, obj=obj) == obj


@pytest.mark.parametrize(
    ("model_def", "obj", "expected"),
    [
        (
            make_model(
                {},
                extra=True,
            ),
            {"field": 0},
            {},
        ),
        (
            make_model(
                {
                    "__annotations__": {"field": int},
                    "field": 0,
                },
            ),
            {},
            {"field": 0},
        ),
        (
            make_model(
                {
                    "__annotations__": {"field": int},
                    "field": field(default=0),
                },
            ),
            {},
            {"field": 0},
        ),
        (
            make_model(
                {
                    "__annotations__": {"field": int},
                    "field": field(json_default=0),
                },
            ),
            {},
            {"field": 0},
        ),
        (
            make_model(
                {
                    "__annotations__": {"field": int},
                },
            ),
            {"field": 0},
            {"field": 0},
        ),
        (
            make_model(
                {
                    "__annotations__": {"field": int},
                    "field": field(json_converter=str_to_int),
                },
            ),
            {"field": "42"},
            {"field": 42},
        ),
    ],
)
def test_model(model_def, obj, expected):
    assert load(objType=model_def, obj=obj) == model_def(**expected)


@pytest.mark.parametrize(
    ("model_def", "obj"),
    [
        (
            make_model(
                {},
                extra=False,
            ),
            {"field": 0},
        ),
        (
            make_model(
                {
                    "__annotations__": {"field": int},
                },
            ),
            {},
        ),
        (
            make_model(
                {
                    "__annotations__": {"field": int},
                },
            ),
            {"field": True},
        ),
        (
            make_model(
                {
                    "__annotations__": {"field": int},
                    "field": field(json_converter=str_to_int),
                },
            ),
            {"field": 0},
        ),
    ],
)
def test_model__invalid(model_def, obj):
    with pytest.raises(TypeError):
        load(objType=model_def, obj=obj)


def test_model__extras():
    class MyModel(Model, extra=True):
        pass

    instance = load(objType=MyModel, obj={"field": "value"})
    assert instance._extra["field"] == "value"


def test_nested_models():
    # @TODOL Test list[Model] or dict[str, Model] or `Model | None`
    pass
