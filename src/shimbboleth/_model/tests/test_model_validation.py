from shimbboleth._model.model import Model
from shimbboleth._model.validation import NonEmptyString, ValidationError

import pytest


class MyModel(Model):
    field: NonEmptyString


def test_validates_on_construction():
    with pytest.raises(ValidationError):
        MyModel(field="")


def test_validates_on_attribute_assignment():
    instance = MyModel(field="a")
    with pytest.raises(ValidationError):
        instance.field = ""


def test_error_message():
    with pytest.raises(ValidationError) as e:
        MyModel(field="")

    assert "Field: field" in str(e.value)
