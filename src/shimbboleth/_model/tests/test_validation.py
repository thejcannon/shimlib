import pytest
from typing import Annotated
from typing_extensions import TypeAliasType
from pytest import param

from shimbboleth._model.model import Model
from shimbboleth._model.field_types import MatchesRegex, NonEmpty
from shimbboleth._model.validation import ValidationVisitor, ValidationError


def make_model(attrs, **kwargs):
    return type(Model)("MyModel", (Model,), attrs, **kwargs)


@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        # dict
        param(dict[str, int], {}, id="dict"),
        param(dict[str, int], {"key": 0}, id="dict"),
        param(dict[str, int], {"key1": 0, "key2": 1}, id="dict"),
        param(Annotated[dict[str, int], NonEmpty], {"key": 0}, id="dict"),
        param(Annotated[dict[str, int], NonEmpty], {"": 0}, id="dict"),
        param(Annotated[dict[Annotated[str, NonEmpty], int], NonEmpty], {"key": 0}, id="dict"),
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
    ],
)
def test_valid(field_type, obj):
    ValidationVisitor().visit(objType=field_type, obj=obj)



@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        # dict
        param(Annotated[dict[str, int], NonEmpty], {}, id="dict"),
        param(Annotated[dict[Annotated[str, NonEmpty], int], NonEmpty], {"": 0}, id="dict"),
        param(dict[Annotated[str, MatchesRegex("^a$")], int], {"": 0}, id="dict"),
        # str
        param(Annotated[str, MatchesRegex(r"^a$")], "", id="str"),
        param(Annotated[str, MatchesRegex(r"^$"), NonEmpty], "", id="str"),
        # list
        param(list[Annotated[str, NonEmpty]], [""], id="list"),
        param(list[Annotated[str, MatchesRegex("^a$")]], [""], id="list"),
        param(Annotated[list[str], NonEmpty], [], id="list"),
    ],
)
def test_invalid(field_type, obj):
    with pytest.raises(ValidationError):
        ValidationVisitor().visit(objType=field_type, obj=obj)


@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        (TypeAliasType("TAT", Annotated[list, NonEmpty]), []),
    ],
)
def test_type_alias_types__invalid(field_type, obj):
    with pytest.raises(ValidationError):
        ValidationVisitor().visit(objType=field_type, obj=obj)


def test_nested_models():
    class NestedModel(Model):
        field: list[Annotated[str, NonEmpty]]

    class MyModel(Model):
        field: Annotated[list[NestedModel], NonEmpty]

    MyModel(field=[NestedModel(field=["a"])])
    MyModel(field=[NestedModel(field=[])])

    with pytest.raises(ValidationError):
        MyModel(field=[])
    with pytest.raises(ValidationError):
        NestedModel(field=[""])
