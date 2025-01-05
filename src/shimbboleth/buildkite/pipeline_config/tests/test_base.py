import pytest
from shimbboleth._model.validation import ValidationError
from shimbboleth.buildkite.pipeline_config import BlockStep


def test_key_not_uuid(all_step_types):
    all_step_types.ctor(key="hello")


@pytest.mark.parametrize(
    "key",
    [
        "123e4567-e89b-12d3-a456-426614174000",
        "123E4567-E89B-12D3-A456-426614174000",
    ],
)
def test_key_as_uuid(key):
    with pytest.raises(ValidationError):
        BlockStep(key=key)


@pytest.mark.parametrize(
    "key",
    [
        "123e4567-e89b-12d3-a456-426614174000",
        "123E4567-E89B-12D3-A456-426614174000",
    ],
)
@pytest.mark.xfail(reason="We don't validate on property setting yet")
def test_key_setting_uuid(key):
    with pytest.raises(ValidationError):
        BlockStep().key = key
