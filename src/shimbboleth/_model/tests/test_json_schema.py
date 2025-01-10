from shimbboleth._model.json_schema import schema
import re
import uuid
from shimbboleth._model.model import Model
from shimbboleth._model.validation import (
    MatchesRegex,
    Ge,
    Le,
    NonEmptyList,
    NonEmptyString,
    Not,
)
from shimbboleth._model.field import field
from shimbboleth._model.field_alias import FieldAlias
from typing import Annotated, Literal, ClassVar

import pytest
from pytest import param


def make_model(attrs, **kwargs):
    return type(Model)("MyModel", (Model,), attrs, **kwargs)


def str_to_int(value: str) -> int:
    return int(value)


@pytest.mark.parametrize(
    ("field_type", "expected"),
    [
        param(bool, {"type": "boolean"}, id="simple"),
        param(int, {"type": "integer"}, id="simple"),
        param(str, {"type": "string"}, id="simple"),
        param(None, {"type": "null"}, id="simple"),
        param(list[bool], {"type": "array", "items": {"type": "boolean"}}, id="list"),
        param(list[str], {"type": "array", "items": {"type": "string"}}, id="list"),
        param(list[int], {"type": "array", "items": {"type": "integer"}}, id="list"),
        param(
            dict[str, bool],
            {"type": "object", "additionalProperties": {"type": "boolean"}},
            id="dict",
        ),
        param(
            dict[str, int],
            {"type": "object", "additionalProperties": {"type": "integer"}},
            id="dict",
        ),
        param(
            dict[str, str],
            {"type": "object", "additionalProperties": {"type": "string"}},
            id="dict",
        ),
        # Union
        param(
            bool | int,
            {"oneOf": [{"type": "boolean"}, {"type": "integer"}]},
            id="union",
        ),
        param(
            str | None, {"oneOf": [{"type": "string"}, {"type": "null"}]}, id="union"
        ),
        # Literal
        param(Literal["hello"], {"enum": ["hello"]}, id="literal"),
        param(
            Literal["hello", "goodbye"], {"enum": ["hello", "goodbye"]}, id="literal"
        ),
        # Pattern
        param(re.Pattern, {"type": "string", "format": "regex"}, id="pattern"),
        # UUID
        param(
            uuid.UUID,
            {
                "type": "string",
                "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
            },
            id="uuid",
        ),
        # Annotated
        param(
            NonEmptyList[int],
            {"type": "array", "items": {"type": "integer"}, "minLength": 1},
            id="annotated",
        ),
        param(
            dict[Annotated[str, MatchesRegex("^.*$")], str],
            {
                "type": "object",
                "additionalProperties": {"type": "string"},
                "propertyNames": {"pattern": "^.*$"},
            },
            id="annotated",
        ),
        param(
            Annotated[str, MatchesRegex("^.*$")],
            {"type": "string", "pattern": "^.*$"},
            id="annotated",
        ),
        param(Annotated[int, Ge(5)], {"type": "integer", "minimum": 5}, id="annotated"),
        param(
            Annotated[int, Le(10)], {"type": "integer", "maximum": 10}, id="annotated"
        ),
        param(
            Annotated[int, Ge(0), Le(100)],
            {"type": "integer", "minimum": 0, "maximum": 100},
            id="annotated",
        ),
        param(NonEmptyString, {"type": "string", "minLength": 1}, id="annotated"),
        param(
            Annotated[int, Not[Ge(10)]],
            {"type": "integer", "not": {"minimum": 10}},
            id="annotated",
        ),
    ],
)
def test_schema(field_type, expected):
    model_defs = {}
    assert schema(field_type, model_defs=model_defs) == expected


@pytest.mark.parametrize(
    ("model_def", "expected"),
    [
        (
            make_model(
                {
                    "__annotations__": {"field": int},
                },
            ),
            {
                "properties": {"field": {"type": "integer"}},
                "required": ["field"],
            },
        ),
        (
            make_model(
                {
                    "__annotations__": {"field": int},
                    "field": field(json_loader=str_to_int),
                },
            ),
            {
                "properties": {"field": {"type": "string"}},
                "required": ["field"],
            },
        ),
    ],
)
def test_model(model_def, expected):
    assert model_def.model_json_schema == {
        "type": "object",
        "$defs": {},
        "additionalProperties": False,
        **expected,
    }


@pytest.mark.parametrize(
    ("model_def", "expected"),
    [
        (make_model({}), False),
        (make_model({}, extra=False), False),
        (make_model({}, extra=True), True),
    ],
)
def test_model__extra(model_def, expected):
    """Ensure that `additionalProperties` matches `extra` (and is always provided)."""
    assert model_def.model_json_schema["additionalProperties"] == expected


@pytest.mark.parametrize(
    ("model_def", "expected"),
    [
        (
            make_model(
                {"__annotations__": {"field": int}, "field": 0},
            ),
            0,
        ),
        (
            make_model(
                {"__annotations__": {"field": int}, "field": field(default=0)},
            ),
            0,
        ),
        (
            make_model(
                {
                    "__annotations__": {"field": int},
                    "field": field(default_factory=list),
                },
            ),
            [],
        ),
    ],
)
def test_model__default(model_def, expected):
    """Ensure if a default is provided, the field is not required and the default is in the schema."""
    schema = model_def.model_json_schema
    assert "field" not in schema["required"]
    assert schema["properties"]["field"]["default"] == expected, schema


def test_field_alias():
    class MyModel(Model):
        field: str

        alias1: ClassVar = FieldAlias("field")

    assert MyModel.model_json_schema == {
        "type": "object",
        "additionalProperties": False,
        "$defs": {},
        "properties": {
            "field": {"type": "string"},
            "alias1": {"$ref": "#/$defs/MyModel/properties/field"},
        },
        "required": ["field"],
    }


def test_nested_models():
    class NestedModel(Model):
        pass

    class MyModel(Model):
        field: NestedModel

    assert MyModel.model_json_schema == {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "field": {"$ref": "#/$defs/NestedModel"},
        },
        "required": ["field"],
        "$defs": {
            "NestedModel": {
                "type": "object",
                "additionalProperties": False,
                "properties": {},
                "required": [],
            }
        },
    }
