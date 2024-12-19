from shimbboleth._model.json_schema import JSONSchemaVisitor
from shimbboleth._model.model import Model
from shimbboleth._model.field_types import (
    Description,
    MatchesRegex,
    Examples,
    NonEmpty,
)
from shimbboleth._model.field import field
from shimbboleth._model.field_alias import FieldAlias
from typing import Annotated, Literal, ClassVar

import pytest


def make_model(attrs, **kwargs):
    return type(Model)("MyModel", (Model,), attrs, **kwargs)


def str_to_int(value: str) -> int:
    return int(value)


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
    assert JSONSchemaVisitor().visit(field_type) == expected


@pytest.mark.parametrize(
    ("field_type", "expected"),
    [
        (list[bool], {"type": "array", "items": {"type": "boolean"}}),
        (list[str], {"type": "array", "items": {"type": "string"}}),
        (list[int], {"type": "array", "items": {"type": "integer"}}),
    ],
)
def test_list(field_type, expected):
    assert JSONSchemaVisitor().visit(field_type) == expected


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
    assert JSONSchemaVisitor().visit(field_type) == expected


@pytest.mark.parametrize(
    ("field_type", "expected"),
    [
        (bool | int, {"oneOf": [{"type": "boolean"}, {"type": "integer"}]}),
    ],
)
def test_union(field_type, expected):
    assert JSONSchemaVisitor().visit(field_type) == expected


@pytest.mark.parametrize(
    ("field_type", "expected"),
    [
        (Literal["hello"], {"enum": ["hello"]}),
        (Literal["hello", "goodbye"], {"enum": ["hello", "goodbye"]}),
    ],
)
def test_literal(field_type, expected):
    assert JSONSchemaVisitor().visit(field_type) == expected


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
    """Ensure that `Annotated` types are handled correctly."""
    assert JSONSchemaVisitor().visit(field_type) == expected


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
                    "field": field(json_converter=str_to_int),
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
                    "field": field(default=1, json_default=4),
                },
            ),
            4,
        ),
        # NB: Test default being a Falsey value
        (
            make_model(
                {
                    "__annotations__": {"field": int},
                    "field": field(default=1, json_default=0),
                },
            ),
            0,
        ),
        # NB: Test `None` explicitly (to guard against `= None` dwfaults)
        (
            make_model(
                {
                    "__annotations__": {"field": int},
                    "field": field(default=1, json_default=None),
                },
            ),
            None,
        ),
    ],
)
def test_model__default(model_def, expected):
    """Ensure if a default is provided, the field is not required and the default is in the schema."""
    schema = model_def.model_json_schema
    assert "field" not in schema["required"]
    assert schema["properties"]["field"]["default"] == expected, schema


@pytest.mark.parametrize(
    ("field_type", "expected"),
    [
        (dict[int, int], ""),
        (dict[Annotated[int, None], int], ""),
    ],
)
def test_bad_type(field_type, expected):
    with pytest.raises(TypeError):
        JSONSchemaVisitor().visit(field_type)


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
