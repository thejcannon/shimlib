from shimbboleth._model.field_alias import FieldAlias
from shimbboleth._model.model import Model


def test_field_alias():
    class MyModel(Model):
        field: str

        alias = FieldAlias("field")

    MyModel(field="").alias
