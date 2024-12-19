from shimbboleth._model.field_alias import FieldAlias
from shimbboleth._model.model import Model


def test_field_alias():
    class MyModel(Model):
        field: str

        alias = FieldAlias("field")

    model = MyModel(field="value")
    assert model.field == model.alias == "value"
    model.field = "other value"
    assert model.field == model.alias == "other value"
    model.alias = "alias value"
    assert model.field == model.alias == "alias value"
