from shimbboleth._model.json_schema import JSONSchemaVisitor
import re
from shimbboleth._model.model import Model
from shimbboleth._model.field_types import (
    Description,
    MatchesRegex,
    Examples,
    NonEmpty,
    Ge,
    Le,
    NonEmptyList,
    NonEmptyString,
)
from shimbboleth._model.field import field
from shimbboleth._model.field_alias import FieldAlias
from typing import Annotated, Literal, ClassVar
from typing_extensions import TypeAliasType

import pytest
from pytest import param


def make_model(attrs, **kwargs):
    return type(Model)("MyModel", (Model,), attrs, **kwargs)


def str_to_int(value: str) -> int:
    return int(value)


@pytest.mark.parametrize(
    ("field_type", "expected"),
    [
        pytest.param(bool, {"type": "boolean"}, id="simple"),
        pytest.param(int, {"type": "integer"}, id="simple"),
        pytest.param(str, {"type": "string"}, id="simple"),
        pytest.param(None, {"type": "null"}, id="simple"),
        pytest.param(
            list[bool], {"type": "array", "items": {"type": "boolean"}}, id="list"
        ),
        pytest.param(
            list[str], {"type": "array", "items": {"type": "string"}}, id="list"
        ),
        pytest.param(
            list[int], {"type": "array", "items": {"type": "integer"}}, id="list"
        ),
        pytest.param(
            dict[str, bool],
            {"type": "object", "additionalProperties": {"type": "boolean"}},
            id="dict",
        ),
        pytest.param(
            dict[str, int],
            {"type": "object", "additionalProperties": {"type": "integer"}},
            id="dict",
        ),
        pytest.param(
            dict[str, str],
            {"type": "object", "additionalProperties": {"type": "string"}},
            id="dict",
        ),
        pytest.param(
            dict[Annotated[str, Description("")], str],
            {
                "type": "object",
                "additionalProperties": {"type": "string"},
                "propertyNames": {"description": ""},
            },
            id="dict_with_annotation",
        ),
        pytest.param(
            dict[Annotated[str, MatchesRegex("^.*$")], str],
            {
                "type": "object",
                "additionalProperties": {"type": "string"},
                "propertyNames": {"pattern": "^.*$"},
            },
            id="dict_with_annotation",
        ),
        pytest.param(
            bool | int,
            {"oneOf": [{"type": "boolean"}, {"type": "integer"}]},
            id="union",
        ),
        pytest.param(
            str | None, {"oneOf": [{"type": "string"}, {"type": "null"}]}, id="union"
        ),
        pytest.param(Literal["hello"], {"enum": ["hello"]}, id="literal"),
        pytest.param(
            Literal["hello", "goodbye"], {"enum": ["hello", "goodbye"]}, id="literal"
        ),
        pytest.param(re.Pattern, {"type": "string", "format": "regex"}, id="pattern"),
        pytest.param(
            NonEmptyList[int],
            {"type": "array", "items": {"type": "integer"}, "minLength": 1},
            id="non-empty-list",
        ),
        pytest.param(
            NonEmptyString, {"type": "string", "minLength": 1}, id="non-empty-string"
        ),
    ],
)
def test_schema(field_type, expected):
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
        (Annotated[int, Ge(5)], {"type": "integer", "minimum": 5}),
        (Annotated[int, Le(10)], {"type": "integer", "maximum": 10}),
        (
            Annotated[int, Ge(0), Le(100)],
            {"type": "integer", "minimum": 0, "maximum": 100},
        ),
    ],
)
def test_annotated(field_type, expected):
    """Ensure that `Annotated` types are handled correctly."""
    assert JSONSchemaVisitor().visit(field_type) == expected


def test_type_alias_type():
    visitor = JSONSchemaVisitor()
    assert visitor.visit(TypeAliasType("TAT", int)) == {"$ref": "#/$defs/TAT"}
    assert visitor.model_defs == {"TAT": {"type": "integer"}}


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
