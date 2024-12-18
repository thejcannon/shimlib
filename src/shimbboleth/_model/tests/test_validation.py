import pytest
from typing import Annotated

from shimbboleth._model.model import Model
from shimbboleth._model.field_types import MatchesRegex, NonEmpty
from shimbboleth._model.validation import ValidationVisitor, ValidationError


def make_model(attrs, **kwargs):
    return type(Model)("MyModel", (Model,), attrs, **kwargs)


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
    ValidationVisitor().visit(objType=field_type, obj=obj)


@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        (Annotated[str, MatchesRegex(r"^.*$")], ""),
        (Annotated[str, MatchesRegex(r"^.*$")], "a"),
        (Annotated[str, MatchesRegex(r"^a{4}$")], "aaaa"),
        (Annotated[str, MatchesRegex(r"^a{4}$"), NonEmpty], "aaaa"),
        (Annotated[str, NonEmpty], "a"),
    ],
)
def test_str(field_type, obj):
    ValidationVisitor().visit(objType=field_type, obj=obj)


@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        (Annotated[str, MatchesRegex(r"^a$")], ""),
        (Annotated[str, MatchesRegex(r"^$"), NonEmpty], ""),
    ],
)
def test_str__invalid(field_type, obj):
    with pytest.raises(ValidationError):
        ValidationVisitor().visit(objType=field_type, obj=obj)


@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        (Annotated[dict[str, int], NonEmpty], {}),
        (Annotated[dict[Annotated[str, NonEmpty], int], NonEmpty], {"": 0}),
        (dict[Annotated[str, MatchesRegex("^a$")], int], {"": 0}),
    ],
)
def test_dict__invalid(field_type, obj):
    with pytest.raises(ValidationError):
        ValidationVisitor().visit(objType=field_type, obj=obj)


@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        (list[str], []),
        (list[str], ["a", "b"]),
        (list[Annotated[str, MatchesRegex("^a$")]], ["a"]),
        (list[Annotated[str, NonEmpty]], ["a", "b", "c"]),
    ],
)
def test_list(field_type, obj):
    ValidationVisitor().visit(objType=field_type, obj=obj)


@pytest.mark.parametrize(
    ("field_type", "obj"),
    [
        (list[Annotated[str, NonEmpty]], [""]),
        (list[Annotated[str, MatchesRegex("^a$")]], [""]),
        (Annotated[list[str], NonEmpty], []),
    ],
)
def test_list__invalid(field_type, obj):
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
