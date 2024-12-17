import pytest
from typing import Literal, Annotated

from shimbboleth._model.field_types import MatchesRegex, NonEmpty
from shimbboleth._model.validation import ValidationError, validate



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
    validate(objType=field_type, obj=obj)

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
    with pytest.raises(ValidationError):
        validate(objType=field_type, obj=obj)


@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        (dict[str, int], {}),
        (dict[str, int], {"key": 0}),
        (dict[str, int], {"key1": 0, "key2": 1}),
        (Annotated[dict[str, int], NonEmpty], {"key": 0}),
        (Annotated[dict[str, int], NonEmpty], {"": 0}),
        (Annotated[dict[Annotated[str, NonEmpty], int], NonEmpty], {"key": 0}),
        (dict[Annotated[str, MatchesRegex("^a$")], int], {"a": 0}),
    ],
)
def test_dict(field_type, obj):
    validate(objType=field_type, obj=obj)

@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        (dict[str, int], []),
        (dict[str, int], {0: 0}),
        (dict[str, int], {0: None}),
        (dict[str, int], {"key": False}),
        (dict[str, bool], {"key": 1}),
        (dict[str, int], {"key1": 0, "key2": "value"}),
        (Annotated[dict[str, int], NonEmpty], {}),
        (Annotated[dict[Annotated[str, NonEmpty], int], NonEmpty], {"": 0}),
        (dict[Annotated[str, MatchesRegex("^a$")], int], {"": 0}),
    ],
)
def test_dict__invalid(field_type, obj):
    with pytest.raises(ValidationError):
        validate(objType=field_type, obj=obj)

@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        (list[int], []),
        (list[int], [1, 2, 3]),
        (list[str], ["a", "b", "c"]),
        (list[bool], [True, False]),
        (list[Annotated[str, MatchesRegex("^a$")]], ["a"]),
        (list[Annotated[str, NonEmpty]], ["a", "b", "c"]),
    ],
)
def test_list(field_type, obj):
    validate(objType=field_type, obj=obj)

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
        (list[Annotated[str, NonEmpty]], [""]),
        (list[Annotated[str, MatchesRegex("^a$")]], [""]),
        (Annotated[list[str], NonEmpty], []),
    ],
)
def test_list__invalid(field_type, obj):
    with pytest.raises(ValidationError):
        validate(objType=field_type, obj=obj)



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
    validate(objType=field_type, obj=obj)

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
    with pytest.raises(ValidationError):
        validate(objType=field_type, obj=obj)

@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        (int | str, 42),
        (int | str, "hello"),
        (bool | str, True),
        (bool | str, "true"),
        (list[str] | dict[str, int], ["1", "2", '3']),
        (list[str] | dict[str, int], {"a": 1, "b": 2}),
    ],
)
def test_union(field_type, obj):
    validate(objType=field_type, obj=obj)

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
    with pytest.raises(ValidationError):
        validate(objType=field_type, obj=obj)


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
    validate(objType=field_type, obj=obj)

@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        (Annotated[str, MatchesRegex(r"^a$")], ""),
        (Annotated[str, MatchesRegex(r"^$"), NonEmpty], ""),
    ],
)
def test_annotated__invalid(field_type, obj):
    with pytest.raises(ValidationError):
        validate(objType=field_type, obj=obj)
