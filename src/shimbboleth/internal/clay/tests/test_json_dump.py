import pytest
import uuid
import re
from typing import ClassVar
from pytest import param

from shimbboleth.internal.clay.model import Model
from shimbboleth.internal.clay.field import field
from shimbboleth.internal.clay.json_dump import dump
from shimbboleth.internal.clay.field_alias import FieldAlias


def make_model(attrs, **kwargs):
    return type(Model)("MyModel", (Model,), attrs, **kwargs)


def int_to_str(value: int) -> str:
    return str(value)


@pytest.mark.parametrize(
    ("obj"),
    [
        param(True, id="simple"),
        param(False, id="simple"),
        param(0, id="simple"),
        param(1, id="simple"),
        param("a string", id="simple"),
        param("", id="simple"),
        param(None, id="simple"),
        # dict
        param({}, id="dict"),
        param({"key": 0}, id="dict"),
        param({"key1": 0, "key2": 1}, id="dict"),
        param({"key": "value"}, id="dict"),
        # list
        param([], id="list"),
        param([1, 2, 3], id="list"),
        param(["a", "b", "c"], id="list"),
        param([True, False], id="list"),
        param([{"key": "value"}], id="list"),
        param([[1, 2], [3, 4]], id="list"),
    ],
)
def test_simple_dump(obj):
    assert dump(obj) == obj


def test_uuid_dump():
    uuid_str = "123e4567-e89b-12d3-a456-426614174000"
    uuid_obj = uuid.UUID(uuid_str)
    assert dump(uuid_obj) == uuid_str


def test_regex_dump():
    pattern = r"^test.*$"
    regex = re.compile(pattern)
    assert dump(regex) == pattern


@pytest.mark.parametrize(
    ("model_def", "data", "expected"),
    [
        (
            make_model(
                {},
                extra=True,
            ),
            {},
            {},
        ),
        (
            make_model(
                {
                    "__annotations__": {"field": int},
                    "field": 0,
                },
            ),
            {"field": 1},
            {"field": 1},
        ),
        (
            make_model(
                {
                    "__annotations__": {"field": int},
                    "field": field(default=0),
                },
            ),
            {"field": 0},
            {},  # Default values should be omitted
        ),
        (
            make_model(
                {
                    "__annotations__": {"field": int},
                    "field": field(json_dumper=int_to_str),
                },
            ),
            {"field": 42},
            {"field": "42"},
        ),
    ],
)
def test_model_dump(model_def, data, expected):
    instance = model_def(**data)
    assert dump(instance) == expected


def test_model_extras():
    class ModelWithExtras(Model, extra=True):
        field: str = "value"

    instance = ModelWithExtras()
    instance._extra = {"extra_field": "extra_value"}
    dumped = dump(instance)
    assert "extra_field" in dumped
    assert dumped["extra_field"] == "extra_value"


def test_field_alias():
    class MyModel(Model):
        field: str
        alias: ClassVar = FieldAlias("field")

    instance = MyModel(field="value")
    assert dump(instance) == {"field": "value"}


def test_json_alias():
    class MyModel(Model):
        if_condition: str = field(json_alias="if")

    instance = MyModel(if_condition="value")
    assert dump(instance) == {"if": "value"}
