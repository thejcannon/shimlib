import pytest
from shimbboleth._model.validation import ValidationError


def test_key_not_uuid(all_step_types):
    all_step_types.ctor(key="hello")


@pytest.mark.parametrize(
    "key",
    [
        "123e4567-e89b-12d3-a456-426614174000",
        "123E4567-E89B-12D3-A456-426614174000",
    ],
)
def test_key_as_uuid(all_step_types, key):
    with pytest.raises(ValidationError):
        all_step_types.ctor(key=key)

    step = all_step_types.ctor()
    with pytest.raises(ValidationError):
        step.key = key
