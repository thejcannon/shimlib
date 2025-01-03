from shimbboleth._model.field_alias import FieldAlias
from shimbboleth._model.model import Model
from typing import ClassVar


def test_field_alias__property():
    class MyModel(Model):
        field: str

        alias = FieldAlias("field")

    model = MyModel(field="value")
    assert model.field == model.alias == "value"
    model.field = "other value"
    assert model.field == model.alias == "other value"
    model.alias = "alias value"
    assert model.field == model.alias == "alias value"


def test_field_alias__json_mode_prepend():
    class MyModel(Model):
        field: str

        alias: ClassVar = FieldAlias("field", json_mode="prepend")

    model = MyModel.model_load({"field": "field", "alias": "alias"})
    assert model.field == "alias"


def test_field_alias__json_mode_append():
    class MyModel(Model):
        field: str

        alias: ClassVar = FieldAlias("field", json_mode="append")

    model = MyModel.model_load({"field": "field", "alias": "alias"})
    assert model.field == "field"
