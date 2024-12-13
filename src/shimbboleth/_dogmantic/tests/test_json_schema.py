from shimbboleth._dogmantic.json_schema import generate
from shimbboleth._dogmantic.model import Model
from shimbboleth._dogmantic.field_types import (
    Description,
    MatchesRegex,
    Examples,
    NonEmpty,
)
from typing import Annotated

import pytest


@pytest.mark.parametrize(
    ("field_type", "expected"),
    [
        (bool, {"type": "boolean"}),
        (int, {"type": "integer"}),
        (str, {"type": "string"}),
        (None, {"type": "null"}),
    ],
)
def test_simple(field_type, expected):
    assert generate(field_type) == expected


@pytest.mark.parametrize(
    ("field_type", "expected"),
    [
        (list[bool], {"type": "array", "items": {"type": "boolean"}}),
        (list[str], {"type": "array", "items": {"type": "string"}}),
        (list[int], {"type": "array", "items": {"type": "integer"}}),
    ],
)
def test_list(field_type, expected):
    assert generate(field_type) == expected


@pytest.mark.parametrize(
    ("field_type", "expected"),
    [
        (
            dict[str, bool],
            {"type": "object", "additionalProperties": {"type": "boolean"}},
        ),
        (
            dict[str, int],
            {"type": "object", "additionalProperties": {"type": "integer"}},
        ),
        (
            dict[str, str],
            {"type": "object", "additionalProperties": {"type": "string"}},
        ),
        (
            dict[Annotated[str, Description("")], str],
            {
                "type": "object",
                "additionalProperties": {"type": "string"},
                "propertyNames": {"description": ""},
            },
        ),
        (
            dict[Annotated[str, MatchesRegex("^.*$")], str],
            {
                "type": "object",
                "additionalProperties": {"type": "string"},
                "propertyNames": {"pattern": "^.*$"},
            },
        ),
    ],
)
def test_dict(field_type, expected):
    assert generate(field_type) == expected


@pytest.mark.parametrize(
    ("field_type", "expected"),
    [
        (bool | int, {"oneOf": [{"type": "boolean"}, {"type": "integer"}]}),
    ],
)
def test_union(field_type, expected):
    assert generate(field_type) == expected


@pytest.mark.parametrize(
    ("field_type", "expected"),
    [
        (Annotated[int, Description("")], {"type": "integer", "description": ""}),
        (Annotated[int, Examples(0, 1)], {"type": "integer", "examples": [0, 1]}),
        (Annotated[str, NonEmpty], {"type": "string", "minLength": 1}),
        (Annotated[str, MatchesRegex("^.*$")], {"type": "string", "pattern": "^.*$"}),
        (
            Annotated[
                str, Description(""), Examples("", ""), NonEmpty, MatchesRegex("^.*$")
            ],
            {
                "type": "string",
                "description": "",
                "examples": ["", ""],
                "minLength": 1,
                "pattern": "^.*$",
            },
        ),
    ],
)
def test_annotated(field_type, expected):
    assert generate(field_type) == expected


@pytest.mark.parametrize(
    ("field_type", "expected"),
    [
        (
            type(Model)("MyModel", (Model,), {"__annotations__": {"field": int}}),
            {
                "type": "object",
                "properties": {"field": {"type": "integer"}},
                "required": ["field"],
                "additionalProperties": False,
            },
        ),
        (
            type(Model)(
                "MyModel", (Model,), {"__annotations__": {"field": int}}, extra=False
            ),
            {
                "type": "object",
                "properties": {"field": {"type": "integer"}},
                "required": ["field"],
                "additionalProperties": False,
            },
        ),
        (
            type(Model)(
                "MyModel", (Model,), {"__annotations__": {"field": int}}, extra=True
            ),
            {
                "type": "object",
                "properties": {"field": {"type": "integer"}},
                "required": ["field"],
                "additionalProperties": True,
            },
        ),
    ],
)
def test_model(field_type, expected):
    assert generate(field_type) == expected


@pytest.mark.parametrize(
    ("field_type", "expected"),
    [
        (dict[int, int], ""),
        (dict[Annotated[int, None], int], ""),
    ],
)
def test_bad_type(field_type, expected):
    with pytest.raises(TypeError):
        generate(field_type)
