from shimbboleth._model.validate import get_validators, ValidationError
from shimbboleth._model.validate import NonEmpty, MatchesRegex, Not, Ge, Le
import uuid
from typing import Annotated


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
        # @TODO: Unions
    ],
)
def test_valid(field_type, obj):
    for validator in get_validators(field_type):
        validator(obj)


# @TODO: Add error message expectation
@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        # int
        param(Annotated[int, Ge(1)], 0, id="int"),
        param(Annotated[int, Le(1)], 2, id="int"),
        # dict
        param(Annotated[dict[str, int], NonEmpty], {}, id="dict"),
        param(
            Annotated[dict[Annotated[str, NonEmpty], int], NonEmpty], {"": 0}, id="dict"
        ),
        param(dict[Annotated[str, MatchesRegex("^a$")], int], {"": 0}, id="dict"),
        # str
        param(Annotated[str, MatchesRegex(r"^a$")], "", id="str"),
        param(Annotated[str, MatchesRegex(r"^$"), NonEmpty], "", id="str"),
        # list
        param(list[Annotated[str, NonEmpty]], [""], id="list"),
        param(list[Annotated[str, MatchesRegex("^a$")]], [""], id="list"),
        param(Annotated[list[str], NonEmpty], [], id="list"),
        # Not
        param(Annotated[int, Not[Ge(10)]], 10, id="not"),
        param(Annotated[int, Not[Ge(10)]], 11, id="not"),
        param(Annotated[int, Not[Ge(10)]], 100, id="not"),
        param(
            Annotated[str, Not[uuid.UUID]],
            "123e4567-e89b-12d3-a456-426614174000",
            id="not",
        ),
        # UUID
        param(Annotated[str, uuid.UUID], "not-a-uuid", id="uuid"),
        # @TODO: Unions
    ],
)
def test_invalid(field_type, obj):
    validators = get_validators(field_type)
    with pytest.raises(ValidationError) as e:
        for validator in validators:
            validator(obj)
