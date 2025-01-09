from shimbboleth._model._validators import get_validators
from shimbboleth._model.validation import (
    ValidationError,
    NonEmpty,
    MatchesRegex,
    Not,
    Ge,
    Le,
)
import uuid
from typing import Annotated, Union


import pytest
from pytest import param


@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        # int
        param(Annotated[int, Ge(1)], 1, id="int"),
        param(Annotated[int, Ge(1)], 2, id="int"),
        param(Annotated[int, Le(1)], 1, id="int"),
        param(Annotated[int, Le(1)], 0, id="int"),
        # dict
        param(dict[str, int], {}, id="dict"),
        param(dict[str, int], {"key": 0}, id="dict"),
        param(dict[str, int], {"key1": 0, "key2": 1}, id="dict"),
        param(Annotated[dict[str, int], NonEmpty], {"key": 0}, id="dict"),
        param(Annotated[dict[str, int], NonEmpty], {"": 0}, id="dict"),
        param(
            Annotated[dict[Annotated[str, NonEmpty], int], NonEmpty],
            {"key": 0},
            id="dict",
        ),
        param(dict[Annotated[str, MatchesRegex("^a$")], int], {"a": 0}, id="dict"),
        # str
        param(Annotated[str, MatchesRegex(r"^.*$")], "", id="str"),
        param(Annotated[str, MatchesRegex(r"^.*$")], "a", id="str"),
        param(Annotated[str, MatchesRegex(r"^a{4}$")], "aaaa", id="str"),
        param(Annotated[str, MatchesRegex(r"^a{4}$"), NonEmpty], "aaaa", id="str"),
        param(Annotated[str, NonEmpty], "a", id="str"),
        # list
        param(list[str], [], id="list"),
        param(list[str], ["a", "b"], id="list"),
        param(list[Annotated[str, MatchesRegex("^a$")]], ["a"], id="list"),
        param(list[Annotated[str, NonEmpty]], ["a", "b", "c"], id="list"),
        # Not
        param(Annotated[int, Not[Ge(10)]], 5, id="not"),
        param(Annotated[int, Not[Ge(10)]], 9, id="not"),
        param(Annotated[int, Not[uuid.UUID]], "not-a-uuid", id="not"),
        # UUID
        param(
            Annotated[str, uuid.UUID], "123e4567-e89b-12d3-a456-426614174000", id="uuid"
        ),
        param(Union[Annotated[str, NonEmpty], Annotated[int, Ge(1)]], "1", id="union"),
        param(Union[Annotated[str, NonEmpty], Annotated[int, Ge(1)]], 1, id="union"),
        param(list[Annotated[str, NonEmpty]] | int, ["a"], id="union"),
        param(list[Annotated[str, NonEmpty]] | int, 1, id="union"),
    ],
)
def test_valid(field_type, obj):
    for validator in get_validators(field_type):
        validator(obj)


@pytest.mark.parametrize(
    ("field_type", "obj", "expected_error"),
    [
        # int
        param(Annotated[int, Ge(1)], 0, "'0' to be >= 1", id="int"),
        param(Annotated[int, Le(1)], 2, "'2' to be <= 1", id="int"),
        # dict
        param(
            Annotated[dict[str, int], NonEmpty], {}, "'{}' to be non-empty", id="dict"
        ),
        param(
            Annotated[dict[Annotated[str, NonEmpty], int], NonEmpty],
            {"": 0},
            "'' to be non-empty",
            id="dict",
        ),
        param(
            Annotated[dict[Annotated[str, NonEmpty], int], NonEmpty],
            {"": 0},
            "Where: value is a dict key",
            id="dict",
        ),
        param(
            Annotated[dict[str, Annotated[str, NonEmpty]], NonEmpty],
            {"": ""},
            "Where: value is a dict value",
            id="dict",
        ),
        param(
            dict[Annotated[str, MatchesRegex("^a$")], int],
            {"": 0},
            r"'' to match regex '\^a\$'",
            id="dict",
        ),
        # str
        param(
            Annotated[str, MatchesRegex(r"^a$")],
            "",
            r"'' to match regex '\^a\$'",
            id="str",
        ),
        param(
            Annotated[str, MatchesRegex(r"^$"), NonEmpty],
            "",
            "'' to be non-empty",
            id="str",
        ),
        # list
        param(list[Annotated[str, NonEmpty]], [""], "'' to be non-empty", id="list"),
        param(
            list[Annotated[str, NonEmpty]],
            [""],
            "Where: value is a list element",
            id="list",
        ),
        param(
            list[Annotated[str, MatchesRegex("^a$")]],
            [""],
            r"'' to match regex '\^a\$'",
            id="list",
        ),
        param(Annotated[list[str], NonEmpty], [], r"'\[\]' to be non-empty", id="list"),
        # Not
        param(Annotated[int, Not[Ge(10)]], 10, "'10' to not be >= 10", id="not"),
        param(Annotated[int, Not[Ge(10)]], 11, "'11' to not be >= 10", id="not"),
        param(Annotated[int, Not[Ge(10)]], 100, "'100' to not be >= 10", id="not"),
        param(
            Annotated[str, Not[uuid.UUID]],
            "123e4567-e89b-12d3-a456-426614174000",
            "'123e4567-e89b-12d3-a456-426614174000' to not be a valid UUID",
            id="not",
        ),
        # UUID
        param(
            Annotated[str, uuid.UUID],
            "not-a-uuid",
            "'not-a-uuid' to be a valid UUID",
            id="uuid",
        ),
        # Union
        param(
            Union[Annotated[str, NonEmpty], Annotated[int, Ge(1)]],
            "",
            "'' to be non-empty",
            id="union",
        ),
        param(
            Union[Annotated[str, NonEmpty], Annotated[int, Ge(1)]],
            0,
            "'0' to be >= 1",
            id="union",
        ),
        param(
            list[Annotated[str, NonEmpty]] | int, [""], "'' to be non-empty", id="union"
        ),
    ],
)
def test_invalid(field_type, obj, expected_error):
    validators = get_validators(field_type)
    with pytest.raises(ValidationError, match=expected_error):
        for validator in validators:
            validator(obj)


@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        param(Annotated[str | int, NonEmpty], 1, id="annotated-union"),
        param(
            Union[Annotated[list[int], NonEmpty], Annotated[list[str], NonEmpty]],
            1,
            id="overlapping-outer-types-in-union",
        ),
    ],
)
def test_types_we_dont_support(field_type, obj):
    with pytest.raises(TypeError, match="unsupported"):
        tuple(get_validators(field_type))
