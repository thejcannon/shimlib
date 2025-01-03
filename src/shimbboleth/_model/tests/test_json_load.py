import pytest
from typing import Literal, Annotated, ClassVar
from typing_extensions import TypeAliasType

from shimbboleth._model.model import Model
from shimbboleth._model.field_types import MatchesRegex, NonEmpty
from shimbboleth._model.field import field
from shimbboleth._model.json_load import JSONLoadVisitor
from shimbboleth._model.field_alias import FieldAlias

param = pytest.param


def make_model(attrs, **kwargs):
    return type(Model)("MyModel", (Model,), attrs, **kwargs)


def str_to_int(value: str) -> int:
    return int(value)


@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        param(bool, True, id="simple"),
        param(bool, False, id="simple"),
        param(int, 0, id="simple"),
        param(int, 1, id="simple"),
        param(str, "a string", id="simple"),
        param(str, "", id="simple"),
        param(None, None, id="simple"),
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
        # list
        param(list[int], [], id="list"),
        param(list[int], [1, 2, 3], id="list"),
        param(list[str], ["a", "b", "c"], id="list"),
        param(list[bool], [True, False], id="list"),
        param(list[Annotated[str, NonEmpty]], [""], id="list"),
        param(Annotated[list[str], NonEmpty], [], id="list"),
        # literal
        param(Literal["a", "b", "c"], "a", id="literal"),
        param(Literal["a", "b", "c"], "b", id="literal"),
        param(Literal["a", "b", "c"], "c", id="literal"),
        param(Literal[1, 2, 3], 1, id="literal"),
        param(Literal[1, 2, 3], 2, id="literal"),
        param(Literal[1, 2, 3], 3, id="literal"),
        param(Literal[True, False, "true", "false"], True, id="literal"),
        param(Literal[True, False, "true", "false"], "true", id="literal"),
        # union
        param(int | str, 42, id="union"),
        param(int | str, "hello", id="union"),
        param(bool | str, True, id="union"),
        param(bool | str, "true", id="union"),
        param(list[str] | dict[str, int], ["1", "2", "3"], id="union"),
        param(list[str] | dict[str, int], {"a": 1, "b": 2}, id="union"),
        # misc
        param(Annotated[str, MatchesRegex(r"^.*$")], "", id="annotated"),
        param(TypeAliasType("TAT", int), 0, id="type_alias_type"),
        param(TypeAliasType("TAT", list[str]), [""], id="type_alias_type"),
    ],
)
def test_paassing(field_type, obj):
    assert JSONLoadVisitor().visit(objType=field_type, obj=obj) == obj


@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        param(bool, 0, id="simple"),
        param(bool, None, id="simple"),
        param(int, True, id="simple"),
        param(int, False, id="simple"),
        # dict
        param(dict[str, int], [], id="dict"),
        param(dict[str, int], {0: 0}, id="dict"),
        param(dict[str, int], {0: None}, id="dict"),
        param(dict[str, int], {"key": False}, id="dict"),
        param(dict[str, bool], {"key": 1}, id="dict"),
        param(dict[str, int], {"key1": 0, "key2": "value"}, id="dict"),
        # list
        param(list[int], dict(), id="list"),
        param(list[int], [1, "2", 3], id="list"),
        param(list[str], ["a", 1, "c"], id="list"),
        param(list[int], [True], id="list"),
        param(list[bool], [True, "False"], id="list"),
        param(list[bool], [0], id="list"),
        param(list[int], "not a list", id="list"),
        # literal
        param(Literal["a", "b", "c"], "d", id="literal"),
        param(Literal["a", "b", "c"], 1, id="literal"),
        param(Literal[True], 1, id="literal"),
        param(Literal[1], True, id="literal"),
        param(Literal[False], 0, id="literal"),
        param(Literal[0], False, id="literal"),
        # union
        param(int | str, True, id="union"),
        param(int | str, [], id="union"),
        param(bool | str, 0, id="union"),
        param(bool | int, "string", id="union"),
        param(list[str] | dict[str, int], set(), id="union"),
        param(list[str] | dict[str, int], "string", id="union"),
    ],
)
def test_invalid(field_type, obj):
    with pytest.raises(TypeError):
        JSONLoadVisitor().visit(objType=field_type, obj=obj)


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
    assert model_def.model_load(obj) == model_def(**expected)


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
        model_def.model_load(obj=obj)


def test_model__extras():
    class MyModel(Model, extra=True):
        pass

    instance = MyModel.model_load({"field": "value"})
    assert instance._extra["field"] == "value"


def test_nested_models():
    # @TODO: Test list[Model] or dict[str, Model] or `Model | None`
    pass


def test_field_alias():
    class MyModel(Model):
        field: str
        alias: ClassVar = FieldAlias("field")

    instance = MyModel.model_load({"alias": "value"})
    assert instance.field == "value"


def test_json_alias():
    class MyModel(Model):
        if_condition: str = field(json_alias="if")

    assert MyModel.model_load({"if": "value"}).if_condition == "value"

    with pytest.raises(TypeError):
        MyModel.model_load({"if_condition": "value"})
